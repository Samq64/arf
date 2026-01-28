#!/usr/bin/env python3
import sys
from resolve import resolve
from update import pacman_update, aur_update

if __name__ == "__main__":
    if len(sys.argv) < 2:
        #pacman_update()
        aur_update()
        exit
    pkgs = resolve(sys.argv[1:])
    for label, group in pkgs.items():
        for pkg in group:
            print(f"{label} {pkg}")
