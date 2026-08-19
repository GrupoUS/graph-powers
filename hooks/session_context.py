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
import typing
from pathlib import Path

# Project parameters come from _config, never hardcoded — this file is byte-for-byte
# the same in every repository that installs the plugin.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _config as gp  # noqa: E402


def read_input() -> dict[str, object]:
    try:
        import select

        if select.select([sys.stdin], [], [], 0.2)[0]:
            raw = sys.stdin.read()
            return (
                typing.cast(dict[str, object], json.loads(raw)) if raw.strip() else {}
            )
    except Exception:
        pass
    return {}


def get_git_branch(project_dir: str) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=3,
            cwd=project_dir,
        )
        return result.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def get_project_dir() -> str:
    return str(gp.project_dir())


def load_project_config(project_dir: str) -> dict[str, object]:
    return gp.load(Path(project_dir))


def main() -> None:
    data: dict[str, object] = read_input()
    source = str(data.get("source", "startup"))

    project_dir = get_project_dir()
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
    commands = typing.cast(dict[str, object], tooling.get("commands", {}))
    gates = "+".join(k for k in ("typeCheck", "lint", "test", "build") if commands.get(k))
    gate_tag = f" | gates: {gates}" if gates else ""

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
