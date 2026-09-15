#!/usr/bin/env python3
"""Refresh the native Grok Graph Powers package.

Grok's plugin bytes live in the client cache. Claude/Codex updates are owned by
``hooks/auto_update.py``; that worker must not call ``grok``. This script is the Grok
half: ``grok plugin marketplace update`` then ``grok plugin update``. It never writes
``hooks.json`` under the Grok home and never edits a project.

Operators may copy this file into the Grok user-hooks directory as a SessionStart
command, or run ``--scheduled`` from a timer. The installer does not install either
copy. An already-open Grok session keeps the previous files until it is restarted.

Interval is 15 minutes, matching the Claude/Codex clone timer. That is independent of
``autoUpdate.intervalHours`` (the SessionStart throttle for Claude/Codex only).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

PLUGIN = "graph-powers"
STATE_DIR = Path.home() / ".graph-powers"
STATE_FILE = STATE_DIR / "update-state.json"
LOG_FILE = STATE_DIR / "grok-update.log"
INTERVAL_SECONDS = 15 * 60


def read_state() -> dict:
    try:
        raw = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        return raw if isinstance(raw, dict) else {}
    except Exception:
        return {}


def write_state(patch: dict) -> None:
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        merged = {**read_state(), **patch}
        STATE_FILE.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")
    except Exception:
        pass


def log(line: str) -> None:
    stamp = time.strftime("%Y-%m-%dT%H:%M:%S")
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as handle:
            handle.write(f"{stamp} {line}\n")
    except Exception:
        pass


def due(state: dict) -> bool:
    last = state.get("lastGrokCheck")
    if not isinstance(last, (int, float)):
        return True
    return time.time() - last > INTERVAL_SECONDS


def grok_bin() -> str | None:
    explicit = os.environ.get("GROK_BIN")
    if explicit and Path(explicit).is_file():
        return explicit
    return shutil.which("grok")


def run(cmd: list[str], timeout: int = 300) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
        return proc.returncode, f"{proc.stdout}{proc.stderr}".strip()
    except Exception as exc:
        return 1, str(exc)


def plugin_version() -> str:
    binary = grok_bin()
    if not binary:
        return ""
    code, out = run([binary, "plugin", "list", "--json"], timeout=60)
    if code != 0:
        return ""
    try:
        payload = json.loads(out)
    except Exception:
        return ""
    rows = payload if isinstance(payload, list) else []
    for row in rows:
        if isinstance(row, dict) and row.get("name") == PLUGIN:
            return str(row.get("version") or "")
    return ""


def worker() -> int:
    binary = grok_bin()
    if not binary:
        write_state({"lastGrokCheck": time.time(), "lastGrokResult": "grok not on PATH"})
        log("skip: grok not on PATH")
        return 0

    before = plugin_version()
    mk_code, mk_out = run([binary, "plugin", "marketplace", "update", PLUGIN])
    up_code, up_out = run([binary, "plugin", "update", PLUGIN])
    after = plugin_version()
    changed = bool(before and after and before != after) or (
        "already up to date" not in up_out.lower() and up_code == 0 and up_out
    )
    result = "updated" if changed else "no change"
    if mk_code != 0:
        result = f"marketplace update failed: {mk_out[:200]}"
    elif up_code != 0:
        result = f"plugin update failed: {up_out[:200]}"

    notice = ""
    if changed and after:
        notice = (
            f"[graph-powers] Grok plugin {before or '?'} -> {after}. "
            "Start a new session to load the new files."
        )
    write_state(
        {
            "lastGrokCheck": time.time(),
            "lastGrokResult": result,
            "lastGrokVersion": after or before,
            "pendingGrokNotice": notice,
        }
    )
    log(f"{result} before={before or '?'} after={after or '?'} mk={mk_code} up={up_code}")
    if mk_out:
        log(f"marketplace: {mk_out[:500]}")
    if up_out:
        log(f"update: {up_out[:500]}")
    return 0


def announce(state: dict) -> None:
    notice = state.get("pendingGrokNotice")
    if not isinstance(notice, str) or not notice:
        return
    write_state({"pendingGrokNotice": ""})
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": notice,
                }
            }
        )
    )


def detach() -> None:
    env = dict(os.environ)
    subprocess.Popen(
        [sys.executable, str(Path(__file__).resolve()), "--worker"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
        start_new_session=True,
    )


def main() -> int:
    args = set(sys.argv[1:])
    if "--worker" in args or "--scheduled" in args:
        if "--scheduled" in args:
            if os.environ.get("GRAPH_POWERS_NO_AUTO_UPDATE"):
                return 0
            if not due(read_state()):
                return 0
        return worker()

    state = read_state()
    announce(state)
    if os.environ.get("GRAPH_POWERS_NO_AUTO_UPDATE"):
        return 0
    if due(state):
        write_state({"lastGrokCheck": time.time()})
        detach()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        raise SystemExit(0)
