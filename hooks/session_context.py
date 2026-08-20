#!/usr/bin/env python3
"""session_context.py - Minimal SessionStart context tag.

Outputs a short additionalContext tag (project + package manager + branch + gates).

AGENTS.md, CLAUDE.md, and overlay markdown are loaded by the runtime
via the claudeMd mechanism. This hook intentionally does NOT duplicate them
in additionalContext — that would double-load the same content into every
turn's system prompt.

Trigger: SessionStart (startup | resume | compact)
"""

import json
import subprocess
import sys
import threading
import typing
from pathlib import Path

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



def read_input() -> dict[str, object]:
    """Read the payload without assuming stdin is a POSIX pipe.

    `select.select` only accepts sockets on Windows — given a pipe it raises, the payload silently
    becomes `{}`, and the `cwd` the Codex CLI sends is lost, so the hook resolves the wrong project.
    A thread with a join timeout is the same non-blocking read everywhere.
    """
    box: list[str] = []
    reader = threading.Thread(target=lambda: box.append(sys.stdin.read()), daemon=True)
    reader.start()
    reader.join(0.2)
    try:
        raw = box[0] if box else ""
        return typing.cast(dict[str, object], json.loads(raw)) if raw.strip() else {}
    except Exception:
        return {}


def get_git_branch(project_dir: str) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=3,
            cwd=project_dir,
            check=False,
        )
        return result.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def get_project_dir(payload: dict[str, object] | None = None) -> str:
    """The repository this session is in — resolved from the payload first.

    Codex CLI does not export `CLAUDE_PROJECT_DIR`; it puts the working directory in the payload,
    and `.claude/rules/hooks.md` requires every hook that reads the payload to pass it in. This one
    read the payload and then asked without it, so under Codex the tag named whatever repository
    the hook process happened to start in — the project name, the branch and the gate list all
    belonged to somebody else's checkout.
    """
    return str(gp.project_dir(payload))


def load_project_config(project_dir: str) -> dict[str, object]:
    return gp.load(Path(project_dir))


def main() -> None:
    data: dict[str, object] = read_input()
    source = str(data.get("source", "startup"))

    project_dir = get_project_dir(data)
    branch = get_git_branch(project_dir)

    config = load_project_config(project_dir)
    project = typing.cast(dict[str, object], config.get("project", {}))
    project_name = (
        str(project.get("name", "")).strip().upper() or Path(project_dir).name.upper()
    )
    tooling = typing.cast(dict[str, object], config.get("tooling", {}))
    pkg_mgr = str(tooling.get("packageManager", "")).strip()
    pkg_tag = pkg_mgr.capitalize() if pkg_mgr else ""

    # The gate list is whatever the project declared. Naming a gate the project does not
    # have would be worse than naming none: a line that reads as covered and never runs.
    #
    # Declaring one whose tool is not installed has exactly the same effect, one level down, and
    # for longer — the tag said `lint` while `oxlint` was absent from PATH, the Stop hook caught
    # `FileNotFoundError` and returned, and nothing ever said so. `format` is listed here too
    # although it is not a gate: `ultracite.py` runs it after every edit, so a missing formatter
    # means a session silently stops being formatted.
    commands = typing.cast(dict[str, object], tooling.get("commands", {}))
    declared = [k for k in ("typeCheck", "lint", "test", "build") if commands.get(k)]
    absent: list[tuple[str, str]] = []
    for key in ("typeCheck", "lint", "test", "build", "format"):
        value = commands.get(key)
        if not value:
            continue
        tool = gp.missing_tool(str(value))
        if tool:
            absent.append((key, tool))
    unusable = {k for k, _ in absent}
    gates = "+".join(k for k in declared if k not in unusable)
    gate_tag = f" | gates: {gates}" if gates else ""
    if absent:
        detail = ", ".join(f"{key} needs `{tool}`" for key, tool in absent)
        gate_tag += f" | NOT INSTALLED: {detail} — install globally or these never run"

    base_tag = f"[{project_name}]" + (f" {pkg_tag}" if pkg_tag else "")
    prefixes = {
        "startup": f"{base_tag} | branch:{branch}{gate_tag}",
        "compact": f"{base_tag} | branch:{branch}{gate_tag} (post-compact)",
        "resume": f"{base_tag} resumed | branch:{branch}",
    }
    additional_context = prefixes.get(source, f"{base_tag} | branch:{branch}")

    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": additional_context,
        }
    }
    print(json.dumps(output))


if __name__ == "__main__":
    main()
    sys.exit(0)
