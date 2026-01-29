from argparse import ArgumentParser
from arf.main import (
    cmd_install,
    cmd_update,
    cmd_remove,
    cmd_clean,
    cmd_sync,
)


def add_aur_group(parser):
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-a", "--aur-only", dest="aur_only", action="store_true")
    group.add_argument("-A", "--no-aur", dest="no_aur", action="store_true")


def parse_args():
    parser = ArgumentParser(prog="arf", description="Arf: an fzf Pacman wrapper and AUR helper")
    subparsers = parser.add_subparsers(dest="command")

    install = subparsers.add_parser(
        "install",
        aliases=["i"],
        help="Install packages (default, interactive if none specified)",
    )
    install.add_argument("packages", nargs="*", help="Packages to install (opens fzf if omitted)")
    add_aur_group(install)
    install.add_argument("--makepkg-flags", help="A string of flags to pass to makepkg")
    install.set_defaults(func=cmd_install)

    update = subparsers.add_parser("update", aliases=["u"], help="Update system and AUR packages")
    add_aur_group(update)
    update.add_argument(
        "-d",
        "--devel",
        action="store_true",
        help="Update all development (-git) packages",
    )
    update.set_defaults(func=cmd_update)

    remove = subparsers.add_parser(
        "remove", aliases=["r"], help="Remove packages (interactive if none specified)"
    )
    remove.add_argument("packages", nargs="*", help="Packages to remove (opens fzf if omitted)")
    remove.set_defaults(func=cmd_remove)

    clean = subparsers.add_parser("clean", aliases=["c"], help="Remove orphans and clean cache")
    clean.set_defaults(func=cmd_clean)

    sync = subparsers.add_parser("sync", aliases=["s"], help="Refresh AUR metadata")
    sync.set_defaults(func=cmd_sync)

    return parser.parse_args()


def main():
    args = parse_args()
    if args.command is None:
        args.func = cmd_install
        args.packages = []

    args.func(args)


if __name__ == "__main__":
    main()
