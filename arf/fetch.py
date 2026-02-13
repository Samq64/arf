import gzip
import requests
import subprocess
from arf.config import ARF_CACHE, PKGS_DIR
from functools import cache
from io import BytesIO
from pathlib import Path

_seen_repos = set()


class RepoFetchError(Exception):
    pass


class RPCError(Exception):
    pass


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
        raise RPCError("Unable to search the AUR.") from e


def download_package_list(force: bool = False) -> Path | None:
    file_path = Path(ARF_CACHE / "packages.txt")
    if not file_path.exists() or force:
        ARF_CACHE.mkdir(parents=True, exist_ok=True)
        print("Downloading AUR package list...")
        try:
            response = requests.get("https://aur.archlinux.org/packages.gz", timeout=10)
            response.raise_for_status()
        except requests.RequestException:
            raise RPCError("Failed to download AUR package list.")

        with gzip.open(BytesIO(response.content), "rt") as gz, file_path.open("w") as f:
            for line in gz:
                f.write(line)

    return file_path


@cache
def package_list() -> set[str]:
    file_path = download_package_list()
    if not file_path or not file_path.exists():
        return set()
    with open(file_path, "r") as f:
        return {line.strip() for line in f}


def get_repo(pkg_name: str) -> Path | None:
    repo = PKGS_DIR / pkg_name

    if pkg_name in _seen_repos:
        return repo

    if repo.is_dir():
        print(f"Pulling {pkg_name}...")
        try:
            subprocess.run(["git", "pull", "-q", "--ff-only"], cwd=repo, check=True)
        except subprocess.CalledProcessError as e:
            raise RepoFetchError(f"Could not pull {pkg_name} from the AUR.") from e
    else:
        PKGS_DIR.mkdir(parents=True, exist_ok=True)
        if pkg_name not in package_list():
            raise RepoFetchError(f"{pkg_name} is not an AUR package.")

        print(f"Cloning {pkg_name}...")
        try:
            subprocess.run(
                ["git", "clone", "-q", f"https://aur.archlinux.org/{pkg_name}.git"],
                cwd=PKGS_DIR,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            raise RepoFetchError(f"Could not clone {pkg_name} from the AUR.") from e

        _seen_repos.add(pkg_name)
    return repo
