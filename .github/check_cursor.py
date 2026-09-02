#!/usr/bin/env python3
"""Cursor artefacts are generated from the Claude Code ones. This file proves they still match.

A hand-edited `hooks/hooks-cursor.json` is the divergence this repository exists to end, now
inside a single tree. The generator is `cursor/install.mjs`; this gate re-runs it and diffs.
"""

from __future__ import annotations

import json
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CLIENT_MARKER = "--graph-powers-client cursor"
CLIENT_MARKER_PREFIX = "--graph-powers-client"
CLIENT_MARKER_TOKENS = CLIENT_MARKER.split()
STOP_SCRIPT = "hooks/stop_verify.py"


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


def run_negative_generator_probes() -> bool:
    probe = subprocess.run(
        [
            "bun",
            "-e",
            r'''
import { buildCursorHooks } from "./cursor/install.mjs";
const cases = [
  ["malicious-marker", "python3 -X utf8 -c \"pass\" \"hooks/stop_verify.py\" --graph-powers-client cursor-malicious"],
  ["fake-stop", "echo stop_verify.py"],
];
const rejected = cases.map(([name, command]) => {
  try {
    buildCursorHooks({ hooks: { Stop: [{ hooks: [{ type: "command", command }] }] } });
    return { name, rejected: false };
  } catch {
    return { name, rejected: true };
  }
});
process.stdout.write(JSON.stringify(rejected));
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
    rejected = json.loads(probe.stdout)
    if {case.get("name") for case in rejected} != {"malicious-marker", "fake-stop"} or not all(
        case.get("rejected") is True for case in rejected
    ):
        print("::error::Cursor generator must reject malicious marker and fake Stop commands")
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
    if any(tokens is None for tokens in tokenized) or marker_count != 1 or marker_pair_count != 1:
        print(
            "::error::Cursor client marker must occur exactly once, with the exact cursor value"
        )
        return 1
    if len(tracked_stop) != 1 or not is_cursor_stop_command(tracked_stop[0]["command"]):
        print("::error::Cursor client marker must only appear on the generated stop verifier")
        return 1
    stop_command = tracked_stop[0]["command"]
    if any(
        CLIENT_MARKER_TOKENS[0] in tokens
        for command, tokens in zip(tracked_commands, tokenized, strict=True)
        if command != stop_command and tokens is not None
    ):
        print("::error::Cursor client marker must only appear on the generated stop verifier")
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
        print(f"::error::unexpected skipped Cursor events: {sorted(skipped)}")
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
        "cursor artefacts match emit; PermissionRequest, Notification and SubagentStart skipped; "
        f"{len(commands)} registrations; bounded Stop follow-ups; no plugin-root leak"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
