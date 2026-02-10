import shutil
import subprocess
from arf import aur, ui
from arf.alpm import Alpm
from arf.config import ARF_CACHE, PACMAN_AUTH
from arf.resolve import resolve
from pathlib import Path

alpm = Alpm()


def cmd_install(args):
    if args.packages:
        packages = args.packages
    else:
        items = sorted(alpm.all_sync_packages())
        packages = ui.select(
            items,
            "Select packages to install",
            preview="package.sh",
        )
    resolved = resolve(packages)["PACMAN"]
    if resolved:
        subprocess.run([PACMAN_AUTH, "pacman", "-S", "--needed", *resolved])


def cmd_update(args):
    print(f"Update: {args}")


def cmd_remove(args):
    if args.packages:
        packages = args.packages
    else:
        items = sorted(alpm.explicitly_installed())
        packages = ui.select(
            items,
            "Select packages to remove",
            preview="COLUMNS=$FZF_PREVIEW_COLUMNS pacman -Qi",
        )
    if packages:
        subprocess.run([PACMAN_AUTH, "pacman", "-Rns", *packages])


def cmd_clean(args):
    orphans = alpm.orphans()
    if orphans:
        subprocess.run([PACMAN_AUTH, "pacman", "-Rns", *orphans])

    pkgs_dir = Path(ARF_CACHE / "pkgbuild")
    if not pkgs_dir.is_dir():
        return

    foreign = alpm.foreign_packages()
    for subdir in pkgs_dir.iterdir():
        name = subdir.name
        if name not in foreign:
            print(f"Removing PKGBUILD directory for {name}")
            shutil.rmtree(subdir)


def cmd_sync(args):
    shutil.rmtree(f"{ARF_CACHE}/info", ignore_errors=True)
    aur.download_package_list(force=True)
