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


def check_toml_edit_boundary() -> None:
    """Unsupported structure must never be mistaken for editable table lines."""
    rejected = {
        "multiline-basic": '[plugins]\nnote = """\npaths = ["/operator/fake"]\n"""\n',
        "multiline-literal": "[plugins]\nnote = '''\npaths = [\"/operator/fake\"]\n'''\n",
        "multiline-fake-header": 'note = """\n[plugins]\npaths = ["/operator/fake"]\n"""\n',
        "quoted-leaf": '[plugins]\n"paths" = ["/operator"]\n',
        "quoted-escaped-leaf": '[plugins]\n"\\u0070aths" = ["/operator"]\n',
        "nested-leaf": '[plugins.paths]\noperator = true\n',
        "multiline-scalar-target": '[subagents]\nenabled = [\ntrue\n]\n',
        "marketplace-inline-sources": '[marketplace]\nsources = [{ name = "other" }]\n',
        "marketplace-table-sources": '[marketplace.sources]\nname = "other"\n',
        "unsupported-array-value": '[plugins]\npaths = ["/operator", 1]\n',
        "operator-disabled": '[plugins]\ndisabled = ["graph-powers"]\n',
    }
    for namespace in ("ui", "features", "subagents", "plugins", "marketplace"):
        rejected.update({
            f"{namespace}-dotted": f'{namespace}.custom = true\n',
            f"{namespace}-spaced-dotted": f'{namespace} . custom = true\n',
            f"{namespace}-quoted-dotted": f'"{namespace}" . custom = true\n',
            f"{namespace}-inline": f'{namespace} = {{ custom = true }}\n',
            f"{namespace}-literal-inline": f"'{namespace}' = {{ custom = true }}\n",
            f"{namespace}-quoted-header": f'["{namespace}"]\ncustom = true\n',
            f"{namespace}-spaced-header": f'[ {namespace} ]\ncustom = true\n',
            f"{namespace}-array-table": f'[[{namespace}]]\ncustom = true\n',
        })
    accepted = {
        "comments-and-literals": '# triple quotes """ and \'\'\' are comments\n'
        'note = \'literal """ text\'\n[plugins]\npaths = ["/operator"] # keep\n',
        "windows-crlf-tabs": '[ui]\r\npermission_mode = "ask"\t# keep\r\n'
        "[plugins]\r\npaths = ['C:\\operator', # keep\r\n\t\"/other\",]\t\r\n",
        "unrelated-inline": 'custom = { nested = { value = "[plugins]" } }\n'
        '[other.deep]\nvalue = ["plugins.paths=1", "a#b"]\n',
        "subagent-routing-implicit-parent": '[subagents.models]\ndebugger = "operator-model"\n'
        '[subagents.toggle]\nlibrarian = false\n',
        "subagent-routing-explicit-parent": '[subagents]\nenabled = false\n'
        '[subagents.models]\nlibrarian = "operator-fast"\n'
        '[subagents.toggle]\ndebugger = true\nlibrarian = false\n',
    }
    fixtures = [{"name": name, "seed": seed, "reject": True} for name, seed in rejected.items()]
    fixtures.extend({"name": name, "seed": seed, "reject": False} for name, seed in accepted.items())
    result = subprocess.run(
        ["bun", "-e", r'''
import { mkdtempSync, readFileSync, readdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { install, mergeGrokConfig } from "./grok/install.mjs";
const fixtures = JSON.parse(readFileSync(0, "utf8"));
const home = mkdtempSync(join(tmpdir(), "gp-grok-toml-"));
const configFile = join(home, "config.toml");
const pluginRoot = join(home, "plugin");
process.env.GROK_HOME = home;
const results = [];
try {
  for (const fixture of fixtures) {
    const before = Bun.TOML.parse(fixture.seed);
    for (const autonomous of [false, true]) {
      const options = { autonomous, pluginRoot };
      const first = mergeGrokConfig(fixture.seed, options);
      const second = mergeGrokConfig(first.next, options);
      const bytes = Buffer.from(fixture.seed);
      writeFileSync(configFile, bytes);
      let refusals = 0;
      let repeatedWrites = [];
      for (let attempt = 0; attempt < 2; attempt += 1) {
        try {
          repeatedWrites = install({ ...options, verified: true, emit: fixture.reject }).written;
        } catch { refusals += 1; }
      }
      results.push({
        name: fixture.name, autonomous, first, second, refusals, repeatedWrites,
        before, after: fixture.reject ? null : Bun.TOML.parse(first.next),
        unchanged: readFileSync(configFile).equals(bytes),
        entries: readdirSync(home),
      });
    }
  }
} finally {
  rmSync(home, { recursive: true, force: true });
}
process.stdout.write(JSON.stringify(results));
'''],
        input=json.dumps(fixtures), cwd=ROOT, capture_output=True, encoding="utf-8", check=False,
    )
    assert result.returncode == 0, "TOML edit boundary harness failed"
    by_name = {fixture["name"]: fixture for fixture in fixtures}
    for outcome in json.loads(result.stdout):
        fixture = by_name[outcome["name"]]
        label = f'{fixture["name"]} autonomous={outcome["autonomous"]}'
        first = outcome["first"]
        if fixture["reject"]:
            assert first["conflicts"], f"{label}: unsupported structure accepted"
            assert first["next"] == fixture["seed"] and not first["changed"], f"{label}: merge changed input"
            assert outcome["second"] == first, f"{label}: repeated refusal differs"
            assert outcome["refusals"] == 2 and outcome["unchanged"], f"{label}: install changed input"
            assert outcome["entries"] == ["config.toml"], f"{label}: install emitted before refusal"
        else:
            assert not first["conflicts"] and not outcome["refusals"], f"{label}: supported format rejected"
            assert not outcome["second"]["changed"], f"{label}: merge is not idempotent"
            assert not outcome["repeatedWrites"], f"{label}: repeated install wrote config"
            before = outcome["before"]
            after = outcome["after"]
            assert after["plugins"]["paths"][:-1] == before.get("plugins", {}).get("paths", [])
            for key in ("note", "custom", "other"):
                assert after.get(key) == before.get(key), f"{label}: unrelated value changed"
            for key in ("models", "toggle"):
                assert after["subagents"].get(key) == before.get("subagents", {}).get(key), (
                    f"{label}: subagent routing changed"
                )


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

    stop_commands = [
        hook.get("command", "")
        for group in claude_hooks["hooks"].get("Stop", [])
        for hook in group.get("hooks", [])
    ]
    if len(stop_commands) != 1 or "stop_verify.py" not in stop_commands[0]:
        print("::error::the shared Grok manifest lost the stop_verify lifecycle registration")
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
import { existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { install, mergeGrokConfig } from "./grok/install.mjs";
const seed = `# operator comment\\n[ui]\\ntheme = \\"dark\\"\\npermission_mode = \\"ask\\"\\n\\n[subagents]\\nenabled = false\\n\\n[[marketplace.sources]]\\nname = \\"other\\"\\ngit = \\"https://example.invalid/other.git\\"\\n`;
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
if (!guarded.next.includes("[subagents]\\nenabled = true")) process.exit(13);
if (guarded.changed.join(",") !== "subagents.enabled,plugins.enabled,plugins.paths,marketplace.sources") process.exit(14);
const guardedSecond = mergeGrokConfig(guarded.next, { autonomous: false, pluginRoot: "/tmp/gp-clone" });
if (guardedSecond.changed.length) process.exit(15);
const noPath = mergeGrokConfig("", { autonomous: true, pluginRoot: null });
if (noPath.next.includes("plugins.paths") || noPath.next.includes("paths =")) process.exit(16);
const stripped = mergeGrokConfig(first.next, { autonomous: true, pluginRoot: "/tmp/gp-clone", forgetClone: true });
if (stripped.next.includes("/tmp/gp-clone")) process.exit(17);

const installHome = mkdtempSync(join(tmpdir(), "gp-grok-home-"));
const invalidRoot = join(installHome, "missing-plugin");
const configFile = join(installHome, "config.toml");
const previousHome = process.env.GROK_HOME;
process.env.GROK_HOME = installHome;
let failed = false;
try {
  install({ pluginRoot: invalidRoot, autonomous: false, verified: false });
} catch {
  failed = true;
}
if (!failed) process.exit(18);
if (existsSync(configFile)) process.exit(19);
const originalConfig = "# operator config\\n[ui]\\ntheme = \\"dark\\"\\n";
writeFileSync(configFile, originalConfig);
failed = false;
try {
  install({ pluginRoot: join(installHome, "another-missing-plugin"), autonomous: false, verified: false });
} catch {
  failed = true;
}
if (!failed) process.exit(20);
if (readFileSync(configFile, "utf8") !== originalConfig) process.exit(21);

const matching = mergeGrokConfig("", { autonomous: false, pluginRoot: invalidRoot }).next;
writeFileSync(configFile, matching);
const logs = [];
install({ pluginRoot: invalidRoot, autonomous: false, verified: true, log: (message) => logs.push(message) });
if (!logs.some((message) => message.includes("guarded posture"))) process.exit(22);
if (logs.some((message) => message.includes("autonomous posture"))) process.exit(23);

const commentedTable = `# operator comment\\n  [ui] # retained\\n  theme = \\"dark\\" # retained\\n\\n[plugins]\\npaths = [\\"C:\\\\\\\\work\\\\\\\\graph-powers\\"] # retained\\n`;
const windowsRoot = String.raw`C:\\work\\graph-powers`;
const formatted = mergeGrokConfig(commentedTable, { autonomous: true, pluginRoot: windowsRoot });
if ((formatted.next.match(/^\\s*\\[ui\\]/gm) || []).length !== 1) process.exit(24);
if (!formatted.next.includes("# retained")) process.exit(25);
const crlfMode = mergeGrokConfig(`[ui]\\r\\npermission_mode = \\"ask\\" # retained\\r\\n`, { autonomous: true });
if (!crlfMode.next.includes('permission_mode = "always-approve" # retained')) process.exit(26);
if (!crlfMode.next.includes("\\r\\n")) process.exit(27);
const tabWhitespace = mergeGrokConfig(`[plugins]\\r\\npaths = [\\"x\\"]\\t\\r\\n`, { autonomous: true, pluginRoot: "x" });
if (tabWhitespace.conflicts.length || !tabWhitespace.next.includes(`paths = ["x"]\\t\\r\\n`)) process.exit(28);
const tabComment = mergeGrokConfig(`[ui]\\npermission_mode = \\"ask\\"\\t# keep\\n`, { autonomous: true });
if (!tabComment.next.includes('permission_mode = "always-approve"\\t# keep')) process.exit(29);
if (mergeGrokConfig(tabWhitespace.next, { autonomous: true, pluginRoot: "x" }).changed.length) process.exit(30);
if ((formatted.next.match(/graph-powers/g) || []).length !== 4) process.exit(26);
if (mergeGrokConfig(formatted.next, { autonomous: true, pluginRoot: windowsRoot }).changed.length) process.exit(27);

const commentedArray = `[plugins]\\npaths = [\\"/operator/path\\", # \\"]\\" stays a comment\\n  \\"/second/path\\"]\\n`;
const commentMerge = mergeGrokConfig(commentedArray, { autonomous: false, pluginRoot: "/operator/path" });
if (commentMerge.conflicts.length || (commentMerge.next.match(/operator\\/path/g) || []).length !== 1) process.exit(28);
const unsafeArray = mergeGrokConfig(`[plugins]\\npaths = [\\"/safe\\", 1]\\n`, { autonomous: true, pluginRoot: "/tmp/gp-clone" });
if (!unsafeArray.conflicts?.includes("plugins.paths cannot be safely read")) process.exit(29);

const disabled = `# operator decision\\n[plugins]\\ndisabled = [\\"graph-powers\\"]\\n`;
const conflict = mergeGrokConfig(disabled, { autonomous: true, pluginRoot: "/tmp/gp-clone" });
if (!conflict.conflicts?.includes("plugins.disabled contains graph-powers")) process.exit(30);
writeFileSync(configFile, disabled);
failed = false;
try {
  install({ pluginRoot: invalidRoot, autonomous: true, verified: true });
} catch {
  failed = true;
}
if (!failed) process.exit(31);
if (readFileSync(configFile, "utf8") !== disabled) process.exit(32);
if (previousHome === undefined) delete process.env.GROK_HOME;
else process.env.GROK_HOME = previousHome;
rmSync(installHome, { recursive: true, force: true });
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

    check_toml_edit_boundary()
    print(
        "grok artefacts match emit; hooks path is hooks.json; "
        "Stop wiring present (passive event); TOML merge is additive and idempotent; "
        "guarded preserves approval posture and wires discovery"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
