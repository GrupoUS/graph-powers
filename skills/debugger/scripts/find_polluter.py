#!/usr/bin/env python3
"""find_polluter.py - Debug skill: bisect which test pollutes shared state.

Runs each test file matching `glob_pattern` one-by-one via `bun run test`,
checking before/after whether `marker_path` materializes. Stops and reports
the first test that creates the marker — that's the polluter.

Use when `bun run test` in parallel passes/fails intermittently and you
suspect test isolation failure (leftover .git dir, lockfile, tmp file,
env var, DB row not cleaned up in afterEach).

Adapted from obra/superpowers/skills/systematic-debugging/find-polluter.sh
to Python stdlib (repo policy: shell scripts forbidden).

Examples:
    python find_polluter.py '.git' 'src/**/*.test.ts'
    python find_polluter.py '/tmp/lockfile' 'src/**/*.test.tsx'
    python find_polluter.py '.env.test.local' 'src/**/*.test.ts'
"""
from __future__ import annotations

import argparse
import glob
import os
import re
import subprocess
import sys


def expand_brace_glob(pattern: str) -> list[str]:
    """Expand a single `{a,b,c}` group in pattern into multiple globs.

    glob.glob() doesn't support brace expansion natively. We handle one
    group to support `**/*.test.{ts,tsx}` — the common case for vitest.
    """
    match = re.search(r"\{([^{}]+)\}", pattern)
    if not match:
        return [pattern]
    options = match.group(1).split(",")
    return [pattern[: match.start()] + opt + pattern[match.end() :] for opt in options]


def discover_tests(pattern: str) -> list[str]:
    """Return sorted, deduplicated list of test files matching pattern."""
    paths: set[str] = set()
    for sub_pattern in expand_brace_glob(pattern):
        for path in glob.glob(sub_pattern, recursive=True):
            if os.path.isfile(path):
                paths.add(path)
    return sorted(paths)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Bisect which test pollutes a shared filesystem path. "
            "Runs tests sequentially via `bun run test` and stops at the first "
            "test that materializes marker_path."
        )
    )
    parser.add_argument(
        "marker_path",
        help="File or directory whose appearance indicates pollution (e.g. '.git')",
    )
    parser.add_argument(
        "glob_pattern",
        help="Glob to discover test files (e.g. 'src/**/*.test.ts')",
    )
    opts = parser.parse_args()

    marker = opts.marker_path
    pattern = opts.glob_pattern

    if os.path.exists(marker):
        print(f"ERROR: marker '{marker}' already exists before any test ran.")
        print("Clean the pre-polluted state first, then re-run.")
        sys.exit(2)

    tests = discover_tests(pattern)
    total = len(tests)
    if total == 0:
        print(f"No test files matched pattern: {pattern}")
        sys.exit(0)

    print(f"Bisecting {total} test files for polluter of: {marker}")
    print("-" * 60)

    for idx, test_file in enumerate(tests, start=1):
        print(f"[{idx}/{total}] {test_file}")
        # Run test; ignore exit code (we care about pollution, not pass/fail).
        subprocess.run(
            ["bun", "run", "test", test_file],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if os.path.exists(marker):
            print("-" * 60)
            print(f"POLLUTER FOUND: {test_file}")
            print(f"  → created: {marker}")
            print()
            print("Investigate this test for missing cleanup in afterEach/afterAll,")
            print("leaked fixture, or shared module-level state mutation.")
            sys.exit(1)

    print("-" * 60)
    print(f"No polluter found in {total} tests; marker '{marker}' never appeared.")
    sys.exit(0)


if __name__ == "__main__":
    main()
