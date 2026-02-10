#!/bin/sh
pkg=$1
cd "$PKGS_DIR/$pkg"

if pacman -Qqs "^$pkg$" >/dev/null; then
    date=$(pacman -Qi "$pkg" | sed -n 's/^Build Date *: //p')
    commit=$(git log --before "$(date -d "$date" +%s)" -1 --pretty="%h")
else
    commit=$(git hash-object -t tree /dev/null)
fi

git diff --color=always "$commit" -- . ':!.SRCINFO' ':!.gitignore'
