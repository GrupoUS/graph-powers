#!/usr/bin/env python3
"""Claude Code status line shipped with Graph Powers.

Claude Code pipes a JSON payload on stdin and prints whatever this script prints. The line reads
only that payload (and `.git/HEAD` for the branch), so it never spawns a process:

    ◆ model effort | ▸ dir ⎇ branch | ● context used | 5h 7d left · spend used | ⌘ vim

The 5-hour and 7-day windows show what is left, answering "how much can I still do"; context and
spend show what was used.

`--subagents` renders the subagent rows instead. `--install` copies this file to a stable path
under the Claude home (`CLAUDE_CONFIG_DIR` when set) and points `statusLine` / `subagentStatusLine` at it. A plugin cannot set
`statusLine` itself, and its cache path changes with every version, so AGENT_SETUP.md re-runs
`--install` after each plugin update to keep the copy current.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

# A directory or branch outside the locale code page (cp1252 on Windows) must not garble the line.
for stream in (sys.stdin, sys.stdout):
    try:
        stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    except Exception:
        pass

SCRIPT_NAME = "graph-powers-statusline.py"

# 16-colour ANSI codes and single-character icons: no emoji rendering, nothing to load.
C = {
    "r": "\033[0m",
    "1": "\033[31m",  # red
    "2": "\033[32m",  # green
    "3": "\033[33m",  # yellow
    "4": "\033[34m",  # blue
    "5": "\033[35m",  # magenta
    "6": "\033[36m",  # cyan
    "8": "\033[90m",  # gray
}
I = {"model": "◆", "dir": "▸", "branch": "⎇", "ctx": "●", "warn": "!", "vim": "⌘"}


def used_display(used_pct):
    """What was used: green below 50%, yellow from 50%, red with a warning from 90%."""
    used = round(used_pct)  # compare the number that is shown
    color = C["1"] if used >= 90 else C["3"] if used >= 50 else C["2"]
    return color, f"{I['warn'] if used >= 90 else ''}{used}%"


def left_display(used_pct):
    """What is left: green above 50%, yellow up to 50%, red with a warning up to 10%."""
    left = round(max(0.0, 100 - used_pct))
    color = C["1"] if left <= 10 else C["3"] if left <= 50 else C["2"]
    return color, f"{I['warn'] if left <= 10 else ''}{left}% left"


def get_context_display(context_window):
    used_pct = (context_window or {}).get("used_percentage")
    if used_pct is None:
        return f"{C['8']}?{C['r']}"
    color, text = used_display(used_pct)
    return f"{color}{I['ctx']} {text}{C['r']}"


def get_directory_display(workspace):
    current_dir = (workspace or {}).get("current_dir", "")
    project_dir = (workspace or {}).get("project_dir", "")
    if project_dir and (current_dir == project_dir or current_dir.startswith(f"{project_dir}/")):
        name = current_dir[len(project_dir) :].lstrip("/") or os.path.basename(project_dir)
    else:
        name = os.path.basename(project_dir or current_dir or "unknown")
    return f"{C['6']}{I['dir']} {name}{C['r']}"


def get_git_branch(workspace):
    """Read `.git/HEAD` directly, following a linked worktree's `gitdir:` file."""
    project_dir = (workspace or {}).get("project_dir", "")
    if not project_dir:
        return ""
    head_path = os.path.join(project_dir, ".git", "HEAD")
    try:
        git_file = os.path.join(project_dir, ".git")
        if os.path.isfile(git_file):
            with open(git_file, encoding="utf-8") as f:
                gitdir = f.read().strip().removeprefix("gitdir: ")
            head_path = os.path.join(project_dir, gitdir, "HEAD")
        with open(head_path, encoding="utf-8") as f:
            content = f.read().strip()
        if content.startswith("ref: refs/heads/"):
            return content[16:]
        if len(content) == 40:
            return content[:7]
    except OSError:
        pass
    return ""


def get_branch_display(branch):
    if not branch:
        return ""
    if branch in ("main", "master"):
        color = C["4"]
    elif branch in ("dev", "develop"):
        color = C["2"]
    elif branch.startswith("feature/"):
        color, branch = C["3"], branch[8:]
    else:
        color = C["8"]
    return f" {C['8']}{I['branch']}{C['r']} {color}{branch}{C['r']}"


def get_model_display(model, used_pct, effort=""):
    """The resolved model id plus effort, coloured by context pressure."""
    name = model.get("id") or model.get("display_name") or "Claude"
    color = C["1"] if used_pct >= 90 else C["3"] if used_pct >= 75 else C["6"]
    effort_display = f" {C['8']}{effort}{C['r']}" if effort else ""
    return f"{color}{I['model']} {name}{C['r']}{effort_display}"


