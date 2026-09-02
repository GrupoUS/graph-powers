#!/usr/bin/env python3
"""session_context.py - Minimal SessionStart context tag.

Outputs a short additionalContext tag (project + package manager + branch + gates), plus the
one line that puts the execution floor in force for the session.

AGENTS.md, CLAUDE.md, and overlay markdown are loaded by the runtime
via the claudeMd mechanism. This hook intentionally does NOT duplicate them
in additionalContext — that would double-load the same content into every
turn's system prompt. The execution-floor line is a pointer and one sentence
of posture, not the file: see `execution_floor()` for why that half is
mirrored and the other half is not.

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


def execution_floor() -> str:
    """The line that makes the execution floor active rather than merely available.

    A pointer plus the posture, never a copy: `references/execution-floor.md` is the source, and a
    second copy of it here would be the divergence this plugin exists to end. The posture sentence
    is mirrored on purpose — a pointer nobody follows routes nothing, and the one decision that has
    to survive a session that never opens the file is whether to delegate at all.

    The path is resolved from this file rather than written down, because the same bytes run from
    the plugin root on Claude Code and from a clone on Codex. Fail-open: if anything about the
    lookup fails, the relative name still names the file.
    """
    where = "references/execution-floor.md"
    try:
        floor = Path(__file__).resolve().parent.parent / "references" / "execution-floor.md"
        if floor.is_file():
            where = floor.as_posix()
    except Exception:
        pass
    return (
        # mirror of execution-floor.md §1 — the posture, not the ladder
        "Execution floor in force: L1-L2 is a direct edit and delegating is refused; L3+ delegates, "
        "read-only agents in the background, a whole batch in one message, one writer per file. "
        f"Read it before spawning anything: {where}"
    )


def solution_ladder() -> str:
    """One line that puts the solution ladder in force for the main thread.

    Same shape as `execution_floor()`: the posture, mirrored, and a pointer to the file — never the
    file. Subagents get theirs from `subagent_context.py`, because SessionStart context stops here.
    """
    where = "references/shared/025-solution-ladder.md"
    try:
        ladder = Path(__file__).resolve().parent.parent / "references" / "shared" / "025-solution-ladder.md"
        if ladder.is_file():
            where = ladder.as_posix()
    except Exception:
        pass
    return (
        # mirror of 025-solution-ladder.md — the rungs and the tie-break, not the file
        "Solution ladder in force: does it need to exist → already here → stdlib → native → installed "
        "dependency → one line → the minimum that works; unsure of the tier, take the lower one and "
        f"say so. {where}"
    )


def lifecycle_pointer() -> str:
    """Return one fail-open, bounded pointer to the lifecycle routing authority."""
    relative = "skills/skill-improve/SKILL.md#proactive-lifecycle"
    where = relative
    try:
        candidate = Path(__file__).resolve().parent.parent / "skills" / "skill-improve" / "SKILL.md"
        if candidate.is_file():
            where = candidate.as_posix() + "#proactive-lifecycle"
    except Exception:
        pass
    prefix = (
        "Proactive skill lifecycle: when skill-improve's description selects the task, Mode A/B rows emit the "
        "matching lifecycle entry first before blocker/refusal/permission/tool observation/clarification/plan/"
        "draft/edit, even without tools/Write; read "
    )
    pointer = f"{prefix}{where} before work."
    if len(pointer.encode("utf-8")) <= 512:
        return pointer
    return f"{prefix}{relative} before work."


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
    # for longer — the tag said `lint` while the local linter was absent, the Stop hook caught
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
        gate_tag += f" | NOT INSTALLED: {detail} — install the project-local dependency"

    base_tag = f"[{project_name}]" + (f" {pkg_tag}" if pkg_tag else "")
    prefixes = {
        "startup": f"{base_tag} | branch:{branch}{gate_tag}",
        "compact": f"{base_tag} | branch:{branch}{gate_tag} (post-compact)",
        "resume": f"{base_tag} resumed | branch:{branch}",
    }
    additional_context = prefixes.get(source, f"{base_tag} | branch:{branch}")
    additional_context = (
        f"{additional_context}\n{execution_floor()}\n{solution_ladder()}\n{lifecycle_pointer()}"
    )

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
