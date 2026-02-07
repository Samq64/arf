#!/usr/bin/env python3
import re
import requests
import sys
from os import getenv
from pathlib import Path
from pycman.config import PacmanConfig
from subprocess import run
from time import time

DEP_PATTERN = re.compile(r"^\s*(?:check|make)?depends = ([\w\-.]+)")
SCRIPTS_DIR = Path(getenv("ARF_SCRIPTS", "."))
CACHE_DIR = Path(getenv("ARF_CACHE", "~/.cache/arf")).expanduser()
PKGS_DIR = CACHE_DIR / "pkgbuild"
PKGS_DIR.mkdir(parents=True, exist_ok=True)
MAX_AGE = 3600  # 1 hour

alpm_handle = PacmanConfig("/etc/pacman.conf").initialize_alpm()
localdb = alpm_handle.get_localdb()


with open(f"{CACHE_DIR}/packages.txt", "r") as f:
    AUR_PKGS = {line.strip() for line in f}


def syncdb_providers(pkg_name):
    return {
        pkg.name
        for db in alpm_handle.get_syncdbs()
        for pkg in db.search(pkg_name)
        if any(p.split("=")[0] == pkg_name for p in pkg.provides)
    }


def group_prompt(name, members):
    result = run(
        [
            "fzf",
            "--multi",
            "--header",
            f"Select packages from group {name}",
            "--preview",
            f"{SCRIPTS_DIR}/pkg-preview.sh {{}}",
            "--bind",
            "load:select-all",
        ],
        input="\n".join(members),
        text=True,
        capture_output=True,
    )
    return result.stdout.strip().splitlines()


def get_group(name):
    for db in alpm_handle.get_syncdbs():
        if group := db.read_grp(name):
            _, packages = group
            return group_prompt(name, [pkg.name for pkg in packages])
    return None


def syncdb_get(name):
    for db in alpm_handle.get_syncdbs():
        if pkg := db.get_pkg(name):
            return pkg
    return None


def repo_is_fresh(repo):
    f = repo / ".git" / "FETCH_HEAD"
    if not f.exists():
        f = repo / ".git" / "HEAD"
    return time() - f.stat().st_mtime < MAX_AGE


def fetch_dependencies(name):
    if pkg := syncdb_get(name):
        return pkg.depends

    repo = PKGS_DIR / name

    if repo.is_dir():
        if not repo_is_fresh(repo):
            print(f"Pulling {name}...", file=sys.stderr)
            run(["git", "pull", "-q", "--ff-only"], cwd=repo, check=True)
    else:
        if name not in AUR_PKGS:
            raise RuntimeError(f"{name} is not an AUR package.")

        print(f"Cloning {name}...", file=sys.stderr)
        run(
            ["git", "clone", "-q", f"https://aur.archlinux.org/{name}.git"],
            cwd=PKGS_DIR,
            check=True,
        )

    with open(repo / ".SRCINFO", "r") as f:
        return [m.group(1) for line in f if (m := DEP_PATTERN.match(line))]


def get_provider(pkg_name):
    repo_providers = syncdb_providers(pkg_name)
    if repo_providers:
        providers = sorted(repo_providers)
    else:
        if pkg_name in AUR_PKGS:
            return pkg_name
        r = requests.get(
            "https://aur.archlinux.org/rpc/v5/search",
            params={"by": "provides", "arg": pkg_name},
            timeout=10,
        )
        r.raise_for_status()
        providers = [p["Name"] for p in r.json().get("results", [])]
        if not providers:
            return None

    if len(providers) == 1:
        return providers[0]

    result = run(
        [
            "fzf",
            "--header",
            f"Select provider for {pkg_name}",
            "--preview",
            f"{SCRIPTS_DIR}/pkg-preview.sh {{}}",
        ],
        input="\n".join(providers),
        text=True,
        capture_output=True,
    )
    return result.stdout.strip() or None


def resolve(targets):
    resolved = set()
    resolving = set()
    pacman_pkgs = set()
    aur_order = []

    def visit(pkg):
        pkg = re.split(r"[<>=]", pkg, maxsplit=1)[0]
        if pkg in resolved:
            return

        if localdb.search(f"^{pkg}$"):
            resolved.add(pkg)
            return

        if pkg in resolving:
            print(f"WARNING: Dependency cycle detected for {pkg}", file=sys.stderr)
            return

        resolving.add(pkg)

        if group_pkgs := get_group(pkg):
            for member in group_pkgs:
                visit(member)
            resolving.remove(pkg)
            resolved.add(pkg)
            return

        if syncdb_get(pkg):
            provider = pkg
        else:
            provider = get_provider(pkg)
            if not provider:
                raise RuntimeError(f"ERROR: Could not satisfy {pkg}")

        for dep in fetch_dependencies(provider):
            if not localdb.search(f"^{dep}$"):
                visit(dep)

        resolving.remove(pkg)
        resolved.add(pkg)
        if pkg in AUR_PKGS:
            aur_order.append(provider)
        else:
            pacman_pkgs.add(provider)

    for pkg in targets:
        visit(pkg)

    return {"PACMAN": pacman_pkgs, "AUR": aur_order}


def main():
    pkgs = resolve(sys.argv[1:])
    for label, group in pkgs.items():
        for pkg in group:
            print(f"{label} {pkg}")


if __name__ == "__main__":
    main()
