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
import _config as gp

# The payload arrives on stdin as UTF-8, but Python decodes it with the locale code page unless
# told otherwise — cp1252 on a Windows machine. A file path or a branch name outside that page
# then raises `UnicodeDecodeError`, every hook here falls open, and `protect_files` permits a
# write it was meant to refuse. Reconfiguring costs nothing and is guarded because a stdin that
# is already detached has no `reconfigure`.
try:
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
except Exception:
    pass


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

    # Every check below reads the path as a string. A symlink is a string that names one file and
    # writes another, so `ln -s .env notes.md` followed by a write to `notes.md` walked past all
    # three lists and landed in `.env` — the guardrail matched `notes.md`, which is protected by
    # nothing, and the bytes went where the link pointed.
    #
    # Both spellings are then checked: the link's own path stays in play because a project may
    # protect the link itself, and the target is added because that is where the write lands.
    # `resolve()` touches the filesystem and can raise on a loop or a dead mount, so a failure
    # falls back to the literal path — fewer names checked, never fewer than before.
    candidates = [str(file_path)]
    try:
        resolved = Path(str(file_path)).resolve()
        if str(resolved) != str(file_path):
            candidates.append(str(resolved))
    except Exception:
        pass

    for candidate in candidates:
        if _judge(candidate, str(file_path)):
            return

    allow()


def _judge(candidate: str, reported: str) -> bool:
    """True when `candidate` hit a list and the refusal was printed.

    It returns rather than exiting because there are two names to try and `allow()` exits — an
    early exit here would check the link and never the target, which is the whole defect.
    """
    # An entry without a separator is a filename — matched exactly, so ".env" never matches
    # "environment.ts". An entry WITH a separator is a repo-relative path, matched against the
    # tail of the target. Without this second form a project that declares "ops/secrets.yaml"
    # gets no protection and no warning, which is the worst of both.
    posix = PurePath(candidate).as_posix()
    name = PurePath(candidate).name
    for entry in PROTECTED_EXACT:
        e = str(entry).replace("\\", "/").removeprefix("./")
        hit = (posix == e or posix.endswith("/" + e)) if "/" in e else (name == e)
        if hit:
            deny(f"BLOCKED: '{reported}' is a protected file")
            return True

    path_parts = set(PurePath(candidate).parts)
    for segment in PROTECTED_SEGMENTS:
        if segment in path_parts:
            deny(f"BLOCKED: '{reported}' contains protected path segment '{segment}'")
            return True

    # Directory containment check for patterns that include separators
    for pattern in PROTECTED_CONTAINS:
        # Compare separator-normalised, both sides. The default list carries `.git/` AND `.git\\`
        # precisely because this comparison used to be raw; normalising here is what lets a
        # project declare `config/secrets/` once and have it hold on every platform.
        if str(pattern).replace("\\", "/") in posix:
            deny(f"BLOCKED: '{reported}' matches protected pattern '{pattern}'")
            return True

    return False


if __name__ == "__main__":
    main()
    sys.exit(0)
