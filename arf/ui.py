import subprocess
from arf.config import DEFAULT_FZF_CMD, EDITOR, PREVIEW_SCRIPTS, PKGS_DIR
from os import environ


def select(
    items: list[str],
    header: str,
    footer: str = "",
    preview: str = "",
    bind: str = "",
    multi: bool = True,
    all: bool = False,
) -> list[str]:
    if not items:
        return []

    args = DEFAULT_FZF_CMD.copy()
    args += ["--header", header]
    if footer:
        args += ["--footer", footer]
    if bind:
        args += ["--bind", bind]
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
        env=environ | {"PKGS_DIR": PKGS_DIR},
    )
    return proc.stdout.strip().splitlines()


def select_one(
    items: list[str], header: str, preview: str = "", footer: str = "", bind: str = ""
) -> str | None:
    result = select(items, header, preview=preview, multi=False)
    return result[0] if result else None


def group_prompt(name: str, members: list[str]) -> list[str]:
    return select(
        members,
        f"Select from group {name}",
        preview="package.sh",
        all=True,
    )


def provider_prompt(name: str, providers: list[str]) -> str:
    return select_one(providers, f"Select provider for {name}", preview="package.sh")


def review_prompt(packsges):
    preview_cmd = f"{EDITOR} {PKGS_DIR}/{{}}/PKGBUILD"
    selected = select_one(
        packsges,
        "Review build scripts",
        preview="diff.sh",
        footer="Ctrl+e: Edit PKGBUILD",
        bind=f"ctrl-e:execute({preview_cmd})+refresh-preview",
    )
    return selected is not None
