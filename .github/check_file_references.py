#!/usr/bin/env python3
"""Reject live Markdown references to files that do not exist.

Changelogs, skill learning ledgers, dated audit reports and plans are historical records: a removed
path can be the fact they are preserving. Local runtime logs are outside the repository contract.
Everything else describes the current harness and must resolve either from the repository root or
from the citing file's nearest three directories.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

REFERENCE_RE = re.compile(
    r"(?<![\w${./-])"
    r"(?:references?|scripts|hooks|schema|templates|agents|commands|skills|codex|cursor|grok|hermes|workflows)"
    r"/[A-Za-z0-9._/-]+\.(?:md|py|json|mjs|js|txt)"
)
IGNORED_PARTS = frozenset({".git", "node_modules", ".venv", "venv", "__pycache__"})


def is_historical(relative: PurePosixPath) -> bool:
    """True when a Markdown file records past state rather than declaring the current tree."""
    return (
        relative.name == "CHANGELOG.md"
        or (len(relative.parts) == 3
            and relative.parts[0] == "skills"
            and relative.name == "learning.md")
        or relative.parts[:2] == ("docs", "plans")
        or (
            len(relative.parts) == 2
            and relative.parts[0] == "docs"
            and re.fullmatch(r"AUDIT-REPORT-[0-9-]+\.md", relative.name) is not None
        )
    )


def is_runtime_record(relative: PurePosixPath) -> bool:
    """Runtime logs describe local sessions and are not part of the repository contract."""
    return relative.parts[:2] == (".graph-powers", "logs")


def tracked_files(root: Path) -> set[PurePosixPath] | None:
    """Tracked paths, empty outside Git, or None when tracking status cannot be proved."""
    if not (root / ".git").exists():
        return set()
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z", "--cached"],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=20,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return {PurePosixPath(path) for path in result.stdout.split("\0") if path}


def candidates(root: Path, source: Path, reference: str) -> tuple[Path, ...]:
    """The established root-, owner-, parent- and grandparent-relative resolution order."""
    portable = Path(*PurePosixPath(reference).parts)
    owner = source.parent
    return (root / portable, owner / portable, owner.parent / portable, owner.parent.parent / portable)


def scan(root: Path) -> dict[str, list[str]]:
    """Return unresolved references mapped to their repository-relative citing files."""
    root = root.resolve()
    tracked = tracked_files(root)
    missing: dict[str, set[str]] = {}
    for source in root.rglob("*.md"):
        relative = PurePosixPath(source.relative_to(root).as_posix())
        if (any(part in IGNORED_PARTS for part in relative.parts)
                or is_historical(relative)
                or (is_runtime_record(relative)
                    and tracked is not None
                    and relative not in tracked)):
            continue
        text = source.read_text(encoding="utf-8", errors="replace")
        for reference in set(REFERENCE_RE.findall(text)):
            if any(path.exists() for path in candidates(root, source, reference)):
                continue
            missing.setdefault(reference, set()).add(relative.as_posix())
    return {reference: sorted(sources) for reference, sources in sorted(missing.items())}


def main() -> int:
    missing = scan(Path.cwd())
    for reference, sources in missing.items():
        print(f"DANGLING: {reference}  <- {', '.join(sources[:3])}")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
