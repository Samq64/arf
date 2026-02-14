import sys


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


def print_step(message: str, pad: bool = False):
    formatted = f"{Colors.BOLD}{Colors.BLUE}:: {Colors.DEFAULT}{message}{Colors.RESET}"
    if pad:
        formatted = f"\n{formatted}\n"
    print(formatted)


def print_error(message: str):
    print(Colors.RED + "Error: " + Colors.RESET + message, file=sys.stderr)


def print_warning(message: str):
    print(Colors.YELLOW + "Warning: " + Colors.RESET + message, file=sys.stderr)


def print_srcinfo_errors(errors):
    for error in errors:
        line = error.get("line", "?")
        raw = error.get("error", "")
        if isinstance(raw, list):
            msg = "; ".join(raw)
        else:
            msg = raw
        print(f" Line {line}: {msg}")
