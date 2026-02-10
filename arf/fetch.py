import gzip
import requests
from arf.config import ARF_CACHE, PKGS_DIR
from functools import cache
from io import BytesIO
from pathlib import Path
from subprocess import run

_seen_repos = set()


def search_rpc(query: str, by: str = "name", type: str = "search") -> list[dict]:
    try:
        response = requests.get(
            f"https://aur.archlinux.org/rpc/v5/{type}",
            params={"by": by, "arg": query},
            timeout=10,
        )
        response.raise_for_status()
        return response.json().get("results", [])
    except requests.RequestException as e:
        print(f"Failed to fetch RPC results: {e}")
        return []


def download_package_list(force: bool = False) -> Path:
    file_path = Path(ARF_CACHE / "packages.txt")
    if not file_path.exists() or force:
        ARF_CACHE.mkdir(parents=True, exist_ok=True)
        print("Downloading AUR package list...")
        response = requests.get("https://aur.archlinux.org/packages.gz", timeout=10)
        response.raise_for_status()
        with gzip.open(BytesIO(response.content), "rt") as gz, file_path.open("w") as f:
            for line in gz:
                f.write(line)
    return file_path


@cache
def package_list() -> set[str]:
    file_path = download_package_list()
    with open(file_path, "r") as f:
        return {line.strip() for line in f}


def get_repo(pkg_name: str) -> Path:
    repo = PKGS_DIR / pkg_name

    if pkg_name in _seen_repos:
        return repo

    if repo.is_dir():
        print(f"Pulling {pkg_name}...")
        run(["git", "pull", "-q", "--ff-only"], cwd=repo, check=True)
    else:
        PKGS_DIR.mkdir(parents=True, exist_ok=True)
        if pkg_name not in package_list():
            raise RuntimeError(f"{pkg_name} is not an AUR package.")

        print(f"Cloning {pkg_name}...")
        run(
            ["git", "clone", "-q", f"https://aur.archlinux.org/{pkg_name}.git"],
            cwd=PKGS_DIR,
            check=True,
        )
    _seen_repos.add(pkg_name)
    return repo
