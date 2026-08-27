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

The worker asks each harness to update **itself**, through its own supported path:

  Claude Code   claude plugin marketplace update <mp> && claude plugin update <plugin>@<mp>
  Codex CLI     git -C <clone> pull --ff-only, then regenerate the artefacts from it
  Grok CLI      grok plugin marketplace update && grok plugin update <plugin>

The Codex worker half intentionally covers only the clone fallback: its install manifest records the
stable directory this worker may fast-forward and regenerate. Native Codex marketplace plugins are
client-owned and may replace a versioned cache while a process still retains old hook commands, so
this SessionStart worker does not update them. Cursor is client-owned for the same reason.

Claude Code keeps the running version directory and picks a new one up at the next start; clone
Codex artefacts keep a stable root and are read at startup. Grok uses its own updater and also needs
a restarted session. The honest state after any update is "restart to apply"; native clients not
owned here are documented separately in AGENT_SETUP.md.

What it will not do, at any setting: change anything in the project. Config, rules, AGENTS.md and
the three authorities are the project's, and a background process is the last thing that should
be editing them.

Turn it off:  `"autoUpdate": {"enabled": false}` in .graph-powers/config.json,
              or GRAPH_POWERS_NO_AUTO_UPDATE=1 in the environment.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import threading
import time
import typing
from pathlib import Path

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
        "grok": node.get("grok") is not False,
    }


# ── the hook half: fast, and never on the network ────────────────────────────

def read_payload() -> dict[str, typing.Any]:
    """Read the hook payload, without assuming stdin is a POSIX pipe.

    `select.select` was the previous approach and it only accepts sockets on Windows — with a pipe
    it raises, the payload silently becomes `{}`, and the `cwd` the Codex CLI passes is lost. A
    thread with a join timeout is the same non-blocking read on every platform.
    """
    box: list[str] = []
    reader = threading.Thread(target=lambda: box.append(sys.stdin.read()), daemon=True)
    reader.start()
    reader.join(0.2)
    try:
        raw = box[0] if box else ""
        return json.loads(raw) if raw.strip() else {}
    except Exception:
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
        env["GRAPH_POWERS_UPDATE_CLAUDE"] = "1" if opts["claude"] else "0"
        env["GRAPH_POWERS_UPDATE_CODEX"] = "1" if opts["codex"] else "0"
        env["GRAPH_POWERS_UPDATE_GROK"] = "1" if opts["grok"] else "0"
        # Detach, so the update outlives this hook and never holds the session open.
        # `start_new_session` is `setsid`, and CPython silently ignores it on Windows — the worker
        # then stays in the console's process group and dies with it, or holds it open. The two
        # creation flags are the Windows equivalent, and asking for them by `getattr` keeps this
        # importable on platforms where `subprocess` does not define them.
        detach: dict[str, typing.Any] = {"start_new_session": True}
        if os.name == "nt":
            detach = {"creationflags": getattr(subprocess, "DETACHED_PROCESS", 0x00000008)
                                     | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)}
        subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), "--worker"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=env,
            **detach,
        )
    except Exception:
        pass


# ── the worker half: allowed to be slow, never allowed to block ──────────────

def run(cmd: list[str], timeout: int = 180) -> tuple[int, str]:
    try:
        proc = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace",
                              timeout=timeout, check=False)
        return proc.returncode, f"{proc.stdout}{proc.stderr}"
    except Exception as exc:
        return 1, str(exc)


def which(binary: str) -> bool:
    return shutil.which(binary) is not None


def registered_version() -> str:
    """The version Claude Code records for this plugin at user scope, or "".

    Deliberately not the version of the directory this hook is running from. `claude plugin
    update` unpacks a *new* version directory and leaves the running one exactly as it was —
    which is why it says "restart to apply". Reading the running copy would therefore report
    "no change" after every successful update.
    """
    home = os.environ.get("HOME") or os.environ.get("USERPROFILE")
    if not home:
        return ""
    try:
        raw = json.loads(
            (Path(home) / ".claude/plugins/installed_plugins.json").read_text(encoding="utf-8")
        )
    except Exception:
        return ""
    for key, installs in (raw.get("plugins") or {}).items():
        if not str(key).startswith(f"{PLUGIN}@"):
            continue
        for install in installs or []:
            if install.get("scope") == "user":
                return str(install.get("version") or "")
    return ""


def codex_manifest() -> dict[str, typing.Any]:
    """What the Codex install recorded about itself, including where it was installed from."""
    home = os.environ.get("HOME") or os.environ.get("USERPROFILE")
    if not home:
        return {}
    try:
        raw = json.loads(
            (Path(home) / ".codex/graph-powers-installed.json").read_text(encoding="utf-8")
        )
        return raw if isinstance(raw, dict) else {}
    except Exception:
        return {}


def git(root: Path, *args: str, timeout: int = 120) -> tuple[int, str]:
    return run(["git", "-C", str(root), *args], timeout=timeout)


def pull_clone(root: Path) -> tuple[bool, str]:
    """Fast-forward the clone. Returns (moved, new HEAD).

    `--ff-only` deliberately. A merge commit created by a background process is a state nobody
    chose and nobody can explain later, and a clone somebody edited locally should refuse to
    update rather than quietly rewrite itself. A refusal here is a no-op, not a failure.
    """
    if git(root, "rev-parse", "--git-dir")[0] != 0:
        return False, ""
    before = git(root, "rev-parse", "HEAD")[1].strip()
    if git(root, "pull", "--ff-only")[0] != 0:
        return False, before
    after = git(root, "rev-parse", "HEAD")[1].strip()
    return (before != after and bool(after)), after


def worker() -> int:
    before = registered_version()
    notices: list[str] = []

    if os.environ.get("GRAPH_POWERS_UPDATE_CLAUDE") == "1" and which("claude"):
        run(["claude", "plugin", "marketplace", "update", MARKETPLACE])
        # The qualified `<plugin>@<marketplace>` form, because the bare name is not found — and
        # the command exits 0 when it fails, so nothing downstream may trust its exit code.
        run(["claude", "plugin", "update", f"{PLUGIN}@{MARKETPLACE}"])
        after_claude = registered_version()
        if before and after_claude and after_claude != before:
            notices.append(f"Claude Code plugin {before} -> {after_claude}")

    if os.environ.get("GRAPH_POWERS_UPDATE_CODEX") == "1" and which("codex"):
        source = str(codex_manifest().get("pluginRoot") or "")
        if source and Path(source).is_dir() and which("git"):
            moved, head = pull_clone(Path(source))
            # Only when the clone genuinely moved. Regenerating unchanged Codex artefacts is not
            # free: `.codex/hooks.json` is trusted by content, so rewriting it costs the user a
            # `/hooks` re-approval and leaves the guardrails inert until they give it.
            if moved:
                code, _ = run([
                    "node", str(Path(source) / "bin/graph-powers.mjs"),
                    "--target", "codex", "--scope", "user", "--force", "--skip-marketplace",
                ], timeout=300)
                if code == 0:
                    notices.append(f"Codex artefacts regenerated at {head[:8]}")

    if os.environ.get("GRAPH_POWERS_UPDATE_GROK") == "1" and which("grok"):
        run(["grok", "plugin", "marketplace", "update"])
        run(["grok", "plugin", "update", PLUGIN])

    after = registered_version()
    if notices or (before and after and before != after):
        version = after or "a newer version"
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
