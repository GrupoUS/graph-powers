#!/usr/bin/env python3
"""Cursor artefacts are generated from the Claude Code ones. This file proves they still match.

A hand-edited `hooks/hooks-cursor.json` is the divergence this repository exists to end, now
inside a single tree. The generator is `cursor/install.mjs`; this gate re-runs it and diffs.
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CLIENT_MARKER = "--graph-powers-client cursor"
CLIENT_MARKER_PREFIX = "--graph-powers-client"
CLIENT_MARKER_TOKENS = CLIENT_MARKER.split()
STOP_SCRIPT = "hooks/stop_verify.py"
SESSION_CONTEXT_SCRIPT = "hooks/session_context.py"


def load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def shell_tokens(command: str) -> list[str] | None:
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return None


def is_cursor_stop_command(command: str) -> bool:
    tokens = shell_tokens(command)
    if tokens is None or len(tokens) < 3:
        return False
    marker_pairs = sum(
        tokens[index : index + 2] == CLIENT_MARKER_TOKENS
        for index in range(len(tokens) - 1)
    )
    return (
        tokens[-2:] == CLIENT_MARKER_TOKENS
        and marker_pairs == 1
        and tokens.count(STOP_SCRIPT) == 1
        and tokens[-3] == STOP_SCRIPT
    )


def is_cursor_session_context_command(command: str) -> bool:
    tokens = shell_tokens(command)
    if tokens is None or len(tokens) < 3:
        return False
    marker_pairs = sum(
        tokens[index : index + 2] == CLIENT_MARKER_TOKENS
        for index in range(len(tokens) - 1)
    )
    return (
        tokens[-2:] == CLIENT_MARKER_TOKENS
        and marker_pairs == 1
        and tokens.count(SESSION_CONTEXT_SCRIPT) == 1
        and tokens[-3] == SESSION_CONTEXT_SCRIPT
    )


def run_negative_generator_probes() -> bool:
    probe = subprocess.run(
        [
            "bun",
            "-e",
            r'''
import { buildCursorHooks, mergePermissions } from "./cursor/install.mjs";
const cases = [
  ["malicious-stop-marker", "Stop", "python3 -X utf8 -c \"pass\" \"hooks/stop_verify.py\" --graph-powers-client cursor-malicious"],
  ["fake-stop", "Stop", "echo stop_verify.py"],
  ["malicious-session-marker", "SessionStart", "python3 -X utf8 -c \"pass\" \"hooks/session_context.py\" --graph-powers-client cursor-malicious"],
  ["fake-session-context", "SessionStart", "echo hooks/session_context.py"],
];
const rejected = cases.map(([name, event, command]) => {
  try {
    buildCursorHooks({ hooks: { [event]: [{ hooks: [{ type: "command", command }] }] } });
    return { name, rejected: false };
  } catch {
    return { name, rejected: true };
  }
});
const permissions = mergePermissions({
  autoRun: {
    allow_instructions: [],
    block_instructions: [],
    future_cursor_field: "preserve me",
  },
}, { autonomous: true });
const repeated = mergePermissions(permissions.next, { autonomous: true });
const guarded = { autoRun: { future_cursor_field: "leave untouched" } };
const guardedResult = mergePermissions(guarded, { autonomous: false });
process.stdout.write(JSON.stringify({
  rejected,
  preservesAutoRunFields: permissions.next.autoRun.future_cursor_field === "preserve me",
  idempotent: repeated.changed.length === 0,
  guardedUnchanged: guardedResult.next === guarded && guardedResult.changed.length === 0,
}));
''',
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        encoding="utf-8",
    )
    if probe.returncode != 0:
        print(probe.stderr)
        print("::error::Cursor generator negative probe could not run")
        return False
    result = json.loads(probe.stdout)
    rejected = result.get("rejected", [])
    if {case.get("name") for case in rejected} != {
        "malicious-stop-marker",
        "fake-stop",
        "malicious-session-marker",
        "fake-session-context",
    } or not all(case.get("rejected") is True for case in rejected):
        print("::error::Cursor generator must reject malformed Stop and SessionStart context commands")
        return False
    if result.get("preservesAutoRunFields") is not True:
        print("::error::Cursor permission merge must preserve unknown autoRun properties")
        return False
    if result.get("idempotent") is not True or result.get("guardedUnchanged") is not True:
        print("::error::Cursor permission merge must remain idempotent and leave guarded mode unchanged")
        return False
    return True


def main() -> int:
    claude_plugin = load(ROOT / ".claude-plugin/plugin.json")
    cursor_plugin = load(ROOT / ".cursor-plugin/plugin.json")
    pkg = load(ROOT / "package.json")
    claude_hooks = load(ROOT / "hooks/hooks.json")
    tracked = load(ROOT / "hooks/hooks-cursor.json")

    if not run_negative_generator_probes():
        return 1

    source_text = (ROOT / "hooks/hooks.json").read_text(encoding="utf-8")
    if CLIENT_MARKER_PREFIX in source_text:
        print("::error::canonical hooks/hooks.json must remain marker-free")
        return 1

    tracked_commands = [
        entry["command"]
        for entries in tracked.get("hooks", {}).values()
        for entry in entries
    ]
    tracked_stop = tracked.get("hooks", {}).get("stop", [])
    tokenized = [shell_tokens(command) for command in tracked_commands]
    marker_count = sum(
        tokens.count(CLIENT_MARKER_TOKENS[0])
        for tokens in tokenized
        if tokens is not None
    )
    marker_pair_count = sum(
        sum(
            tokens[index : index + 2] == CLIENT_MARKER_TOKENS
            for index in range(len(tokens) - 1)
        )
        for tokens in tokenized
        if tokens is not None
    )
    if any(tokens is None for tokens in tokenized) or marker_count != 2 or marker_pair_count != 2:
        print(
            "::error::Cursor client marker must occur exactly on the generated Stop and SessionStart context hooks"
        )
        return 1
    if len(tracked_stop) != 1 or not is_cursor_stop_command(tracked_stop[0]["command"]):
        print("::error::Cursor client marker must only appear on the generated stop verifier")
        return 1
    stop_command = tracked_stop[0]["command"]
    tracked_session = tracked.get("hooks", {}).get("sessionStart", [])
    context_commands = [
        entry["command"]
        for entry in tracked_session
        if SESSION_CONTEXT_SCRIPT in entry.get("command", "")
    ]
    if len(context_commands) != 1 or not is_cursor_session_context_command(context_commands[0]):
        print("::error::Cursor session context must carry exactly the generated client marker")
        return 1
    context_command = context_commands[0]
    if any(
        CLIENT_MARKER_TOKENS[0] in tokens
        for command, tokens in zip(tracked_commands, tokenized, strict=True)
        if command not in {stop_command, context_command} and tokens is not None
    ):
        print("::error::Cursor client marker must only appear on generated Stop and session context hooks")
        return 1

    versions = {
        "plugin.json": claude_plugin.get("version"),
        "package.json": pkg.get("version"),
        ".cursor-plugin/plugin.json": cursor_plugin.get("version"),
    }
    if len(set(versions.values())) != 1:
        print(f"::error::version mismatch across manifests: {versions}")
        return 1

    if cursor_plugin.get("hooks") != "./hooks/hooks-cursor.json":
        print("::error::.cursor-plugin/plugin.json must point at hooks/hooks-cursor.json, not the Claude file")
        return 1

    raw = json.dumps(tracked)
    if "CLAUDE_PLUGIN_ROOT" in raw:
        print("::error::hooks-cursor.json still carries ${CLAUDE_PLUGIN_ROOT} — Cursor never sets it")
        return 1

    generated = subprocess.run(
        [
            "bun",
            "-e",
            """
