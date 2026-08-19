#!/usr/bin/env python3
"""protect_files.py - Block modifications to sensitive files.
Trigger: PreToolUse (Edit|Write)

Generic defaults block .env, lockfiles, and .git/ directory.
Project-specific protected paths come from the Graph Powers config via _config
(each list is extended, never replaced).
"""
import json
import sys
import typing

from pathlib import Path, PurePath

# Project parameters come from _config, never hardcoded — this file is byte-for-byte
# the same in every repository that installs the plugin.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _config as gp  # noqa: E402

# Generic exact filename matches — apply to every project
PROTECTED_EXACT_DEFAULT = {
    ".env",
    ".env.local",
    ".env.production",
    ".env.development",
    ".env.test",
    "bun.lockb",
    "bun.lock",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
}

# Generic path segment matches — block any directory named these
PROTECTED_SEGMENTS_DEFAULT = {"credentials", "secrets", "api-keys"}

# Generic directory containment — patterns with separators
PROTECTED_CONTAINS_DEFAULT = [
    ".git/",
    ".git\\",
]


def load_extra_protections() -> tuple[set[str], set[str], list[str]]:
    """Read protectedFiles from the project config to extend the generic lists.
    Returns (exact, segments, contains).
    """
    pf = gp.protected_files()
    return (
        set(pf.get("exact") or []),
        set(pf.get("segments") or []),
        list(pf.get("contains") or []),
    )


_extra_exact, _extra_segments, _extra_contains = load_extra_protections()
PROTECTED_EXACT = PROTECTED_EXACT_DEFAULT | _extra_exact
PROTECTED_SEGMENTS = PROTECTED_SEGMENTS_DEFAULT | _extra_segments
PROTECTED_CONTAINS = PROTECTED_CONTAINS_DEFAULT + _extra_contains


def read_input() -> dict[str, object]:
    try:
        raw = sys.stdin.read()
        return typing.cast(dict[str, object], json.loads(raw)) if raw.strip() else {}
    except Exception:
        return {}


def deny(reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))


def allow() -> None:
    sys.exit(0)


def main() -> None:
    data: dict[str, object] = read_input()
    # Support both top-level and nested tool_input
    file_path = str(
        data.get("file_path")
        or typing.cast(dict[str, object], data.get("tool_input", {})).get("file_path", "")
    )

    if not file_path:
        allow()
        return

    # An entry without a separator is a filename — matched exactly, so ".env" never matches
    # "environment.ts". An entry WITH a separator is a repo-relative path, matched against the
    # tail of the target. Without this second form a project that declares "ops/secrets.yaml"
    # gets no protection and no warning, which is the worst of both.
    posix = PurePath(str(file_path)).as_posix()
    name = PurePath(str(file_path)).name
    for entry in PROTECTED_EXACT:
        e = str(entry).replace("\\", "/").lstrip("./")
        hit = (posix == e or posix.endswith("/" + e)) if "/" in e else (name == e)
        if hit:
            deny(f"BLOCKED: '{file_path}' is a protected file")
            return

    path_parts = set(PurePath(str(file_path)).parts)
    for segment in PROTECTED_SEGMENTS:
        if segment in path_parts:
            deny(f"BLOCKED: '{file_path}' contains protected path segment '{segment}'")
            return

    # Directory containment check for patterns that include separators
    for pattern in PROTECTED_CONTAINS:
        if pattern in file_path:
            deny(f"BLOCKED: '{file_path}' matches protected pattern '{pattern}'")
            return

    allow()


if __name__ == "__main__":
    main()
    sys.exit(0)
