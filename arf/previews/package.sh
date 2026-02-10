#!/bin/sh
COLUMNS=$FZF_PREVIEW_COLUMNS
pacman -Si --color=always "$1" | sed '/^$/q'

# TODO: AUR
