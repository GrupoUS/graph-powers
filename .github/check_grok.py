#!/usr/bin/env python3
"""Grok artefacts are generated from the Claude Code ones. This file proves they still match.

Grok reads `hooks/hooks.json` in Claude's nested shape. Inventing `hooks-grok.json` is the
divergence this repository exists to end. The generator is `grok/install.mjs`; this gate
re-runs it and diffs the tracked `.grok-plugin/` manifests.
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
    grok_plugin = load(ROOT / ".grok-plugin/plugin.json")
    grok_market = load(ROOT / ".grok-plugin/marketplace.json")
    pkg = load(ROOT / "package.json")
    claude_hooks = load(ROOT / "hooks/hooks.json")

    versions = {
        "plugin.json": claude_plugin.get("version"),
        "package.json": pkg.get("version"),
        ".grok-plugin/plugin.json": grok_plugin.get("version"),
    }
    if len(set(versions.values())) != 1:
        print(f"::error::version mismatch across manifests: {versions}")
        return 1

    if grok_plugin.get("hooks") != "./hooks/hooks.json":
        print("::error::.grok-plugin/plugin.json must point at hooks/hooks.json, not a second list")
        return 1

    if "hooks-grok" in json.dumps(grok_plugin):
        print("::error::Grok must not invent a second hook file")
        return 1

    if not isinstance(claude_hooks.get("hooks"), dict) or not claude_hooks["hooks"]:
        print("::error::hooks/hooks.json is empty — Grok would load nothing")
        return 1

    generated = subprocess.run(
        [
            "bun",
            "-e",
            """
import { readFileSync } from "node:fs";
import { buildMarketplace, buildPluginManifest } from "./grok/install.mjs";
const claude = JSON.parse(readFileSync(".claude-plugin/plugin.json", "utf8"));
const market = JSON.parse(readFileSync(".claude-plugin/marketplace.json", "utf8"));
process.stdout.write(JSON.stringify({
  manifest: buildPluginManifest(claude),
  marketplace: buildMarketplace(market),
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
        print("::error::grok/install.mjs failed to emit")
        return 1

    data = json.loads(generated.stdout)
    if data["manifest"] != grok_plugin:
        print("::error::.grok-plugin/plugin.json is stale — run: bun grok/install.mjs --emit-only")
        return 1
    if data["marketplace"] != grok_market:
        print("::error::.grok-plugin/marketplace.json is stale — run: bun grok/install.mjs --emit-only")
        return 1

    merge = subprocess.run(
        [
            "bun",
            "-e",
            """
import { mergeGrokConfig } from "./grok/install.mjs";
const seed = `# operator comment\\n[ui]\\ntheme = \\"dark\\"\\npermission_mode = \\"ask\\"\\n\\n[[marketplace.sources]]\\nname = \\"other\\"\\ngit = \\"https://example.invalid/other.git\\"\\n`;
const first = mergeGrokConfig(seed, { autonomous: true, pluginRoot: "/tmp/gp-clone" });
if (!first.next.includes('permission_mode = "always-approve"')) process.exit(2);
if (!first.next.includes('theme = "dark"')) process.exit(3);
if ((first.next.match(/\\[ui\\]/g) || []).length !== 1) process.exit(4);
if (!first.next.includes('name = "other"')) process.exit(5);
const second = mergeGrokConfig(first.next, { autonomous: true, pluginRoot: "/tmp/gp-clone" });
if (second.changed.length) process.exit(6);
const guarded = mergeGrokConfig(seed, { autonomous: false, pluginRoot: "/tmp/gp-clone" });
if (!guarded.next.includes('permission_mode = "ask"')) process.exit(7);
if (guarded.next.includes('permission_mode = "always-approve"')) process.exit(8);
if (!guarded.next.includes('enabled = ["graph-powers"]')) process.exit(9);
if (!guarded.next.includes('paths = ["/tmp/gp-clone"]')) process.exit(10);
if (!guarded.next.includes('name = "graph-powers"')) process.exit(11);
if (!guarded.next.includes('git = "https://github.com/GrupoUS/graph-powers.git"')) process.exit(12);
if (guarded.changed.join(",") !== "plugins.enabled,plugins.paths,marketplace.sources") process.exit(13);
const noPath = mergeGrokConfig("", { autonomous: true, pluginRoot: null });
if (noPath.next.includes("plugins.paths") || noPath.next.includes("paths =")) process.exit(14);
const stripped = mergeGrokConfig(first.next, { autonomous: true, pluginRoot: "/tmp/gp-clone", forgetClone: true });
if (stripped.next.includes("/tmp/gp-clone")) process.exit(15);
process.stdout.write("ok");
""",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        encoding="utf-8",
    )
    if merge.returncode != 0 or merge.stdout.strip() != "ok":
        print(merge.stdout)
        print(merge.stderr)
        print(f"::error::mergeGrokConfig failed (exit {merge.returncode})")
        return 1

    print(
        "grok artefacts match emit; hooks path is hooks.json; "
        "TOML merge is additive and idempotent; guarded preserves approval posture and wires discovery"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
