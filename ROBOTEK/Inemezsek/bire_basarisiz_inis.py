#!/usr/bin/env python3
"""Compatibility launcher for the original script, now using the modular architecture."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from robotek.cli import main

if __name__ == "__main__":
    raise SystemExit(main(["run", "--profile", "inis_tekrar_1", *sys.argv[1:]]))
