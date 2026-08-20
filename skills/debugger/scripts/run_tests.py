#!/usr/bin/env python3
"""run_tests.py - Debug skill: monorepo check gate + tests.

Replaces legacy run_tests.sh (repo policy prefers Python for automation).
Runs `bun run check` then `bun run test`, forwarding extra argv to the test runner.
"""
from __future__ import annotations

import subprocess
import sys


def main() -> None:
    subprocess.run(["bun", "run", "check"], check=True)
    subprocess.run(["bun", "run", "test", *sys.argv[1:]], check=True)


if __name__ == "__main__":
    main()
