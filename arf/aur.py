import gzip
import requests
from arf.config import ARF_CACHE, MAX_CACHE_AGE
from io import BytesIO
from pathlib import Path
from time import time
from subprocess import run

def search_rpc(query: str, by: str = "name") -> list[dict]:
    try:
        response = requests.get(
            "https://aur.archlinux.org/rpc/v5/search",
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
    if not file_path.exists() or force or (time() - file_path.stat().st_mtime > MAX_CACHE_AGE):
        ARF_CACHE.mkdir(parents=True, exist_ok=True)
        print("Downloading AUR package list...")
        response = requests.get("https://aur.archlinux.org/packages.gz", timeout=10)
        response.raise_for_status()
        with gzip.open(BytesIO(response.content), "rt") as gz, file_path.open("w") as f:
            for line in gz:
                f.write(line)
    return file_path


def package_list() -> set[str]:
    file_path = download_package_list()
    with open(file_path, "r") as f:
        return {line.strip() for line in f}


def repo_is_fresh(repo: Path, max_age: int = MAX_CACHE_AGE) -> bool:
    f = repo / ".git" / "FETCH_HEAD"
    if not f.exists():
        f = repo / ".git" / "HEAD"
    return time() - f.stat().st_mtime < max_age


def get_repo(pkg_name: str) -> Path:
    pkgs_dir = ARF_CACHE / "pkgbuild"
    pkgs_dir.mkdir(parents=True, exist_ok=True)
    repo = pkgs_dir / pkg_name

    if repo.is_dir():
        if not repo_is_fresh(repo):
            print(f"Pulling {pkg_name}...")
            run(["git", "pull", "-q", "--ff-only"], cwd=repo, check=True)
    else:
        if pkg_name not in package_list():
            raise RuntimeError(f"{pkg_name} is not an AUR package.")

        print(f"Cloning {pkg_name}...")
        run(
            ["git", "clone", "-q", f"https://aur.archlinux.org/{pkg_name}.git"],
            cwd=str(ARF_CACHE / "pkgbuild"),
            check=True,
        )
    return repo