def get_limits_display(rate_limits):
    """Subscription windows; absent outside claude.ai subscriptions."""
    parts = []
    for key, label, display in (
        ("five_hour", "5h", left_display),
        ("seven_day", "7d", left_display),
        ("spend_limit", "spend", used_display),
    ):
        pct = ((rate_limits or {}).get(key) or {}).get("used_percentage")
        if pct is None:
            continue
        color, text = display(pct)
        parts.append(f"{color}{label} {text}{C['r']}")
    return " ".join(parts)


def show_subagent_status():
    try:
        tasks = json.load(sys.stdin).get("tasks") or []
    except Exception:
        return  # no rows: Claude Code keeps its default subagent rows
    for task in tasks:
        if not isinstance(task, dict):
            continue
        model = task.get("model")
        if not model or not task.get("id"):
            continue  # keep Claude Code's default row until the model is resolved
        name = task.get("name") or task.get("type") or "Agent"
        content = f"{name} · {C['6']}{I['model']} {model}{C['r']}"
        if task.get("effort"):
            content += f" {C['8']}{task['effort']}{C['r']}"
        label = task.get("label") or task.get("description")
        if label:
            content += f" · {str(label).splitlines()[0]}"
        if task.get("tokenCount") is not None:
            content += f" · {task['tokenCount']} tokens"
            if task.get("contextWindowSize"):
                content += f" ({task['tokenCount'] / task['contextWindowSize']:.0%})"
        print(json.dumps({"id": task["id"], "content": content}, ensure_ascii=False))


def main():
    try:
        data = json.load(sys.stdin)
        context_window = data.get("context_window") or {}
        workspace = data.get("workspace") or {}
        used_pct = context_window.get("used_percentage") or 0  # null early in a session
        effort = (data.get("effort") or {}).get("level", "")
        branch = (data.get("worktree") or {}).get("branch") or get_git_branch(workspace)
        parts = [
            get_model_display(data.get("model") or {}, used_pct, effort),
            get_directory_display(workspace) + get_branch_display(branch),
            get_context_display(context_window),
        ]
        limits = get_limits_display(data.get("rate_limits"))
        if limits:
            parts.append(limits)
        mode = (data.get("vim") or {}).get("mode", "")
        if mode:
            parts.append(f"{C['5']}{I['vim']} {mode}{C['r']}")
        print(f" {C['8']}|{C['r']} ".join(parts))
    except Exception:
        print(f"{C['6']}{I['model']} Claude{C['r']}")


def is_graph_powers_line(entry) -> bool:
    return isinstance(entry, dict) and SCRIPT_NAME in str(entry.get("command", ""))


def install(adopt: bool) -> int:
    """Refresh the stable copy and point the two status-line settings at it.

    A status line the operator configured is kept unless `adopt` is set; Claude Code's own
    `~/.claude/settings.json` keeps every other key. An unreadable settings file stops the install
    before anything is written.
    """
    raw_home = os.environ.get("HOME") or os.environ.get("USERPROFILE")
    config_dir = os.environ.get("CLAUDE_CONFIG_DIR")
    if not config_dir and not raw_home:
        print("statusline --install: HOME/USERPROFILE is not set; nothing written")
        return 1
    claude_home = Path(config_dir) if config_dir else Path(raw_home) / ".claude"
    settings_file = claude_home / "settings.json"
    try:
        text = settings_file.read_text(encoding="utf-8") if settings_file.exists() else "{}"
        settings = json.loads(text)
    except (OSError, ValueError) as error:
        print(f"statusline --install: {settings_file} is unreadable ({error}); nothing written")
        return 1
    if not isinstance(settings, dict):
        print(f"statusline --install: {settings_file} is not a JSON object; nothing written")
        return 1

    target = claude_home / "scripts" / SCRIPT_NAME
    body = Path(__file__).resolve().read_bytes()
    if target.exists() and target.read_bytes() == body:
        print(f"script current: {target.as_posix()}")
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            backup = target.with_name(f"{SCRIPT_NAME}.bak")
            shutil.copy2(target, backup)
            print(f"previous script kept at {backup.as_posix()}")
        target.write_bytes(body)
        print(f"script installed: {target.as_posix()}")

    command = f'python3 -X utf8 "{target.as_posix()}"'
    changed = False
    for key, wanted in (("statusLine", command), ("subagentStatusLine", f"{command} --subagents")):
        current = settings.get(key)
        if current is not None and not is_graph_powers_line(current) and not adopt:
            print(f"{key}: kept the operator's own command; re-run with --adopt to replace it")
            continue
        entry = {**(current if isinstance(current, dict) else {}), "type": "command", "command": wanted}
        if entry == current:
            print(f"{key}: current")
            continue
        if isinstance(current, dict) and not is_graph_powers_line(current):
            print(f"{key}: replaced {current.get('command')!r}")
        settings[key] = entry
        changed = True
        print(f"{key}: {wanted}")
    if changed:
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        settings_file.write_text(f"{json.dumps(settings, indent=2, ensure_ascii=False)}\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    if "--install" in sys.argv:
        sys.exit(install(adopt="--adopt" in sys.argv))
    elif "--subagents" in sys.argv:
        show_subagent_status()
    else:
        main()
