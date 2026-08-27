"""Complete, bounded-by-time Git changeset assessment for the Stop verifier."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import _config as gp

STATUS_TIMEOUT_S = 10


@dataclass(frozen=True)
class ChangeSet:
    """The paths Git reports and whether the assessment itself completed."""

    paths: tuple[str, ...]
    assessed: bool
    project_dir: Path | None


def _parse_status(raw: str) -> tuple[str, ...]:
    """Parse porcelain-v1 -z records, including the second record of a rename."""
    records = raw.split("\0")
    paths: list[str] = []
    index = 0
    while index < len(records):
        record = records[index]
        index += 1
        if not record:
            continue
        if len(record) < 3 or record[2] != " ":
            raise ValueError("malformed git status record")
        status = record[:2]
        path = record[3:]
        if path:
            paths.append(path)
        if "R" in status or "C" in status:
            if index >= len(records) or not records[index]:
                raise ValueError("incomplete git rename record")
            paths.append(records[index])
            index += 1
    return tuple(paths)


def collect_change_set(payload: dict[str, Any] | None) -> ChangeSet:
    """Read every Git change for the project resolved from the hook payload.

    ``assessed`` is deliberately separate from ``paths``: an empty list after a failed Git call
    must not be mistaken for a clean tree by the Stop verifier.
    """
    try:
        project = gp.project_dir(payload)
    except Exception:
        return ChangeSet((), False, None)
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
            cwd=str(project),
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=STATUS_TIMEOUT_S,
            check=False,
        )
        if result.returncode != 0:
            return ChangeSet((), False, project)
        return ChangeSet(_parse_status(result.stdout or ""), True, project)
    except Exception:
        return ChangeSet((), False, project)
