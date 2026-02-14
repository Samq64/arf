import re
from arf import fetch
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


class Resolver:
    def __init__(self, alpm, select_provider, select_group):
        self.alpm = alpm
        self.select_provider = select_provider
        self.select_group = select_group

        self.resolved = set()
        self.resolving = set()
        self.provider_cache = {}
        self.dependency_cache = {}
        self.pacman = []
        self.aur = []

    def strip_version(self, pkg_name: str) -> str:
        return re.split(r"[<>=]", pkg_name, maxsplit=1)[0]

    def fetch_aur_dependencies(self, name: str) -> set[str]:
        repo = fetch.get_repo(name)

        with open(repo / ".SRCINFO", "r") as f:
            parsed, _ = parse_srcinfo(f.read())
            deps = set(parsed.get("depends", []) + parsed.get("makedepends", []))

            for subpkg in parsed.get("packages", {}).values():
                deps.update(subpkg.get("depends", []))
            return deps

    def get_provider(self, pkg_name: str) -> str | None:
        repo_providers = self.alpm.get_providers(pkg_name)
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

        return self.select_provider(pkg_name, providers)

    def handle_group(self, name: str, members: list) -> None:
        selected = self.select_group(name, members)
        for pkg in selected:
            self.visit(pkg)
        self.resolving.remove(name)
        self.resolved.add(name)

    def visit(self, pkg: str, parent=None) -> None:
        pkg = self.strip_version(pkg)
        if (parent and self.alpm.is_installed(pkg)) or pkg in self.resolved:
            return

        if pkg in self.resolving:
            print_warning(f"Dependency cycle detected for {pkg}")
            return

        self.resolving.add(pkg)
        repo_provider = None

        if repo_pkg := self.alpm.get_sync_package(pkg):
            provider = pkg
            repo_provider = repo_pkg
        elif pkg in self.provider_cache:
            provider = self.provider_cache[pkg]
        elif provider := self.get_provider(pkg):
            self.provider_cache[pkg] = provider
        elif group_pkgs := self.alpm.get_group(pkg):
            self.handle_group(pkg, group_pkgs)
            return
        else:
            raise PackageResolutionError(pkg, parent)

        if provider != pkg and repo_provider is None:
            repo_provider = self.alpm.get_sync_package(provider)

        if repo_provider:
            deps = repo_provider.depends
        else:
            deps = self.dependency_cache.setdefault(provider, self.fetch_aur_dependencies(provider))

        for dep in deps:
            self.visit(dep, parent=pkg)

        self.resolving.remove(pkg)
        self.resolved.add(pkg)

        if repo_provider:
            self.pacman.append({"name": provider, "dependency": parent is not None})
        else:
            self.aur.append({"name": provider, "dependency": parent is not None})

    def resolve(self, targets: list[str]) -> ResolvedPackages:
        for pkg in targets:
            self.visit(pkg)
        return ResolvedPackages(pacman=self.pacman, aur=self.aur)
