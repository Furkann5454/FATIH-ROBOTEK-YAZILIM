#!/usr/bin/env python3
"""Original GPS collector entrypoint, now using the modular GPS module."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from robotek.cli import main

if __name__ == "__main__":
    # Legacy positional format: [connection] [baud].
    args = ["gps", "--execute"]
    if len(sys.argv) > 1:
        args.extend(["--connection", sys.argv[1]])
    if len(sys.argv) > 2:
        args.extend(["--baud", sys.argv[2]])
    raise SystemExit(main(args))
