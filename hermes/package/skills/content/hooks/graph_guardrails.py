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
G2  spawn ceiling    - `Agent` spawns inside a rolling window
                       (`graphGuardrails.spawnWindowMinutes`, default 60). A
                       runaway fan-out burns a budget in one afternoon and the
                       first sign of it is the bill. The window is what makes
                       that the measured thing: counted from session start
                       instead, the ceiling became a session-lifetime quota, and
                       a long working session hit it on the FIRST spawn of an
                       unrelated later task and then refused every spawn for the
                       rest of the day. Observed here — a `/pr-review` fan-out of
                       three agents got one through and two denied, and the
                       review silently ran one path instead of three.
G3  round ceiling    - spawns of the SAME agent inside that same window. This is
                       "max rounds per loop" in the only shape a hook can see: a
                       loop that is not converging keeps re-spawning the same
                       specialist. The name is normalised, so a plugin agent and the
                       same agent named without its prefix share one counter
                       instead of granting double the rounds.
G4  write lease      - when `.graph-powers/logs/write-lease.json` exists, `Write`/`Edit`
                       outside the declared paths is denied. That file is how the
                       orchestrator declares file ownership before a parallel
                       wave; without it this check stands down entirely. The
                       producer is planning Phase C, from the `writeLease` array
                       `skills/planning/scripts/sdd.py validate` returns.

What it deliberately does NOT enforce, and why
----------------------------------------------
*Two writers on one file, detected by agent identity.* It is not implementable
here: a hook cannot tell a subagent from the main thread — they run in-process
with the same `CLAUDE_CODE_SESSION_ID` and the same PID (verified empirically,
see the same note in `git_commit_gate.py`). G4 enforces the actionable half —
"touch only the files you own" — and the structural half lives where the
violation is actually born, in planning Phase C. Its `sdd.py validate` preflight
rejects concurrent tasks that claim the same path before any wave or lease exists.

*A spend ceiling in an interactive session.* The CLI exposes `--max-budget-usd`
in print mode only (`claude --help`, 2.1.245 — there is no `--max-turns` either).
G2/G3 are the controllable proxy in-session; the real ceiling belongs on the
headless engine of `graph-powers:evaluator` Mode 5, the second opinion
(`${CLAUDE_PLUGIN_ROOT}/references/rubrics/evaluator-rubric.md`).

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
import time
from pathlib import Path, PurePath
from typing import Any

# Project parameters (branch, protected branches, opt-in prefix, ceilings) come from
# _config, never hardcoded — this file is byte-for-byte the same in every repository
# that installs the plugin.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _config as gp

# The payload arrives on stdin as UTF-8, but Python decodes it with the locale code page unless
# told otherwise — cp1252 on a Windows machine. A branch name or path outside that page then
# raises `UnicodeDecodeError`, the hook falls open, and a gate that should have denied releases.
try:
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
except Exception:
    pass



STOP_FILE = "AGENT_STOP"
LEASE_FILE = ".graph-powers/logs/write-lease.json"
COUNTER_DIR = ".graph-powers/logs/sessions"

OPT_IN_SPAWN = gp.opt_in("SPAWN_OVER")
OPT_IN_LEASE = gp.opt_in("OFF_LEASE")




def limits(root: Path) -> dict[str, int]:
    """Ceilings live in the project config so tuning them is a reviewable diff."""
    return gp.graph_limits(gp.load(root))


def deny(reason: str) -> None:
    gp.emit_pretool_deny(reason)


def counter_path(root: Path, session: str) -> Path:
    """Session id keys the file, so a fresh session starts from zero with no cleanup."""
    return root / COUNTER_DIR / f"{session or 'unknown'}-guardrails.json"


def read_state(path: Path) -> dict[str, Any]:
    try:
        state = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except Exception:
        state = {}
    return state if isinstance(state, dict) else {}