import { readFileSync } from "node:fs";
import { buildCursorHooks, buildPluginManifest } from "./cursor/install.mjs";
const hooks = JSON.parse(readFileSync("hooks/hooks.json", "utf8"));
const claude = JSON.parse(readFileSync(".claude-plugin/plugin.json", "utf8"));
const built = buildCursorHooks(hooks);
const { skipped, ...file } = built;
process.stdout.write(JSON.stringify({
  file,
  skipped,
  manifest: buildPluginManifest(claude),
}));
""",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        encoding="utf-8",
    )
    if generated.returncode != 0:
        print(generated.stderr)
        print("::error::cursor/install.mjs failed to emit")
        return 1

    data = json.loads(generated.stdout)
    if data["file"] != tracked:
        print("::error::hooks/hooks-cursor.json is stale — run: bun cursor/install.mjs --emit-only")
        return 1

    # Keywords and description can drift in the tracked manifest independently of the hook
    # list; the generator is still the owner of both, so the whole file has to match.
    if data["manifest"] != cursor_plugin:
        print("::error::.cursor-plugin/plugin.json is stale — run: bun cursor/install.mjs --emit-only")
        return 1

    skipped = set(data["skipped"])
    if skipped != {"PermissionRequest", "Notification", "SubagentStart"}:
        print(f"::error::unexpected omitted Cursor events: {sorted(skipped)}")
        return 1

    commands = [
        entry["command"]
        for entries in tracked["hooks"].values()
        for entry in entries
    ]
    expected_commands = sum(
        len(group.get("hooks", []))
        for event, groups in claude_hooks.get("hooks", {}).items()
        if event not in skipped
        for group in groups
    )
    if len(commands) != expected_commands:
        print(
            "::error::expected "
            f"{expected_commands} generated Cursor registrations, found {len(commands)}"
        )
        return 1
    joined = "\n".join(commands)
    if "tool_approver.py" in joined or "notify.py" in joined:
        print("::error::a skipped Claude event leaked into the Cursor hook list")
        return 1
    if "smart_bash_approver.py" not in joined:
        print("::error::smart_bash_approver is missing from Cursor preToolUse")
        return 1

    with tempfile.TemporaryDirectory(prefix="gp-cursor-session-") as raw:
        project = Path(raw)
        home = project / "home"
        home.mkdir()
        (project / ".graph-powers").mkdir()
        (project / ".graph-powers" / "config.json").write_text(
            json.dumps({"project": {"name": "cursor-session"}}), encoding="utf-8"
        )
        result = subprocess.run(
            context_command,
            shell=True,
            cwd=ROOT,
            input=json.dumps({"cwd": str(project), "source": "startup"}),
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            check=False,
            env={
                **{
                    key: value
                    for key, value in os.environ.items()
                    if key not in {"HOME", "USERPROFILE", "CLAUDE_CONFIG_DIR", "GROK_HOME", "CODEX_HOME"}
                },
                "HOME": str(home),
                "USERPROFILE": str(home),
            },
        )
    try:
        context_output = json.loads(result.stdout)
        context_valid = (
            result.returncode == 0
            and set(context_output) == {"additional_context"}
            and isinstance(context_output.get("additional_context"), str)
            and "[CURSOR-SESSION]" in context_output["additional_context"]
        )
    except (KeyError, TypeError, ValueError):
        context_valid = False
    if not context_valid:
        print("::error::generated Cursor SessionStart command must emit documented additional_context")
        return 1

    stop = tracked["hooks"].get("stop", [])
    if len(stop) != 1 or "stop_verify.py" not in stop[0].get("command", ""):
        print("::error::Cursor stop must contain exactly the generated stop_verify registration")
        return 1
    if stop[0].get("loop_limit") != 5:
        print("::error::Cursor stop_verify must cap automatic follow-ups at loop_limit 5")
        return 1

    catch_all = tracked["hooks"]["preToolUse"][0]
    if "matcher" in catch_all:
        print("::error::the catch-all preToolUse hook must omit matcher (Claude matcher *), not invent .*")
        return 1
    shell = [e for e in tracked["hooks"]["preToolUse"] if e.get("matcher") == "Shell"]
    if len(shell) != 5:
        print(f"::error::expected 5 Shell-matched gates, found {len(shell)}")
        return 1

    print(
        "cursor artefacts match emit; PermissionRequest and Notification skipped; SubagentStart "
        "omitted because it cannot inject additional_context; "
        f"{len(commands)} registrations; bounded Stop follow-ups; no plugin-root leak"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
