from os import environ
from importlib.resources import files
from pathlib import Path

ARF_CACHE = Path(environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "arf"
PKGS_DIR = ARF_CACHE / "pkgbuild"
EDITOR = environ.get("EDITOR", "nano")
PACMAN_AUTH = environ.get("PACMAN_AUTH", "sudo")
DEFAULT_FZF_CMD = ["fzf", "--reverse", "--header-first", "--preview-window=75%"]
PREVIEW_SCRIPTS = files("arf").joinpath("previews")
