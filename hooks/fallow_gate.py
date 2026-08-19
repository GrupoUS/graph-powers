#!/usr/bin/env python3
"""Fallow agent gate — Claude Code PreToolUse hook.

Blocks `git commit` / `git push` when `fallow audit` returns verdict=fail
(i.e. NEW, error-severity dead-code/structure findings in the current changeset
vs the merge-base). Mirrors `fallow hooks install --target agent` but in Python
(repo Cardinal Rule 3 forbids .sh/.bash) and with no `jq` dependency.

Severity comes from `.fallowrc.json::rules` — dead-code categories are `warn`
(never block), structural-correctness ones (`unresolved-imports`,
`unlisted-dependencies`, `circular-dependencies`, `route-collision`,
`dynamic-segment-name-conflict`) are `error` → those are what trip a `fail`
verdict. `--gate new-only` (fallow audit default) only counts findings the
changeset introduced, so pre-existing issues never block.

Design guarantees:
- Fail-open: any runtime problem (bun missing, parse error, timeout) -> exit 0.
- Scoped: only fires on git commit/push Bash calls.
- Reproducible: pinned fallow version.

Disable once:  set env FALLOW_GATE_DISABLE=1
Make advisory: change the `return 2` below to `return 0`
Remove:        delete the PreToolUse handler in .claude/settings.json
"""

import json
import os
import re
import subprocess
import sys

FALLOW_VERSION = "2.99.0"  # keep in sync with CI + /refactor-code Iron Law (pin version)
GIT_WRITE_RE = re.compile(r"(^|[\s;|&()])git\s+(commit|push)(\s|$)")


def main() -> int:
    if os.environ.get("FALLOW_GATE_DISABLE"):
        return 0

    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0  # no/invalid hook input -> never block

    command = ((payload.get("tool_input") or {}).get("command")) or ""
    if not GIT_WRITE_RE.search(command):
        return 0  # not a commit/push -> ignore

    # Static command string (no payload interpolation) -> shell=True is safe and
    # resolves bunx.cmd on Windows.
    audit_cmd = (
        f"bunx fallow@{FALLOW_VERSION} audit "
        "--format json --quiet --explain --gate-marker agent"
    )
    try:
        proc = subprocess.run(
            audit_cmd, shell=True, capture_output=True, text=True, timeout=120
        )
    except Exception as exc:  # bun missing, timeout, etc.
        print(f"fallow-gate: audit could not run ({exc}); skipping.", file=sys.stderr)
        return 0

    try:
        report = json.loads(proc.stdout or "{}")
    except Exception:
        print("fallow-gate: unparseable audit output; skipping.", file=sys.stderr)
        return 0

    if report.get("error"):
        print(
            f"fallow-gate: audit runtime error ({report.get('message', '')}); skipping.",
            file=sys.stderr,
        )
        return 0

    if report.get("verdict") == "fail":
        print(
            "fallow-gate: BLOCKED — fallow audit found NEW error-severity issues "
            "in this changeset (unresolved/unlisted import, cycle, or route collision).",
            file=sys.stderr,
        )
        print(proc.stdout, file=sys.stderr)
        print(
            "Fix the findings, or set FALLOW_GATE_DISABLE=1 to bypass this once.",
            file=sys.stderr,
        )
        return 2  # PreToolUse: exit 2 blocks the tool call

    return 0


if __name__ == "__main__":
    sys.exit(main())
