import subprocess
from arf.config import DEFAULT_FZF_CMD


def select(items: list[str], header: str, preview: str = "", multi: bool = True) -> list[str]:
    if not items:
        return []

    args = DEFAULT_FZF_CMD.copy()
    args += ["--header", header]
    if multi:
        args.append("--multi")
    if preview:
        if "{}" not in preview:
            preview += " {}"
        args += ["--preview", preview]

    proc = subprocess.run(
        args,
        input="\n".join(items),
        text=True,
        capture_output=True,
    )
    return proc.stdout.strip().splitlines()


def select_one(items: list[str], header: str, preview: str = "") -> str | None:
    result = select(items, header, preview=preview, multi=False)
    return result[0] if result else None
