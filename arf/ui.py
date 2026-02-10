import subprocess
from arf.config import DEFAULT_FZF_CMD, PREVIEW_SCRIPTS


def select(
    items: list[str], header: str, preview: str = "", multi: bool = True, all: bool = False
) -> list[str]:
    if not items:
        return []

    args = DEFAULT_FZF_CMD.copy()
    args += ["--header", header]
    if multi:
        args.append("--multi")
        if all:
            args += ["--bind", "load:select-all"]
    if preview:
        preview_path = PREVIEW_SCRIPTS / preview
        preview_cmd = str(preview_path) if preview_path.exists() else preview
        if "{}" not in preview_cmd:
            preview_cmd += " {}"
        args += ["--preview", preview_cmd]

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
