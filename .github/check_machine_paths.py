#!/usr/bin/env python3
"""No path that exists only on the machine that wrote it. Cardinal 2, enforced.

    python3 .github/check_machine_paths.py

What it catches is one class, named precisely: **a home directory**. `/home/<someone>/`,
`/Users/<someone>/` and `C:\\Users\\<someone>\\` are the three spellings, and they are the ones that
actually leak — an agent pastes its own working directory into a command, the line reads fine in
review, and the instruction is dead on every other machine.

What it deliberately does not catch, and why the previous version of this gate had to be fixed:

- `C:\\` written as a hazard — `Remove-Item -Recurse -Force C:\\` in the destructive-floor tests, in
  the hook comment explaining why that floor exists, and in the changelog entry recording it. The
  old pattern matched any drive letter, so the very fixtures proving the plugin defends Windows
  turned the gate red. A gate that fails on evidence of the thing working is a gate someone deletes.
- `C:\\Windows\\System32\\find.exe` — the same absolute path on every Windows install, cited to
  explain why `find` in a command block means a different program there.
- `C:\\tools\\biome.exe` — an example of a *config value* the host project supplies, not a path this
  repository resolves.

It also does not catch `/opt/x` or `D:\\projects\\x`, and never did on the POSIX side either. The
three arms now agree on one rule instead of the Windows one being stricter than the other two;
widening past home directories would need a real case, and the portability gate
(`check_portability.py`) already covers hardcoded paths from the other direction.
"""

from __future__ import annotations

import glob
import re
import sys

# The lookbehind keeps `https://` and any other `<word>:/` out. Anchoring on the `Users` segment is
# what separates a home directory from a drive root.
PATTERN = re.compile(r"(/home/|/Users/|(?<![A-Za-z])[A-Za-z]:[\\/]+Users[\\/])")

SUFFIXES = ("*.md", "*.py", "*.json", "*.mjs", "*.js", "*.yml", "*.yaml")

# This file states the pattern in prose and in code; scanning it would report itself.
EXEMPT_FILES = {".github/check_machine_paths.py"}


def files() -> list[str]:
    found: list[str] = []
    for suffix in SUFFIXES:
        found += glob.glob(f"**/{suffix}", recursive=True)
        found += glob.glob(f".*/{suffix}")
    return sorted({f.replace("\\", "/") for f in found if "node_modules" not in f})


def main() -> int:
    hits: list[str] = []
    for path in files():
        if path in EXEMPT_FILES:
            continue
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                for i, line in enumerate(fh, 1):
                    if PATTERN.search(line):
                        hits.append(f"{path}:{i}: {line.strip()[:120]}")
        except OSError:
            continue
    print("\n".join(hits) or "no home-directory paths")
    if hits:
        print("::error::a home directory reached a tracked file — it does not exist on any other machine")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
