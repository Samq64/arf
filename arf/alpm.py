import pyalpm
from pycman.config import PacmanConfig
from re import escape
from typing import Any


class Alpm:
    def __init__(self, conf="/etc/pacman.conf"):
        self.handle = PacmanConfig(conf).initialize_alpm()
        self.localdb = self.handle.get_localdb()
        self.syncdbs = self.handle.get_syncdbs()

    def in_repos(self, package: str) -> bool:
        pattern = f"^{escape(package)}$"
        return any(db.search(pattern) for db in self.syncdbs)

    def is_installed(self, package: str) -> bool:
        pattern = f"^{escape(package)}$"
        return bool(self.localdb.search(pattern))

    def explicitly_installed(self) -> list[str]:
        return [
            pkg.name for pkg in self.localdb.pkgcache if pkg.reason == pyalpm.PKG_REASON_EXPLICIT
        ]

    def foreign_pkgs(self) -> list[str]:
        repo_pkgs = set()
        for db in self.syncdbs:
            for pkg in db.pkgcache:
                repo_pkgs.add(pkg.name)

        return [pkg.name for pkg in self.localdb.pkgcache if pkg.name not in repo_pkgs]

    def local_pkg_prop(self, package: str, prop: str) -> Any:
        pkg_obj = self.localdb.get_pkg(package)
        if not pkg_obj:
            raise KeyError(package)
        return getattr(pkg_obj, prop)
