from io import BytesIO
from pathlib import Path
from time import time
import gzip
import sys
from subprocess import run

from config import ARF_CACHE, PKGS_DIR, REPO_MAX_CACHE


def _repo_is_fresh(repo):
    f = repo / ".git" / "FETCH_HEAD"
    if not f.exists():
        f = repo / ".git" / "HEAD"
    return time() - f.stat().st_mtime < REPO_MAX_CACHE


def package_list():
    file = Path(ARF_CACHE / "packages.txt")
    if not file.exists():
        r = requests.get("https://aur.archlinux.org/packages.gz")
        with gzip.open(BytesIO(r.content), "rb") as gz:
            with open(file, "wb") as txt:
                txt.write(gz.read())

    with open(file, "r") as f:
        return {line.strip() for line in f}


def update_repo(pkg):
    repo = PKGS_DIR / pkg

    if repo.is_dir():
        if _repo_is_fresh(repo):
            return
        print(f"Pulling {pkg}...", file=sys.stderr)
        run(["git", "pull", "-q", "--ff-only"], cwd=repo, check=True)
    else:
        if pkg not in package_list():
            raise RuntimeError(f"{pkg} is not an AUR package.")

        print(f"Cloning {pkg}...", file=sys.stderr)
        run(
            ["git", "clone", "-q", f"https://aur.archlinux.org/{pkg}.git"],
            cwd=PKGS_DIR,
            check=True,
        )
