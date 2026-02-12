import subprocess
from arf.config import DEFAULT_FZF_CMD, EDITOR, PREVIEW_SCRIPTS, PKGS_DIR, Colors
from os import environ


def select(
    items: list[str],
    header: str,
    footer: str = "",
    preview: str = "",
    bind: str = "",
    multi: bool = True,
    print_selection: bool = True,
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

    selected = proc.stdout.strip().splitlines()
    if print_selection:
        if len(selected) > 0:
            print(f"{Colors.BOLD}Selected:{Colors.RESET}", " ".join(selected))
        else:
            print("Selection cancelled")
    return selected


def select_one(*args, **kwargs) -> str | None:
    kwargs.pop("multi", None)
    result = select(*args, multi=False, **kwargs)
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


def review_prompt(packages):
    preview_cmd = f"{EDITOR} {PKGS_DIR}/{{}}/PKGBUILD"
    selected = select_one(
        packages,
        "Review build scripts",
        print_selection=False,
        preview="diff.sh",
        footer="Ctrl+e: Edit PKGBUILD",
        bind=f"ctrl-e:execute({preview_cmd})+refresh-preview",
    )
    return selected is not None
