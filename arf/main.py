import subprocess
from arf import ui
from arf.alpm import Alpm
from arf.config import PACMAN_AUTH


def cmd_install(args):
    print(f"Install: {args}")


def cmd_update(args):
    print(f"Update: {args}")


def cmd_remove(args):
    if args.packages:
        packages = args.packages
    else:
        alpm = Alpm()
        items = alpm.explicitly_installed()
        packages = ui.select(
            items,
            "Select packages to remove",
            preview="COLUMNS=$FZF_PREVIEW_COLUMNS pacman -Qi",
        )
    if packages:
        subprocess.run([PACMAN_AUTH, "pacman", "-Rns", *packages])


def cmd_clean(args):
    print(f"Clean: {args}")


def cmd_sync(args):
    print(f"Sync: {args}")
