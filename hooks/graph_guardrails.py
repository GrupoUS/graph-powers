#!/usr/bin/env python3
"""graph_guardrails.py - the executable half of the task-graph guardrails.

Why this exists
---------------
The harness routed work through subagents long before it could stop them. The
stopping rules lived in `${rulesDir}/execution.md:36` as "~3 tentativas / ~5
spawns", labelled in the file itself as *recomendada, nao limite rigido*, and in
`subagent_stop.py`, which counts failures and then always exits 0. A counter that
cannot say no is telemetry, not a guardrail. Measured 2026-08-19: none of the
five doctrine guardrails were enforced by code.

What it enforces
----------------
G1  kill switch      - while `AGENT_STOP` exists at the repo root, every tool
                       call is denied. The only way to stop a headless run today
                       is a human pressing Esc in an interactive session; this is
                       the file-based equivalent that also works when nobody is
                       watching.
G2  spawn ceiling    - total `Agent` spawns per session. A runaway fan-out burns
                       a budget in one afternoon and the first sign of it is the
                       bill.
G3  round ceiling    - spawns of the SAME `subagent_type` per session. This is
                       "max rounds per loop" in the only shape a hook can see: a
                       loop that is not converging keeps re-spawning the same
                       specialist.
G4  write lease      - when `.graph-powers/logs/write-lease.json` exists, `Write`/`Edit`
                       outside the declared paths is denied. That file is how the
                       orchestrator declares file ownership before a parallel
                       wave; without it this check stands down entirely.

What it deliberately does NOT enforce, and why
----------------------------------------------
*Two writers on one file, detected by agent identity.* It is not implementable
here: a hook cannot tell a subagent from the main thread — they run in-process
with the same `CLAUDE_CODE_SESSION_ID` and the same PID (verified empirically,
see the same note in `git_commit_gate.py`). G4 enforces the actionable half —
"touch only the files you own" — and the structural half lives where the
violation is actually born, in `.claude/workflows/ultra-build.js`
(`splitByFileOwnership`), which re-slices a wave so two tasks claiming the same
path never run in parallel.

*A spend ceiling in an interactive session.* The CLI exposes `--max-budget-usd`
in print mode only (`claude --help`, 2.1.235 — there is no `--max-turns` either).
G2/G3 are the controllable proxy in-session; the real ceiling belongs on the
headless wrapper that `${CLAUDE_PLUGIN_ROOT}/skills/second-opinion/` uses.

Contract
--------
Reads the hook payload on stdin, exits 0 to allow, prints a
`permissionDecision: "deny"` payload to block. Never blocks on its own failure:
a guardrail that breaks the session when IT has a bug trains people to delete it.
Every ceiling has a per-command opt-in, in the same shape as the git gates —
`<PREFIXO>_ALLOW_SPAWN_OVER=1`, `<PREFIXO>_ALLOW_OFF_LEASE=1` — because a ceiling
with no override is not a guardrail, it is a wall, and walls get torn down.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

# Project parameters (branch, protected branches, opt-in prefix, ceilings) come from
# _config, never hardcoded — this file is byte-for-byte the same in every repository
# that installs the plugin.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _config as gp  # noqa: E402


STOP_FILE = "AGENT_STOP"
LEASE_FILE = ".graph-powers/logs/write-lease.json"
COUNTER_DIR = ".graph-powers/logs/sessions"

OPT_IN_SPAWN = gp.opt_in("SPAWN_OVER")
OPT_IN_LEASE = gp.opt_in("OFF_LEASE")




def limits(root: Path) -> dict[str, int]:
    """Ceilings live in the project config so tuning them is a reviewable diff."""
    return gp.graph_limits(gp.load(root))


def deny(reason: str) -> None:
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        },
        sys.stdout,
    )
    print()  # the hook payload must be newline-terminated


def bump(root: Path, session: str, key: str) -> int:
    """Per-session counters on disk. Session id keys the file, so a fresh session
    starts from zero without anyone cleaning up."""
    path = root / COUNTER_DIR / f"{session or 'unknown'}-guardrails.json"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        state = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except Exception:
        state = {}
    if not isinstance(state, dict):
        state = {}
    count = int(state.get(key, 0)) + 1
    state[key] = count
    try:
        path.write_text(json.dumps(state), encoding="utf-8")
    except Exception:
        pass  # counting is best-effort; never break the session over telemetry
    return count


def lease_paths(root: Path) -> list[str] | None:
    """None = no lease declared = this check stands down."""
    path = root / LEASE_FILE
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if isinstance(data, dict):
        data = data.get("paths", [])
    if not isinstance(data, list):
        return None
    return [str(p) for p in data if isinstance(p, str)]


def opted_in(name: str, payload: dict[str, Any]) -> bool:
    """Same shape as the git gates: an inline env assignment on the command, or a
    real environment variable for a whole approved run."""
    if os.environ.get(name) == "1":
        return True
    tool_input = payload.get("tool_input")
    blob = json.dumps(tool_input) if isinstance(tool_input, dict) else ""
    return f"{name}=1" in blob


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    if not isinstance(payload, dict):
        return 0

    root = gp.project_dir(payload)
    tool = payload.get("tool_name")
    session = str(payload.get("session_id") or "")

    # G1 — kill switch. Checked before anything else and for every tool: the
    # point of a stop file is that it stops the run, not that it stops the parts
    # of the run this hook happens to understand.
    if (root / STOP_FILE).exists():
        deny(
            f"KILL SWITCH: {STOP_FILE} exists at the repo root, so every tool call is denied. "
            "This is the deliberate stop for a running loop. Do not work around it and do not "
            f"delete the file yourself — the person who created it removes it (`rm {STOP_FILE}`) "
            "when the run may continue."
        )
        return 0

    if tool == "Agent":
        lim = limits(root)
        total = bump(root, session, "spawns")
        if total > lim["maxSpawnsPerSession"] and not opted_in(OPT_IN_SPAWN, payload):
            deny(
                f"SPAWN CEILING: {total} agent spawns this session, over the limit of "
                f"{lim['maxSpawnsPerSession']}. A fan-out this wide usually means the work is being "
                "re-delegated instead of finished — check in with the user, or narrow the task. "
                f"To proceed deliberately, set {OPT_IN_SPAWN}=1 in the environment."
            )
            return 0

        tool_input = payload.get("tool_input")
        agent_type = ""
        if isinstance(tool_input, dict):
            agent_type = str(tool_input.get("subagent_type") or "")
        if agent_type:
            rounds = bump(root, session, f"agent:{agent_type}")
            if rounds > lim["maxRoundsPerAgent"] and not opted_in(OPT_IN_SPAWN, payload):
                deny(
                    f"ROUND CEILING: `{agent_type}` has been spawned {rounds} times this session, over "
                    f"the limit of {lim['maxRoundsPerAgent']}. Re-spawning the same specialist this "
                    "often is the signature of a loop that is not converging — the fix is a different "
                    f"hypothesis, not another round. To proceed deliberately, set {OPT_IN_SPAWN}=1."
                )
                return 0
        return 0

    if tool in {"Write", "Edit", "NotebookEdit"}:
        declared = lease_paths(root)
        if declared is None:
            return 0  # no lease on disk = nobody declared ownership = nothing to enforce
        tool_input = payload.get("tool_input")
        target = ""
        if isinstance(tool_input, dict):
            target = str(tool_input.get("file_path") or tool_input.get("notebook_path") or "")
        if not target:
            return 0
        try:
            rel = str(Path(target).resolve().relative_to(root.resolve()))
        except Exception:
            rel = target
        if any(rel == p or rel.startswith(p.rstrip("/") + "/") for p in declared):
            return 0
        if opted_in(OPT_IN_LEASE, payload):
            return 0
        deny(
            f"WRITE LEASE: `{rel}` is outside the paths declared in {LEASE_FILE} "
            f"({', '.join(declared[:6])}{'…' if len(declared) > 6 else ''}). During a parallel wave "
            "each node owns a disjoint file set; writing outside it is how two nodes end up editing "
            f"the same file. Finish inside your lease, or set {OPT_IN_LEASE}=1 if the lease is stale."
        )
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
