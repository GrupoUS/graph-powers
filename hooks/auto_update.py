#!/usr/bin/env python3
"""auto_update.py — keeps the installed harness at the published version, without being asked.

Trigger: SessionStart (startup | resume | compact), on both harnesses. A user-level scheduler may
also invoke the worker directly when no session is open.

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

The worker asks the routes whose source and cache lifecycle it can safely own to update:

  Claude Code   claude plugin marketplace update <mp> && claude plugin update <plugin>@<mp>
  Codex native  git -C <source> pull --ff-only, then reinstall and regenerate native companions
  Codex CLI     the stable clone fallback, only when no native plugin is installed

The native Codex route updates the shared Codex home. Codex Desktop uses that same route when its
app-server is backed by the same Codex home, so the cache and generated role companions are updated
for both clients. A running process still keeps its loaded definitions: the next new conversation
or a full Desktop restart is the apply boundary, and this worker never kills a client for you.

Claude Code keeps the running version directory and picks a new one up at the next start; native
Codex loads the refreshed cache and companions at the next session boundary; clone Codex artefacts
keep a stable root and are read at startup. The honest state after any update is "restart to apply".

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
    home = user_home()
    return home / STATE_DIR / STATE_FILE if home else None


def user_home() -> Path | None:
    home = os.environ.get("HOME") or os.environ.get("USERPROFILE")
    return Path(home) if home else None


def codex_home() -> Path | None:
    """Resolve the Codex home shared by CLI and a Desktop app-server when configured that way."""
    explicit = os.environ.get("CODEX_HOME")
    if explicit:
        return Path(explicit)
    home = user_home()
    return home / ".codex" if home else None


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
        "intervalHours": hours
        if isinstance(hours, int) and not isinstance(hours, bool) and hours > 0
        else DEFAULT_INTERVAL_HOURS,
        "claude": node.get("claude") is not False,
        "codex": node.get("codex") is not False,
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
    return 0


def spawn_worker(opts: dict[str, typing.Any]) -> None:
    """Start the network half detached, and do not wait for it."""
    try:
        env = dict(os.environ)
        env["GRAPH_POWERS_UPDATE_CLAUDE"] = "1" if opts["claude"] else "0"
        env["GRAPH_POWERS_UPDATE_CODEX"] = "1" if opts["codex"] else "0"
        # Detach, so the update outlives this hook and never holds the session open.
        # `start_new_session` is `setsid`, and CPython silently ignores it on Windows — the worker
        # then stays in the console's process group and dies with it, or holds it open. The two
        # creation flags are the Windows equivalent, and asking for them by `getattr` keeps this
        # importable on platforms where `subprocess` does not define them.
        detach: dict[str, typing.Any] = {"start_new_session": True}
        if os.name == "nt":
            detach = {
                "creationflags": getattr(subprocess, "DETACHED_PROCESS", 0x00000008)
                | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)
            }
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
        proc = subprocess.run(
            cmd,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
        return proc.returncode, f"{proc.stdout}{proc.stderr}"
    except Exception as exc:
        return 1, str(exc)


def run_json(cmd: list[str], timeout: int = 180) -> tuple[int, dict[str, typing.Any]]:
    """Run a JSON-producing command without mixing stderr warnings into the JSON stream."""
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
        try:
            payload = json.loads(proc.stdout.strip())
        except Exception:
            payload = {}
        return proc.returncode, payload if isinstance(payload, dict) else {}
    except Exception:
        return 1, {}


def which(binary: str) -> bool:
    return shutil.which(binary) is not None


def codex_command() -> str | None:
    """Prefer the executable a Desktop/CLI environment explicitly exposes, then PATH."""
    configured = os.environ.get("CODEX_CLI_PATH")
    if configured:
        if Path(configured).is_file():
            return configured
        found = shutil.which(configured)
        if found:
            return found
    return shutil.which("codex")


def runtime_command() -> str | None:
    """Use the native runtime for the generator, with Bun as the installed fallback."""
    return shutil.which("node") or shutil.which("bun")


def registered_version() -> str:
    """The version Claude Code records for this plugin at user scope, or "".

    Deliberately not the version of the directory this hook is running from. `claude plugin
    update` unpacks a *new* version directory and leaves the running one exactly as it was —
    which is why it says "restart to apply". Reading the running copy would therefore report
    "no change" after every successful update.
    """
    home = user_home()
    if not home:
        return ""
    try:
        raw = json.loads(
            (home / ".claude/plugins/installed_plugins.json").read_text(encoding="utf-8")
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
    home = codex_home()
    if home is None:
        return {}
    try:
        raw = json.loads((home / "graph-powers-installed.json").read_text(encoding="utf-8"))
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
    status_code, status = git(root, "status", "--porcelain")
    if status_code != 0 or status.strip():
        return False, before
    if git(root, "pull", "--ff-only")[0] != 0:
        return False, before
    after = git(root, "rev-parse", "HEAD")[1].strip()
    return (before != after and bool(after)), after


def codex_marketplace(binary: str) -> dict[str, typing.Any]:
    code, payload = run_json([binary, "plugin", "marketplace", "list", "--json"], timeout=60)
    if code != 0:
        return {}
    for marketplace in payload.get("marketplaces", []):
        if isinstance(marketplace, dict) and marketplace.get("name") == MARKETPLACE:
            return marketplace
    return {}


def codex_native_plugin(binary: str) -> dict[str, typing.Any]:
    code, payload = run_json(
        [binary, "plugin", "list", "--marketplace", MARKETPLACE, "--json"], timeout=60
    )
    if code != 0:
        return {}
    for plugin in payload.get("installed", []):
        if isinstance(plugin, dict) and plugin.get("pluginId") == f"{PLUGIN}@{MARKETPLACE}":
            return plugin
    return {}


def source_version(root: Path) -> str:
    """Read the version from the source tree without trusting a generated cache directory."""
    for relative in (".codex-plugin/plugin.json", ".claude-plugin/plugin.json", "package.json"):
        try:
            raw = json.loads((root / relative).read_text(encoding="utf-8"))
            version = raw.get("version") if isinstance(raw, dict) else None
            if version:
                return str(version)
        except Exception:
            continue
    return ""


def git_head(root: Path | None) -> str:
    if root is None:
        return ""
    code, output = git(root, "rev-parse", "HEAD")
    return output.strip() if code == 0 else ""


def codex_source(binary: str) -> tuple[Path | None, str]:
    """Find the configured marketplace root, falling back to the clone install manifest."""
    marketplace = codex_marketplace(binary)
    source_meta = marketplace.get("marketplaceSource")
    source_type = source_meta.get("sourceType") if isinstance(source_meta, dict) else "local"
    root_value = marketplace.get("root")
    if not root_value:
        native = codex_native_plugin(binary)
        source = native.get("source")
        root_value = source.get("path") if isinstance(source, dict) else None
    if not root_value:
        root_value = codex_manifest().get("pluginRoot")
    root = Path(str(root_value)) if root_value else None
    return (root if root and root.is_dir() else None), str(source_type or "local")


def refresh_codex_source(
    binary: str, root: Path | None, source_type: str
) -> tuple[bool, str, Path | None]:
    """Refresh a local source or a Git marketplace, preserving dirty trees and branch choices."""
    before = git_head(root)
    if source_type == "git":
        code, _ = run(
            [binary, "plugin", "marketplace", "upgrade", MARKETPLACE, "--json"], timeout=300
        )
        if code != 0:
            return False, before, root
        refreshed_root, _ = codex_source(binary)
        after = git_head(refreshed_root)
        return bool(after and after != before), after or before, refreshed_root
    if root is not None and which("git"):
        moved, head = pull_clone(root)
        return moved, head, root
    return False, before, root


def generate_codex_companions(root: Path) -> bool:
    runtime = runtime_command()
    home = codex_home()
    generator = root / "codex/native-plugin.mjs"
    if not runtime or home is None or not generator.is_file():
        return False
    generation_code, _ = run([runtime, str(generator), "--out", str(home / "agents")], timeout=300)
    return generation_code == 0


def complete_codex_native_update(
    binary: str,
    *,
    head: str,
    version_source: str,
    version_before: str,
    cache_needed: bool,
    cache_ok: bool,
    agents_pending: bool,
    generation_ok: bool,
) -> tuple[list[str], str]:
    notices: list[str] = []
    if cache_needed and cache_ok:
        after = codex_native_plugin(binary)
        version_after = str(after.get("version") or version_source or version_before)
        if generation_ok:
            notices.append(
                f"Codex native/Desktop plugin {version_before or '?'} -> {version_after}"
            )
        else:
            notices.append(
                f"Codex native/Desktop cache refreshed to {version_after}; companion agents pending"
            )
        version_before = version_after
    elif agents_pending and generation_ok:
        notices.append("Codex native/Desktop companion agents regenerated")
    elif cache_needed and not cache_ok:
        write_state({"lastResult": "Codex native update failed"})

    if not cache_needed or cache_ok:
        write_state(
            {
                "codexSourceHead": head,
                "codexNativeVersion": version_before or version_source,
                "codexAgentsPending": not generation_ok,
            }
        )
    return notices, version_before


def update_codex_native(binary: str) -> tuple[list[str], str]:
    """Update the native Codex cache and its companion roles from the configured Git source."""
    state = read_state()
    native_before = codex_native_plugin(binary)
    root, source_type = codex_source(binary)
    version_before = str(native_before.get("version") or "")
    if root is None:
        return [], version_before

    moved, head, root = refresh_codex_source(binary, root, source_type)
    if root is None:
        return [], version_before
    version_source = source_version(root)
    previous_head = str(state.get("codexSourceHead") or "")
    agents_pending = state.get("codexAgentsPending") is True
    source_changed = moved or bool(previous_head and head and previous_head != head)
    cache_needed = (
        not native_before
        or source_changed
        or (bool(version_source) and version_source != version_before)
    )
    cache_ok = True

    if cache_needed:
        code, _ = run([binary, "plugin", "add", f"{PLUGIN}@{MARKETPLACE}", "--json"], timeout=300)
        cache_ok = code == 0

    generation_ok = not agents_pending and not cache_needed
    if cache_ok and (cache_needed or agents_pending):
        generation_ok = generate_codex_companions(root)

    return complete_codex_native_update(
        binary,
        head=head,
        version_source=version_source,
        version_before=version_before,
        cache_needed=cache_needed,
        cache_ok=cache_ok,
        agents_pending=agents_pending,
        generation_ok=generation_ok,
    )


def worker(*, claude_enabled: bool | None = None, codex_enabled: bool | None = None) -> int:
    before = registered_version()
    notices: list[str] = []
    codex_version = ""
    codex_changed = False
    should_update_claude = (
        os.environ.get("GRAPH_POWERS_UPDATE_CLAUDE") == "1"
        if claude_enabled is None
        else claude_enabled
    )
    should_update_codex = (
        os.environ.get("GRAPH_POWERS_UPDATE_CODEX") == "1"
        if codex_enabled is None
        else codex_enabled
    )

    if should_update_claude and which("claude"):
        run(["claude", "plugin", "marketplace", "update", MARKETPLACE])
        # The qualified `<plugin>@<marketplace>` form, because the bare name is not found — and
        # the command exits 0 when it fails, so nothing downstream may trust its exit code.
        run(["claude", "plugin", "update", f"{PLUGIN}@{MARKETPLACE}"])
        after_claude = registered_version()
        if before and after_claude and after_claude != before:
            notices.append(f"Claude Code plugin {before} -> {after_claude}")

    if should_update_codex:
        binary = codex_command()
        if binary:
            native = codex_native_plugin(binary)
            if native:
                native_notices, codex_version = update_codex_native(binary)
                notices.extend(native_notices)
                codex_changed = bool(native_notices)
            elif which("git"):
                # Legacy clone fallback for installations that have not switched to the native
                # marketplace. Keep this branch user-scoped and avoid changing a project checkout.
                source = str(codex_manifest().get("pluginRoot") or "")
                runtime = runtime_command()
                if source and Path(source).is_dir() and runtime:
                    moved, head = pull_clone(Path(source))
                    if moved:
                        code, _ = run(
                            [
                                runtime,
                                str(Path(source) / "bin/graph-powers.mjs"),
                                "--target",
                                "codex",
                                "--scope",
                                "user",
                                "--force",
                                "--skip-marketplace",
                            ],
                            timeout=300,
                        )
                        if code == 0:
                            notices.append(f"Codex artefacts regenerated at {head[:8]}")

    after = registered_version()
    if notices or (before and after and before != after):
        version = codex_version if codex_changed else after or codex_version or "a newer version"
        write_state(
            {
                "pendingNotice": (
                    f"[graph-powers] updated to {version} "
                    f"({'; '.join(notices) or 'plugin files replaced'}). "
                    "Start a new session; fully quit and reopen ChatGPT Desktop if it was already open."
                ),
                "lastUpdate": time.time(),
                "lastVersion": version,
            }
        )
    else:
        write_state({"lastResult": "no change"})
    return 0


def scheduled_worker() -> int:
    """Run the out-of-session worker only when the user-level switch permits it."""
    opts = settings(gp.load(payload={}))
    if not opts["enabled"]:
        return 0
    return worker(claude_enabled=opts["claude"], codex_enabled=opts["codex"])


if __name__ == "__main__":
    try:
        if "--scheduled" in sys.argv:
            sys.exit(scheduled_worker())
        sys.exit(worker() if "--worker" in sys.argv else main())
    except Exception:
        # Fail-open, without exception. This hook exists to keep a harness current; taking a
        # session down to do it would be a worse trade than never updating at all.
        sys.exit(0)
