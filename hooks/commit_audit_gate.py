#!/usr/bin/env python3
"""commit_audit_gate.py — runs the project's own pre-commit audit, if it declared one.

Trigger: PreToolUse on Bash, and only for `git commit` / `git push`.

Why this is a parameter and not a tool
--------------------------------------
This started life as a hard-wired call to one dead-code auditor, pinned to one version, fetched
from the network on every single commit. In one repository that was a deliberate choice somebody
made. Shipped to every repository that installs this plugin it is something else entirely: a
third-party download and execution on a machine whose owner never asked for it, in the middle of
the one operation they least want delayed.

So the tool is the project's to name. Declare it and it runs; declare nothing and this hook does
nothing at all, which is the default.

    "gates": {
      "preCommitAudit": {
        "command": "bunx fallow@2.99.0 audit --format json --quiet --gate new-only",
        "timeout": 120
      }
    }

The contract with that command is the ordinary one: **exit 0 means the commit may proceed.**
Anything else blocks it, and the command's own output is what the person reads — this hook adds
no interpretation of its own, because a gate that paraphrases its tool is a gate that will
eventually paraphrase it wrongly.

Escape hatch: `<PREFIX>_ALLOW_AUDIT=1` inline in the command, the same shape every other gate in
this plugin uses. A ceiling with no override is not a guardrail, it is a wall.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import typing
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _config as gp  # noqa: E402

GIT_WRITE_RE = re.compile(r"(^|[\s;|&()])git\s+(commit|push)(\s|$)")
DEFAULT_TIMEOUT = 120


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0  # no or invalid hook input -> never block

    if not isinstance(payload, dict):
        return 0

    command = ((payload.get("tool_input") or {}).get("command")) or ""
    if not GIT_WRITE_RE.search(command):
        return 0

    cfg = gp.load(payload=payload)

    # Same opt-in vocabulary as the git gates, and per project, so an approval given in one
    # repository never counts in another.
    if gp.opted_in("AUDIT", command, cfg):
        return 0

    gates = cfg.get("gates")
    audit = gates.get("preCommitAudit") if isinstance(gates, dict) else None
    if isinstance(audit, str):
        audit = {"command": audit}
    if not isinstance(audit, dict):
        return 0

    audit_command = audit.get("command")
    if not isinstance(audit_command, str) or not audit_command.strip():
        return 0

    timeout = audit.get("timeout")
    if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout <= 0:
        timeout = DEFAULT_TIMEOUT

    try:
        proc = subprocess.run(
            audit_command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(gp.project_dir(payload)),
            check=False,
        )
    except Exception as exc:
        # Fail-open. The audit could not run — that is a fact about the environment, not a verdict
        # about the changeset, and blocking on it would teach people to disable the hook.
        print(f"commit-audit: could not run ({exc}); skipping.", file=sys.stderr)
        return 0

    if proc.returncode == 0:
        return 0

    # 127 is the shell saying the command does not exist. That is a fact about the machine, not a
    # verdict about the changeset — the same class as the exception above, and it fails open for
    # the same reason. Blocking every commit because a tool was never installed is how a project
    # deletes the hook instead of installing the tool.
    if proc.returncode == 127:
        print(f"commit-audit: `{audit_command.split()[0]}` is not on PATH; skipping.",
              file=sys.stderr)
        return 0

    print("commit-audit: BLOCKED — the audit this project declared exited "
          f"{proc.returncode}.", file=sys.stderr)
    print((proc.stdout or "").strip()[:4000], file=sys.stderr)
    print((proc.stderr or "").strip()[:2000], file=sys.stderr)
    print(f"Fix the findings, or prefix the command with {gp.opt_in('AUDIT', cfg)}=1 to pass "
          "this one.", file=sys.stderr)
    return 2  # PreToolUse: exit 2 blocks the tool call


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
