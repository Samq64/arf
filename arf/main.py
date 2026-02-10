import shutil
import subprocess
from arf import ui
from arf.alpm import Alpm
from arf.config import ARF_CACHE, EDITOR, PACMAN_AUTH, PKGS_DIR
from arf.fetch import download_package_list, get_repo, package_list
from arf.resolve import resolve
from pyalpm import vercmp
from srcinfo.parse import parse_srcinfo

alpm = Alpm()


def install_packages(resolved_packages, makepkg_flags=None, skip=None):
    pacman = resolved_packages["pacman"]
    aur = resolved_packages["aur"]
    pacman_deps = [pkg for pkg in resolved_packages["pacman"] if pkg["dependency"]]
    needs_review = sorted({pkg["name"] for pkg in aur} - set(skip))
    if needs_review:
        preview_cmd = f"{EDITOR} {PKGS_DIR}/{{}}/PKGBUILD"
        if not ui.select_one(
            needs_review,
            "Review build scripts",
            preview="diff.sh",
            footer="Ctrl+e: Edit PKGBUILD",
            bind=f"ctrl-e:execute({preview_cmd})+refresh-preview",
        ):
            return
    if pacman:
        subprocess.run([PACMAN_AUTH, "pacman", "-S", "--needed", *pacman], check=True)
        subprocess.run([PACMAN_AUTH, "pacman", "-D", "--asdeps", *pacman_deps], check=True)
    if aur:
        for pkg in aur:
            print(f"Installing {pkg['name']}...")
            makepkg_cmd = ["makepkg", "--install"]
            if pkg["dependency"]:
                makepkg_cmd += ["-D", "--asdeps"]
            if makepkg_flags:
                makepkg_cmd += makepkg_flags.split(" ")
            subprocess.run(makepkg_cmd, cwd=get_repo(pkg["name"]), check=True)


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
    resolved = resolve(packages, ui.provider_prompt, ui.group_prompt)
    install_packages(resolved, makepkg_flags=args.makepkg_flags)


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
        resolved = resolve(selected, ui.provider_prompt, ui.group_prompt)
        install_packages(resolved, skip=selected)


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
    shutil.rmtree(f"{ARF_CACHE}/info", ignore_errors=True)
    download_package_list(force=True)
