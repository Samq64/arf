import shlex
import shutil
import subprocess
from arf import ui
from arf.alpm import Alpm
from arf.config import ARF_CACHE, PACMAN_AUTH, PKGS_DIR
from arf.fetch import download_package_list, get_repo, package_list
from arf.resolve import resolve
from pathlib import Path
from pyalpm import vercmp
from srcinfo.parse import parse_srcinfo

alpm = Alpm()


def install_aur_package(pkg, flags):
    print(f"Installing {pkg['name']}...")
    makepkg_cmd = ["makepkg", "--install"]
    if pkg["dependency"]:
        makepkg_cmd += ["-D", "--asdeps"]
    if flags:
        makepkg_cmd += flags
    subprocess.run(makepkg_cmd, cwd=get_repo(pkg["name"]), check=True)


def install_packages(packages, makepkg_flags="", skip=None):
    skip = skip or []
    pacman, aur = resolve(packages, ui.provider_prompt, ui.group_prompt)
    pacman_names = [p["name"] for p in pacman]
    pacman_deps = [p["name"] for p in pacman if p.get("dependency")]
    needs_review = sorted(p["name"] for p in aur if p["name"] not in skip)

    if needs_review and not ui.review_prompt(needs_review):
        return

    if pacman:
        subprocess.run([PACMAN_AUTH, "pacman", "-S", "--needed", *pacman_names], check=True)
        if pacman_deps:
            subprocess.run([PACMAN_AUTH, "pacman", "-D", "--asdeps", *pacman_deps], check=True)
    if aur:
        flags = shlex.split(makepkg_flags) if makepkg_flags else None
        for pkg in aur:
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
    install_packages(packages, makepkg_flags=args.makepkg_flags)


def cmd_update(args):
    if not args.aur_only:
        subprocess.run([PACMAN_AUTH, "pacman", "-Syu"], check=True)
    if not args.no_aur:
        updates = []
        print("Checking for AUR updates...")
        aur_pkgs = package_list()

        for pkg in alpm.foreign_packages():
            if pkg.endswith("-debug"):
                continue
            if pkg not in aur_pkgs:
                print("Skipping unknown package: ")
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
        subprocess.run([PACMAN_AUTH, "pacman", "-Rns", *packages], check=True)


def cmd_clean(args):
    orphans = alpm.orphans()
    if orphans:
        subprocess.run([PACMAN_AUTH, "pacman", "-Rns", *orphans], check=True)

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
