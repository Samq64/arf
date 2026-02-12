import shlex
import shutil
import subprocess
import sys
from arf import ui
from arf.alpm import Alpm
from arf.config import ARF_CACHE, PACMAN_AUTH, PKGS_DIR, Colors
from arf.fetch import download_package_list, get_repo, package_list
from arf.resolve import resolve
from pathlib import Path
from pyalpm import vercmp
from srcinfo.parse import parse_srcinfo

alpm = Alpm()


def run_pacman(args):
    cmd = [PACMAN_AUTH, "pacman", *args]
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        sys.exit(130)
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)


def print_step(msg, pad=False):
    formatted = f"{Colors.BOLD}{Colors.BLUE}:: {Colors.RESET}{Colors.BOLD}{msg}{Colors.RESET}"
    if pad:
        formatted = f"\n{formatted}\n"
    print(formatted)


def install_aur_package(pkg, flags):
    makepkg_cmd = ["makepkg", "--install"]
    if pkg["dependency"]:
        makepkg_cmd.append("--asdeps")
    if flags:
        makepkg_cmd += flags
    subprocess.run(makepkg_cmd, cwd=get_repo(pkg["name"]), check=True)


def install_packages(packages, makepkg_flags="", skip=None):
    skip = skip or []

    print_step("Resolving dependencies...")
    pacman, aur = resolve(packages, ui.provider_prompt, ui.group_prompt)
    pacman_names = [p["name"] for p in pacman]
    pacman_deps = [p["name"] for p in pacman if p.get("dependency")]
    needs_review = sorted(p["name"] for p in aur if p["name"] not in skip)

    if needs_review and not ui.review_prompt(needs_review):
        return

    if pacman:
        print_step("Installing Pacman packages...")
        run_pacman(["-S", "--needed", *pacman_names])
        if pacman_deps:
            run_pacman(["-Dq", "--asdeps", *pacman_deps])
    if aur:
        flags = shlex.split(makepkg_flags) if makepkg_flags else None
        total = len(aur)
        for i, pkg in enumerate(aur, start=1):
            print_step(f"Installing AUR package: {pkg['name']} ({i}/{total})", pad=True)
            install_aur_package(pkg, flags)


def cmd_install(args):
    if args.packages:
        packages = args.packages
    else:
        items = []
        if not args.aur_only:
            items = sorted(alpm.all_sync_packages())
        if not args.no_aur:
            items += sorted(package_list())
        packages = ui.select(
            items,
            "Select packages to install",
            preview="package.sh",
        )
    if packages:
        install_packages(packages, makepkg_flags=args.makepkg_flags)


def cmd_update(args):
    if not args.aur_only:
        run_pacman(["-Syu"])
    if not args.no_aur:
        updates = []
        print("Checking for AUR updates...")
        aur_pkgs = package_list()

        for pkg in alpm.foreign_packages():
            if pkg.endswith("-debug"):
                continue
            if pkg not in aur_pkgs:
                print(Colors.YELLOW + f"Skipping unknown package: {pkg}" + Colors.RESET)
                continue

            path = get_repo(pkg)
            with open(path / ".SRCINFO", "r") as f:
                srcinfo, _ = parse_srcinfo(f.read())

            installed_version = alpm.get_local_package(pkg).version
            new_version = srcinfo["pkgver"] + "-" + srcinfo["pkgrel"]
            if vercmp(installed_version, new_version) < 0 or (args.devel and pkg.endswith("-git")):
                updates.append(pkg)

        if not updates:
            print("All AUR packages are up to date.")
            return

        selected = ui.select(updates, "Select AUR packages to update", preview="diff.sh", all=True)
        if selected:
            install_packages(selected, skip=selected)


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
        run_pacman(["-Rns", *packages])


def cmd_clean(args):
    orphans = alpm.orphans()
    if orphans:
        run_pacman(["-Rns", *orphans])

    if not PKGS_DIR.is_dir():
        return

    foreign = alpm.foreign_packages()
    for subdir in PKGS_DIR.iterdir():
        name = subdir.name
        if name not in foreign:
            print(f"Removing PKGBUILD directory for {name}")
            shutil.rmtree(subdir)


def cmd_sync(args):
    shutil.rmtree(Path(ARF_CACHE) / "info", ignore_errors=True)
    download_package_list(force=True)
