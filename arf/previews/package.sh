#!/bin/sh
COLUMNS=$FZF_PREVIEW_COLUMNS

pacman_output=$(pacman -Si --color=always "$1" 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "$pacman_output" | sed '/^$/q';
else
    exec python -m arf.info "$1"
fi
