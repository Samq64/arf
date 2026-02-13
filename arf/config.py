from os import environ
import re
from importlib.resources import files
from pathlib import Path

ARF_CACHE = Path(environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "arf"
PKGS_DIR = ARF_CACHE / "pkgbuild"
EDITOR = environ.get("EDITOR", "nano")
PACMAN_AUTH = environ.get("PACMAN_AUTH", "sudo")
DEFAULT_FZF_CMD = ["fzf", "--reverse", "--header-first", "--preview-window=75%"]
PREVIEW_SCRIPTS = files("arf").joinpath("previews")
EXCLUDE_PACKAGE_PATTERN = re.compile(r".*-debug-.*-any\.pkg\.tar\.zst")


class Colors:
    RESET = "\x1b[0m"
    BOLD = "\x1b[1m"
    DIM = "\x1b[2m"
    UNDERLINE = "\x1b[4m"
    RED = "\x1b[31m"
    GREEN = "\x1b[32m"
    YELLOW = "\x1b[33m"
    BLUE = "\x1b[34m"
    MAGENTA = "\x1b[35m"
    CYAN = "\x1b[36m"
    DEFAULT = "\x1b[39m"
