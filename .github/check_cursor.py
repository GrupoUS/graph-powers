#!/usr/bin/env python3
"""Cursor artefacts are generated from the Claude Code ones. This file proves they still match.

A hand-edited `hooks/hooks-cursor.json` is the divergence this repository exists to end, now
inside a single tree. The generator is `cursor/install.mjs`; this gate re-runs it and diffs.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def main() -> int:
    claude_plugin = load(ROOT / ".claude-plugin/plugin.json")
    cursor_plugin = load(ROOT / ".cursor-plugin/plugin.json")
    pkg = load(ROOT / "package.json")
    tracked = load(ROOT / "hooks/hooks-cursor.json")

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
            "node",
            "--input-type=module",
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
        print("::error::hooks/hooks-cursor.json is stale — run: node cursor/install.mjs --emit-only")
        return 1

    # Keywords and description can drift in the tracked manifest independently of the hook
    # list; the generator is still the owner of both, so the whole file has to match.
    if data["manifest"] != cursor_plugin:
        print("::error::.cursor-plugin/plugin.json is stale — run: node cursor/install.mjs --emit-only")
        return 1

    skipped = set(data["skipped"])
    if skipped != {"PermissionRequest", "Notification"}:
        print(f"::error::unexpected skipped Cursor events: {sorted(skipped)}")
        return 1

    commands = [
        entry["command"]
        for entries in tracked["hooks"].values()
        for entry in entries
    ]
    if len(commands) != 11:
        print(f"::error::expected 11 Cursor registrations (Claude's 14 minus PermissionRequest and Notification), found {len(commands)}")
        return 1
    joined = "\n".join(commands)
    if "tool_approver.py" in joined or "notify.py" in joined:
        print("::error::a skipped Claude event leaked into the Cursor hook list")
        return 1
    if "smart_bash_approver.py" not in joined:
        print("::error::smart_bash_approver is missing from Cursor preToolUse")
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
        "cursor artefacts match emit; PermissionRequest and Notification skipped; "
        "11 registrations; no plugin-root leak"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
