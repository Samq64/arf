import requests
import sys
from srcinfo.parse import parse_srcinfo

from config import ARF_CACHE, PKGS_DIR
import aur
import ui
from pacman import localdb_has, syncdb_has

PKGS_DIR.mkdir(parents=True, exist_ok=True)
AUR_PKGS = aur.package_list()


def fetch_dependencies(pkg):
    aur.update_repo(pkg)
    with open(PKGS_DIR / pkg / ".SRCINFO", "r") as f:
        parsed, _ = parse_srcinfo(f.read())

    deps = set()
    deps.update(parsed.get("depends", []))
    deps.update(parsed.get("makedepends", []))

    # TODO: Proper split package support
    for package in parsed.get("packages", {}).values():
        deps.update(package.get("depends", []))
    return deps


def aur_provider(pkg_name):
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

    return ui.select_one(providers, f"Select a package to provide {pkg_name}")


def resolve(targets):
    resolved = set()
    resolving = set()
    pacman_pkgs = set()
    aur_order = []

    def visit(pkg):
        if pkg in resolved:
            return

        if pkg in resolving:
            print(f"WARNING: Dependency cycle detected for {pkg}", file=sys.stderr)
            return

        if syncdb_has(pkg):
            pacman_pkgs.add(pkg)
            resolved.add(pkg)
            return

        resolving.add(pkg)

        for dep in fetch_dependencies(pkg):
            if localdb_has(f"^{dep}$") or dep in resolved:
                continue

            if syncdb_has(dep):
                pacman_pkgs.add(dep)
                continue

            provider = aur_provider(dep)
            if not provider:
                raise RuntimeError(f"Unsatisfied dependency: {dep}")
            visit(provider)

        resolving.remove(pkg)
        resolved.add(pkg)
        aur_order.append(pkg)

    for pkg in targets:
        visit(pkg)

    return {
        "PACMAN": pacman_pkgs,
        "AUR": aur_order
    }
