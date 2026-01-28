import subprocess
import os
from pyalpm import vercmp

import aur
from ui import select
from config import PACMAN_AUTH, PKGS_DIR
from pacman import foreign_pkgs, local_pkg_prop
from srcinfo.parse import parse_srcinfo


def pacman_update():
    subprocess.run([PACMAN_AUTH, "pacman", "-Syu"])


def aur_update():
    updates = set()
    print("Checking for AUR updates...")
    aur_pkgs = aur.package_list()

    for pkg in foreign_pkgs():
        if pkg.endswith("-debug"):
            continue
        if pkg not in aur_pkgs:
            print("Skipping unknown package: ")
            continue

        aur.update_repo(pkg)
        with open(PKGS_DIR / pkg / ".SRCINFO", "r") as f:
            srcinfo, _ = parse_srcinfo(f.read())
        
        installed_version = local_pkg_prop(pkg, "version")
        new_version = srcinfo["pkgver"] + "-" + srcinfo["pkgrel"]
        if vercmp(installed_version, new_version) < 0:
            updates.add(pkg)

    if not updates:
        print("All AUR packages are up to date.")
        return

    selected = select(updates, "Select AUR packages to update")
