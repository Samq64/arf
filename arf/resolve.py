import re
from arf import fetch
from arf.alpm import Alpm
from arf.format import print_warning
from srcinfo.parse import parse_srcinfo
from typing import NamedTuple


class PackageResolutionError(Exception):
    def __init__(self, pkg, parent=None):
        self.pkg = pkg
        self.parent = parent
        if parent:
            message = f"Failed to satisfy {pkg} required by {parent}"
        else:
            message = f"Package not found: {pkg}"
        super().__init__(message)


class ResolvedPackages(NamedTuple):
    pacman: list[dict]
    aur: list[dict]


alpm = Alpm()


def strip_version(pkg_name: str) -> str:
    return re.split(r"[<>=]", pkg_name, maxsplit=1)[0]


def fetch_aur_dependencies(name: str) -> set[str]:
    repo = fetch.get_repo(name)

    with open(repo / ".SRCINFO", "r") as f:
        parsed, _ = parse_srcinfo(f.read())
        deps = set(parsed.get("depends", []) + parsed.get("makedepends", []))

        for subpkg in parsed.get("packages", {}).values():
            deps.update(subpkg.get("depends", []))
        return deps


def get_provider(pkg_name: str, select_provider: callable) -> str | None:
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


def resolve(
    targets: list[str], select_provider: callable, select_group: callable
) -> ResolvedPackages:
    resolved = set()
    resolving = set()
    provider_cache = {}
    deps_cache = {}
    pacman_pkgs = []
    aur_order = []

    def visit(pkg, parent=None):
        pkg = strip_version(pkg)
        if parent and alpm.is_installed(pkg) or pkg in resolved:
            return

        if pkg in resolving:
            print_warning(f"Dependency cycle detected for {pkg}")
            return

        resolving.add(pkg)
        repo_provider = None

        if repo_pkg := alpm.get_sync_package(pkg):
            provider = pkg
            repo_provider = repo_pkg
        elif pkg in provider_cache:
            provider = provider_cache[pkg]
        elif provider := get_provider(pkg, select_provider):
            provider_cache[pkg] = provider
        elif group_pkgs := alpm.get_group(pkg):
            selected = select_group(pkg, group_pkgs)
            for member in selected:
                visit(member)
            resolving.remove(pkg)
            resolved.add(pkg)
            return
        else:
            raise PackageResolutionError(pkg, parent)

        if provider != pkg and repo_provider is None:
            repo_provider = alpm.get_sync_package(provider)

        if repo_provider:
            deps = repo_provider.depends
        else:
            deps = deps_cache.setdefault(provider, fetch_aur_dependencies(provider))

        for dep in deps:
            visit(dep, parent=pkg)

        resolving.remove(pkg)
        resolved.add(pkg)

        if repo_provider:
            pacman_pkgs.append({"name": provider, "dependency": parent is not None})
        else:
            aur_order.append({"name": provider, "dependency": parent is not None})

    for pkg in targets:
        visit(pkg)

    return ResolvedPackages(pacman=pacman_pkgs, aur=aur_order)