def write_state(path: Path, state: dict[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(state), encoding="utf-8")
    except Exception:
        pass  # counting is best-effort; never break the session over telemetry


def agent_key(subagent_type: str) -> str:
    """One specialist, one counter — whichever way the caller spelled the name.

    A plugin agent is addressed `<plugin>:<agent>`, and the same agent is still reachable by its
    unprefixed name from a project that has not migrated. Counted verbatim, the two spellings were
    two counters for one specialist, so a session that alternated them got double the rounds the
    ceiling grants — which is exactly the shape of the non-converging loop G3 exists to catch.
    Observed in this repository's own session log while that migration was in flight.

    Folding on the last segment can merge two different plugins that ship the same bare name. That
    errs toward firing early, which is the safe direction for a ceiling, and it is the same
    normalisation the CLI's own registry applies when a bare name resolves to a plugin agent.
    """
    return subagent_type.rsplit(":", 1)[-1].strip()


def recent_spawns(state: dict[str, Any], now: float, window_seconds: int) -> list[list[Any]]:
    """The spawn log, pruned to the window. Each entry is `[epoch_seconds, agent_key]`.

    Entries without a usable timestamp are dropped rather than placed at `now`: a counter written
    before this file kept timestamps cannot be located in time, and pretending it happened this
    second would deny work on evidence that does not exist.
    """
    raw = state.get("spawnEvents")
    if not isinstance(raw, list):
        return []
    out: list[list[Any]] = []
    for entry in raw:
        if not isinstance(entry, (list, tuple)) or len(entry) != 2:
            continue
        stamp, key = entry
        if isinstance(stamp, bool) or not isinstance(stamp, (int, float)):
            continue
        if 0 <= now - float(stamp) < window_seconds:
            out.append([float(stamp), str(key)])
    return out


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
    tool_input = gp.tool_input(payload)
    blob = json.dumps(tool_input) if tool_input else ""
    return f"{name}=1" in blob


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    if not isinstance(payload, dict):
        return 0

    root = gp.project_dir(payload)
    tool = gp.canonical_tool(payload)
    session = gp.session_id(payload)

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
        window_minutes = lim["spawnWindowMinutes"]
        now = time.time()
        path = counter_path(root, session)
        state = read_state(path)
        events = recent_spawns(state, now, window_minutes * 60)

        tool_input = gp.tool_input(payload)
        agent_type = ""
        if tool_input:
            agent_type = str(
                tool_input.get("subagent_type")
                or tool_input.get("subagentType")
                or tool_input.get("agent_type")
                or ""
            )
        key = agent_key(agent_type)

        total = len(events) + 1
        rounds = sum(1 for _, k in events if k == key) + 1 if key else 0
        override = opted_in(OPT_IN_SPAWN, payload)

        refusal = ""
        if total > lim["maxSpawnsPerSession"] and not override:
            refusal = (
                f"SPAWN CEILING: {len(events)} agent spawns in the last {window_minutes} minutes, "
                f"at the limit of {lim['maxSpawnsPerSession']}. A fan-out this wide in one window "
                "usually means the work is being re-delegated instead of finished. The direct path: "
                "finish the remaining work in this session and spawn again only for an independently "
                "useful scope, or check in with the user. To proceed "
                f"deliberately, set {OPT_IN_SPAWN}=1 in the environment."
            )
        elif key and rounds > lim["maxRoundsPerAgent"] and not override:
            refusal = (
                f"ROUND CEILING: `{key}` has been spawned {rounds - 1} times in the last "
                f"{window_minutes} minutes, at the limit of {lim['maxRoundsPerAgent']}. Re-spawning "
                "the same specialist this often is the signature of a loop that is not converging — "
                "the fix is a different hypothesis, not another round. The direct path: finish the "
                "remaining work in this session at the lowest rung that works, or surface what was "
                f"tried to the user. To proceed deliberately, set {OPT_IN_SPAWN}=1."
            )

        # A refused spawn never ran, so it is not recorded. Charging for it made the number in the
        # message grow with every retry until it described nothing that had happened: the ceiling
        # reported 27 spawns in a session where 25 ran and 2 were denied.
        if not refusal:
            events.append([now, key])
        state["spawnEvents"] = events
        state["spawnsInWindow"] = len(events)
        state["spawnsTotal"] = int(state.get("spawnsTotal") or 0) + (0 if refusal else 1)
        # Counters from the version that kept no timestamps cannot be placed in a window; leaving
        # them in the file would make it read as if they still counted.
        for stale in [k for k in state if k == "spawns" or k.startswith("agent:")]:
            del state[stale]
        write_state(path, state)

        if refusal:
            deny(refusal)
        return 0

    if tool in {"Write", "Edit", "NotebookEdit"}:
        declared = lease_paths(root)
        if declared is None:
            return 0  # no lease on disk = nobody declared ownership = nothing to enforce
        target = gp.file_path_from_payload(payload)
        if not target:
            return 0
        # Compare in POSIX form on both sides. `str(WindowsPath)` yields `src\\owned.ts` while the
        # lease on disk says `src/owned.ts`, so a raw comparison denies every write during exactly
        # the wave this exists to protect. `protect_files.py` already normalises this way.
        try:
            rel = Path(target).resolve().relative_to(root.resolve()).as_posix()
        except Exception:
            rel = PurePath(target).as_posix()
        declared = [str(p).replace("\\", "/").removeprefix("./") for p in declared]
        if any(rel == p.rstrip("/") or rel.startswith(p.rstrip("/") + "/") for p in declared):
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
