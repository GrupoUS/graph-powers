#!/usr/bin/env python3
"""Codex native-plugin artefacts are generated from the Claude Code ones. This file proves they match.

Without `.codex-plugin/plugin.json`, Codex falls through to `.claude-plugin/` and loads
`agents/*.md` including `model: haiku` / `model: opus`. Those are Claude families. Codex has
no haiku; the cheap-model fallback is Spark, whose rate-limit bucket is `codex_bengalfox`
("Bengal Fox") — not the user's own Codex window. The generator strips those lines.

    node codex/native-plugin.mjs
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLAUDE_MODEL_LINE = re.compile(
    r"^model:\s*['\"]?(?:haiku|sonnet|opus|fable)['\"]?\s*(?:#.*)?$",
    re.IGNORECASE | re.MULTILINE,
)


def load(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def main() -> int:
    claude_plugin = load(ROOT / ".claude-plugin/plugin.json")
    pkg = load(ROOT / "package.json")
    native_plugin = load(ROOT / ".codex-plugin/plugin.json")
    native_market = load(ROOT / ".codex-plugin/marketplace.json")

    versions = {
        "plugin.json": claude_plugin.get("version"),
        "package.json": pkg.get("version"),
        ".codex-plugin/plugin.json": native_plugin.get("version"),
    }
    if len(set(versions.values())) != 1:
        print(f"::error::version mismatch across manifests: {versions}")
        return 1

    if native_plugin.get("agents") != "./codex/native-agents/":
        print("::error::.codex-plugin/plugin.json must point agents at ./codex/native-agents/")
        return 1

    if native_plugin.get("hooks") != "./hooks/hooks.json":
        print("::error::.codex-plugin/plugin.json must point at hooks/hooks.json, not a second list")
        return 1

    generated = subprocess.run(
        ["node", "codex/native-plugin.mjs", "--dry-run"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        encoding="utf-8",
    )
    # --dry-run does not print JSON. Rebuild in-process via a small node snippet.
    built = subprocess.run(
        [
            "node",
            "--input-type=module",
            "-e",
            """
import { readFileSync } from "node:fs";
import { buildMarketplace, buildNativeAgents, buildPluginManifest } from "./codex/native-plugin.mjs";
const claude = JSON.parse(readFileSync(".claude-plugin/plugin.json", "utf8"));
const market = JSON.parse(readFileSync(".claude-plugin/marketplace.json", "utf8"));
const agents = buildNativeAgents(".");
process.stdout.write(JSON.stringify({
  manifest: buildPluginManifest(claude),
  marketplace: buildMarketplace(market),
  agents,
}));
""",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        encoding="utf-8",
    )
    if built.returncode != 0:
        print(built.stderr)
        print("::error::codex/native-plugin.mjs failed to emit")
        return 1

    data = json.loads(built.stdout)
    if data["manifest"] != native_plugin:
        print("::error::.codex-plugin/plugin.json is stale — run: node codex/native-plugin.mjs")
        return 1
    if data["marketplace"] != native_market:
        print("::error::.codex-plugin/marketplace.json is stale — run: node codex/native-plugin.mjs")
        return 1

    native_dir = ROOT / "codex/native-agents"
    if not native_dir.is_dir():
        print("::error::codex/native-agents/ is missing — run: node codex/native-plugin.mjs")
        return 1

    errors = 0
    expected = set(data["agents"])
    tracked = {p.name for p in native_dir.glob("*.md")}
    if expected != tracked:
        print(f"::error::codex/native-agents file set mismatch: expected {sorted(expected)}, got {sorted(tracked)}")
        errors += 1

    for name, body in data["agents"].items():
        path = native_dir / name
        current = path.read_text(encoding="utf-8") if path.is_file() else ""
        want = body if body.endswith("\n") else body + "\n"
        if current != want:
            print(f"::error::{path.relative_to(ROOT)} is stale — run: node codex/native-plugin.mjs")
            errors += 1
        if CLAUDE_MODEL_LINE.search(current):
            print(f"::error::{path.relative_to(ROOT)} still pins a Claude model family")
            errors += 1

    source_agents = list((ROOT / "agents").glob("*.md"))
    if not source_agents:
        print("::error::no agents/*.md to generate from")
        return 1
    if len(source_agents) != len(data["agents"]):
        print(f"::error::native agent count {len(data['agents'])} != source {len(source_agents)}")
        errors += 1

    if generated.returncode != 0:
        print(generated.stderr)
        errors += 1

    if errors:
        return 1
    print(
        f"codex-native: {len(data['agents'])} agents, no Claude model families, "
        f"manifest {native_plugin.get('version')}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
