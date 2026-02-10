import json
import os
import sys
import textwrap
import time
from arf.config import ARF_CACHE
from arf.fetch import search_rpc
from datetime import datetime, timedelta


RED = "\033[31m"
BOLD = "\033[1m"
RESET = "\033[0m"
CACHE_TTL = timedelta(days=1)
COLUMNS = int(os.environ.get("FZF_PREVIEW_COLUMNS", "80"))

INFO_DIR = ARF_CACHE / "info"

FIELDS = [
    ("PackageBase", "Package Base"),
    ("Version", "Version"),
    ("Description", "Description"),
    ("URL", "Upstream URL"),
    ("License", "Licenses"),
    ("Provides", "Provides"),
    ("Conflicts", "Conflicts With"),
    ("Depends", "Depends On"),
    ("OptDepends", "Optional Deps"),
    ("MakeDepends", "Make Deps"),
    ("Submitter", "Submitter"),
    ("Maintainer", "Maintainer"),
    ("NumVotes", "Votes"),
    ("Popularity", "Popularity"),
    ("FirstSubmitted", "First Submitted"),
    ("LastModified", "Last Modified"),
]

FIELD_KEYS = {k for k, _ in FIELDS}


def cache_is_fresh(path):
    return (
        path.is_file() and datetime.now() - datetime.fromtimestamp(path.stat().st_mtime) < CACHE_TTL
    )


def wrap_print(label, value):
    indent = 18
    label_width = indent - 3
    print(f"{BOLD}{label:<{label_width}}{RESET} : ", end="")
    print(textwrap.fill(value, width=COLUMNS - indent, subsequent_indent=" " * indent))


def normalize(value):
    if isinstance(value, list):
        return "  ".join(map(str, value))
    return value


def format_timestamp(ts):
    return time.strftime("%c", time.localtime(ts)) if ts else None


def write_json(pkg, file):
    data = search_rpc(pkg, type="info")[0]
    data = {k: normalize(v) for k, v in data.items()}

    for key in ("FirstSubmitted", "LastModified"):
        data[key] = format_timestamp(data.get(key))

    if data.get("OutOfDate"):
        date = time.strftime("%Y-%m-%d", time.localtime(int(data["OutOfDate"])))
        data["Version"] += f" {RED}Out-of-date ({date}){RESET}"

    if not data.get("Maintainer"):
        data["Maintainer"] = f"{RED}Orphan{RESET}"

    filtered = {k: data[k] for k in FIELD_KEYS if data.get(k) is not None}
    INFO_DIR.mkdir(parents=True, exist_ok=True)
    file.write_text(json.dumps(filtered))


def main(pkg):
    cache_file = INFO_DIR / f"{pkg}.json"
    if not cache_is_fresh(cache_file):
        write_json(pkg, cache_file)

    wrap_print("Repository", "AUR")
    data = json.loads(cache_file.read_text())
    for key, label in FIELDS:
        wrap_print(label, str(data.get(key, "None")))


if __name__ == "__main__":
    main(sys.argv[1])
