#!/usr/bin/env python3
import sys
from resolve import resolve

if __name__ == "__main__":
    pkgs = resolve(sys.argv[1:])
    for label, group in pkgs.items():
        for pkg in group:
            print(f"{label} {pkg}")
