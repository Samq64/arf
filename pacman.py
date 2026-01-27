from pycman.config import PacmanConfig

alpm_handle = PacmanConfig('/etc/pacman.conf').initialize_alpm()
localdb = alpm_handle.get_localdb()
syncdbs = alpm_handle.get_syncdbs()


def syncdb_has(pkg):
    return any(db.search(f"^{pkg}$") for db in syncdbs)


def localdb_has(pkg):
    return bool(localdb.search(f"^{pkg}$"))


def foreign_pkgs():
    repo_pkgs = set()
    for db in syncdbs:
        for pkg in db.pkgcache:
            repo_pkgs.add(pkg.name)

    return [
        pkg.name
        for pkg in localdb.pkgcache
        if pkg.name not in repo_pkgs
    ]
