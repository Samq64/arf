import gzip
import requests
from arf.config import ARF_CACHE
from io import BytesIO
from pathlib import Path


def download_package_list(force: bool = False):
    file_path = Path(ARF_CACHE / "packages.txt")
    if force or not file_path.exists():
        ARF_CACHE.mkdir(parents=True, exist_ok=True)
        print("Downloading AUR package list...")
        response = requests.get("https://aur.archlinux.org/packages.gz")
        response.raise_for_status()
        with gzip.open(BytesIO(response.content), "rt") as gz, file_path.open("w") as f:
            f.write(gz.read())
    return file_path


def package_list() -> list[str]:
    file_path = download_package_list()
    with open(file_path, "r") as f:
        return {line.strip() for line in f}
