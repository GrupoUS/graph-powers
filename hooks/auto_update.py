#!/usr/bin/env python3
"""auto_update.py — keeps the installed harness at the published version, without being asked.

Trigger: SessionStart (startup | resume | compact), on both harnesses.

The problem this solves
-----------------------
A plugin is a copy. The moment it is installed it starts ageing, and the person running it has
no reason to remember it exists — that is the point of a harness. Six months later, five machines
run five versions of guardrails that were supposed to be identical, which is the exact failure
mode this project was built to end, one level up.

What it does, and what it refuses to do
---------------------------------------
The hook itself does almost nothing: it reads a throttle file and, at most once per interval,
starts a detached worker. It never waits for the network. SessionStart has a timeout, and a
guardrail that delays every session start by a DNS lookup is a guardrail people uninstall.

The worker asks each harness to update **itself**, through its own supported command:

  Claude Code   claude plugin marketplace update <mp> && claude plugin update <plugin>
  Codex CLI     npx -y graph-powers@latest --target codex --scope user --force

Neither of those touches the running session. Claude Code unpacks a new version directory and
picks it up at the next start; the Codex artefacts are read at startup too. So the honest report
is "updated — restart to apply", and that is what the next session prints, once.

What it will not do, at any setting: change anything in the project. Config, rules, AGENTS.md and
the three authorities are the project's, and a background process is the last thing that should
be editing them.

Turn it off:  `"autoUpdate": {"enabled": false}` in .graph-powers/config.json,
              or GRAPH_POWERS_NO_AUTO_UPDATE=1 in the environment.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import typing
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _config as gp  # noqa: E402

PLUGIN = "graph-powers"
MARKETPLACE = "graph-powers"
STATE_DIR = ".graph-powers"
STATE_FILE = "update-state.json"
DEFAULT_INTERVAL_HOURS = 12


# ── state ────────────────────────────────────────────────────────────────────

def state_path() -> Path | None:
    home = os.environ.get("HOME") or os.environ.get("USERPROFILE")
    return Path(home) / STATE_DIR / STATE_FILE if home else None


def read_state() -> dict[str, typing.Any]:
    path = state_path()
    if path is None:
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return raw if isinstance(raw, dict) else {}
    except Exception:
        return {}


def write_state(patch: dict[str, typing.Any]) -> None:
    path = state_path()
    if path is None:
        return
    try:
        merged = {**read_state(), **patch}
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")
    except Exception:
        pass


# ── settings ─────────────────────────────────────────────────────────────────

def settings(cfg: dict[str, typing.Any]) -> dict[str, typing.Any]:
    node = cfg.get("autoUpdate")
    if not isinstance(node, dict):
        node = {}
    enabled = node.get("enabled")
    hours = node.get("intervalHours")
    return {
        "enabled": enabled is not False and not os.environ.get("GRAPH_POWERS_NO_AUTO_UPDATE"),
        "intervalHours": hours if isinstance(hours, int) and not isinstance(hours, bool) and hours > 0
        else DEFAULT_INTERVAL_HOURS,
        "claude": node.get("claude") is not False,
        "codex": node.get("codex") is not False,
    }


def plugin_root() -> Path:
    env = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if env:
        return Path(env)
    return Path(__file__).resolve().parent.parent


# ── the hook half: fast, and never on the network ────────────────────────────

def read_payload() -> dict[str, typing.Any]:
    try:
        import select

        if select.select([sys.stdin], [], [], 0.2)[0]:
            raw = sys.stdin.read()
            return json.loads(raw) if raw.strip() else {}
    except Exception:
        pass
    return {}


def announce(state: dict[str, typing.Any]) -> str:
    """The one line a finished update earns — printed once, then cleared.

    A background update nobody is told about is indistinguishable from no update at all: the
    session keeps running the old files and the person keeps reporting the old behaviour.
    """
    pending = state.get("pendingNotice")
    if not isinstance(pending, str) or not pending:
        return ""
    write_state({"pendingNotice": ""})
    return pending


def main() -> int:
    payload = read_payload()
    cfg = gp.load(payload=payload)
    opts = settings(cfg)

    state = read_state()
    notice = announce(state)

    if opts["enabled"]:
        last = state.get("lastCheck")
        age = time.time() - last if isinstance(last, (int, float)) else None
        due = age is None or age > opts["intervalHours"] * 3600
        if due:
            # Recorded before the worker starts, not after. If the worker dies — no network, a
            # laptop closing — the throttle still holds, and the next session does not retry
            # immediately. A check that retries every session is a check that never backs off.
            write_state({"lastCheck": time.time()})
            spawn_worker(opts)

    if notice:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": notice,
            }
        }))
    return 0


def spawn_worker(opts: dict[str, typing.Any]) -> None:
    """Start the network half detached, and do not wait for it."""
    try:
        env = dict(os.environ)
        env["GRAPH_POWERS_PLUGIN_ROOT"] = str(plugin_root())
        env["GRAPH_POWERS_UPDATE_CLAUDE"] = "1" if opts["claude"] else "0"
        env["GRAPH_POWERS_UPDATE_CODEX"] = "1" if opts["codex"] else "0"
        subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), "--worker"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=env,
            start_new_session=True,
        )
    except Exception:
        pass


# ── the worker half: allowed to be slow, never allowed to block ──────────────

def run(cmd: list[str], timeout: int = 180) -> tuple[int, str]:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
        return proc.returncode, f"{proc.stdout}{proc.stderr}"
    except Exception as exc:
        return 1, str(exc)


def which(binary: str) -> bool:
    from shutil import which as _which

    return _which(binary) is not None


def installed_version(root: Path) -> str:
    try:
        raw = json.loads((root / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
        return str(raw.get("version") or "")
    except Exception:
        return ""


def published_version() -> str:
    """The version on the registry, or "" when it cannot be established.

    An empty string is a real answer here and the callers treat it as one: no network, no
    registry, no update. Guessing a version would be worse than not checking — it would trigger a
    reinstall of something that is already current, and on Codex that costs a re-approval.
    """
    for cmd in (["npm", "view", PLUGIN, "version"], ["bun", "pm", "view", PLUGIN, "version"]):
        if not which(cmd[0]):
            continue
        code, out = run(cmd, timeout=60)
        if code != 0:
            continue
        for line in reversed(out.strip().splitlines()):
            token = line.strip().strip('"')
            if token and token[0].isdigit():
                return token
    return ""


def worker() -> int:
    root = Path(os.environ.get("GRAPH_POWERS_PLUGIN_ROOT") or plugin_root())
    before = installed_version(root)
    notices: list[str] = []

    if os.environ.get("GRAPH_POWERS_UPDATE_CLAUDE") == "1" and which("claude"):
        run(["claude", "plugin", "marketplace", "update", MARKETPLACE])
        code, out = run(["claude", "plugin", "update", PLUGIN])
        # `update` exits 0 with "already up to date" too — the version comparison below is what
        # decides whether anything is worth telling the user, not this exit code.
        if code == 0 and "up to date" not in out.lower():
            notices.append("Claude Code plugin updated")

    if os.environ.get("GRAPH_POWERS_UPDATE_CODEX") == "1" and which("codex"):
        home = os.environ.get("HOME")
        manifest = Path(home) / ".codex/graph-powers-installed.json" if home else None
        if manifest is not None and manifest.is_file():
            latest = published_version()
            current = ""
            try:
                current = str(json.loads(manifest.read_text(encoding="utf-8")).get("version") or "")
            except Exception:
                pass
            # Only when the registry genuinely moved. Regenerating unchanged Codex artefacts is
            # not free: `.codex/hooks.json` is trusted by content, so rewriting it costs the user
            # a `/hooks` re-approval and leaves the guardrails inert until they give it.
            if latest and current and latest != current:
                runner = "bunx" if which("bunx") else ("npx" if which("npx") else "")
                if runner:
                    code, _ = run([runner, "-y", f"{PLUGIN}@latest", "--target", "codex",
                                   "--scope", "user", "--force", "--skip-marketplace"], timeout=300)
                    if code == 0:
                        notices.append(f"Codex artefacts regenerated at {latest}")

    after = installed_version(root)
    if notices or (before and after and before != after):
        version = after or published_version() or "a newer version"
        write_state({
            "pendingNotice": (
                f"[graph-powers] updated to {version} ({'; '.join(notices) or 'plugin files replaced'}). "
                "Restart the session to load it — hooks and skills are read at startup."
            ),
            "lastUpdate": time.time(),
            "lastVersion": after or version,
        })
    else:
        write_state({"lastResult": "no change"})
    return 0


if __name__ == "__main__":
    try:
        sys.exit(worker() if "--worker" in sys.argv else main())
    except Exception:
        # Fail-open, without exception. This hook exists to keep a harness current; taking a
        # session down to do it would be a worse trade than never updating at all.
        sys.exit(0)
