import re
import sys
from arf import fetch, ui
from arf.alpm import Alpm
from srcinfo.parse import parse_srcinfo

alpm = Alpm()


def strip_version(pkg_name: str) -> str:
    return re.split(r"[<>=]", pkg_name, maxsplit=1)[0]


def fetch_dependencies(name):
    if pkg := alpm.get_sync_package(name):
        return pkg.depends

    repo = fetch.get_repo(name)
    with open(repo / ".SRCINFO", "r") as f:
        parsed, _ = parse_srcinfo(f.read())
        deps = set(parsed.get("depends", []) + parsed.get("makedepends", []))

        for subpkg in parsed.get("packages", {}).values():
            deps.update(subpkg.get("depends", []))
        return deps


def get_provider(pkg_name, select_provider):
    repo_providers = alpm.get_providers(pkg_name)
    if repo_providers:
        providers = sorted(repo_providers)
    else:
        if pkg_name in fetch.package_list():
            return pkg_name
        response = fetch.search_rpc(pkg_name, by="provides")
        providers = sorted({p["Name"] for p in response})
        if not providers:
            return None

    if len(providers) == 1:
        return providers[0]

    return select_provider(pkg_name, providers)

def resolve(targets, select_provider, select_group):
    resolved = set()
    resolving = set()
    pacman_pkgs = set()
    provider_cache = {}
    deps_cache = {}
    aur_order = []

    def visit(pkg):
        pkg = strip_version(pkg)
        if pkg in resolved:
            return

        if alpm.is_installed(pkg):
            resolved.add(pkg)
            return

        if pkg in resolving:
            print(f"WARNING: Dependency cycle detected for {pkg}", file=sys.stderr)
            return

        resolving.add(pkg)

        if group_pkgs := alpm.get_group(pkg):
            selected = select_group(pkg, group_pkgs)
            for member in selected:
                visit(member)
            resolving.remove(pkg)
            resolved.add(pkg)
            return

        if alpm.get_sync_package(pkg):
            provider = pkg
        else:
            if pkg in provider_cache:
                provider = provider_cache[pkg]
            else:
                provider = get_provider(pkg, select_provider)
                if not provider:
                    raise RuntimeError(f"ERROR: Could not satisfy {pkg}")
                provider_cache[pkg] = provider

        for dep in deps_cache.setdefault(provider, fetch_dependencies(provider)):
            visit(dep)

        resolving.remove(pkg)
        resolved.add(pkg)
        if pkg in fetch.package_list():
            aur_order.append(provider)
        else:
            pacman_pkgs.add(provider)

    for pkg in targets:
        visit(pkg)

    return {"PACMAN": pacman_pkgs, "AUR": aur_order}
