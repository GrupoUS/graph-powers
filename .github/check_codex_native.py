#!/usr/bin/env python3
"""Codex native companion roles are generated from the Claude Code ones and match the clone route.

Without `.codex-plugin/plugin.json`, Codex falls through to `.claude-plugin/` and loads
`agents/*.md` including `model: haiku` / `model: opus`. Those are Claude families. Codex has
no haiku; the cheap-model fallback is Spark, whose rate-limit bucket is `codex_bengalfox`
("Bengal Fox") — not the user's own Codex window. The generator replaces those lines through the
same semantic model policy as the clone TOML route.

    bun codex/native-plugin.mjs
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_POLICY = {
    "evaluator": ("judge", "gpt-5.6-sol", "max"),
    "security-reviewer": ("judge", "gpt-5.6-sol", "max"),
    "skill-improver": ("judge", "gpt-5.6-sol", "max"),
    "ui-ux-designer": ("judge", "gpt-5.6-sol", "max"),
    "project-planner": ("architect", "gpt-5.6-sol", "max"),
    "debugger": ("executor", "gpt-5.6-terra", "high"),
    "frontend-specialist": ("executor", "gpt-5.6-terra", "high"),
    "mobile-developer": ("executor", "gpt-5.6-terra", "high"),
    "performance-optimizer": ("executor", "gpt-5.6-terra", "high"),
    "verification": ("verifier", "gpt-5.6-terra", "high"),
    "explorer": ("scout", "gpt-5.6-luna", "medium"),
    "librarian": ("scout", "gpt-5.6-luna", "medium"),
}
EXPECTED_TOP_LEVEL_PROFILES = {
    "native-economic": ["gpt-5.6-luna", "low"],
    "native-ultra": ["gpt-5.6-sol", "ultra"],
}
READ_ONLY_AGENTS = {
    "evaluator", "security-reviewer", "skill-improver", "ui-ux-designer", "explorer",
    "librarian", "verification",
}


def load(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def standalone_command_refs(text: str, command_names: list[str]) -> list[str]:
    """Find slash-command tokens without confusing paths, URLs or Markdown destinations."""
    alternatives = "|".join(map(re.escape, command_names))
    pattern = re.compile(
        rf"(^|[\s`'\"(\[>|])/(?P<name>{alternatives})(?=$|[\s`'\"),\]:;!?—–])",
        re.MULTILINE,
    )
    refs: list[str] = []
    for match in pattern.finditer(text):
        if match.group(1) == "(" and match.start() > 0 and text[match.start() - 1] == "]":
            continue
        refs.append(match.group("name"))
    return refs


def check_command_ref_rewrite(command_names: list[str]) -> None:
    cases = {
        "plain": "/verify quick",
        "backtick": "run `/verify` now",
        "parenthesized": "run (/verify) now",
        "extension": "/verify.md",
        "child_path": "/verify/path",
        "url": "https://example.test/verify",
        "query": "https://example.test/?next=/verify",
        "markdown_link": "[verification](/verify)",
        "windows_forward": "C:/verify",
        "windows_back": r"C:\verify",
    }
    expected = {
        **cases,
        "plain": "$graph-powers-verify quick",
        "backtick": "run `$graph-powers-verify` now",
        "parenthesized": "run ($graph-powers-verify) now",
    }
    rendered = subprocess.run(
        [
            "bun",
            "-e",
            """
import { rewriteCodexCommandRefs } from "./codex/install.mjs";
const cases = JSON.parse(process.env.GRAPH_POWERS_REWRITE_CASES);
const names = JSON.parse(process.env.GRAPH_POWERS_COMMAND_NAMES);
process.stdout.write(JSON.stringify(Object.fromEntries(
  Object.entries(cases).map(([key, value]) => [key, rewriteCodexCommandRefs(value, names)]),
)));
""",
        ],
        cwd=ROOT,
        env={
            **os.environ,
            "GRAPH_POWERS_REWRITE_CASES": json.dumps(cases),
            "GRAPH_POWERS_COMMAND_NAMES": json.dumps(command_names),
        },
        check=False,
        capture_output=True,
        encoding="utf-8",
    )
    if rendered.returncode != 0:
        raise AssertionError(f"Codex command rewrite probe failed: {rendered.stderr.strip()}")
    actual = json.loads(rendered.stdout)
    if actual != expected:
        raise AssertionError(f"Codex command rewrite changed a path/URL or missed a token: {actual}")


def check_codex_command_skills() -> None:
    """Prove both native-plugin and clone routes expose usable command skills."""
    command_names = sorted(path.stem for path in (ROOT / "commands").glob("*.md"))
    check_command_ref_rewrite(command_names)

    native_root = ROOT / "codex/native-command-skills"
    native_paths = sorted(path.relative_to(native_root).as_posix() for path in native_root.rglob("SKILL.md"))
    expected_native_paths = [f"{name}/SKILL.md" for name in command_names]
    if native_paths != expected_native_paths:
        raise AssertionError(
            f"native command skills are stale: expected {expected_native_paths}, got {native_paths}"
        )
    for name in command_names:
        path = native_root / name / "SKILL.md"
        body = path.read_text(encoding="utf-8")
        if f"name: {name}\n" not in body or f"$graph-powers:{name}" not in body:
            raise AssertionError(f"{path.relative_to(ROOT)} lacks its native Codex invocation")
        if f"${{CLAUDE_PLUGIN_ROOT}}/commands/{name}.md" not in body:
            raise AssertionError(f"{path.relative_to(ROOT)} does not route to its source command")
        if "$ARGUMENTS" in body:
            raise AssertionError(f"{path.relative_to(ROOT)} reintroduced rejected command templates")

    with TemporaryDirectory(prefix="graph-powers-command-skills-") as raw:
        fixture = Path(raw)
        generated = subprocess.run(
            [
                "bun",
                "-e",
                """
import { install } from "./codex/install.mjs";
install({
  projectDir: process.env.GRAPH_POWERS_COMMAND_FIXTURE,
  pluginRoot: process.cwd(),
  scope: "project",
  log: () => {},
});
""",
            ],
            cwd=ROOT,
            env={**os.environ, "GRAPH_POWERS_COMMAND_FIXTURE": str(fixture)},
            check=False,
            capture_output=True,
            encoding="utf-8",
        )
        if generated.returncode != 0:
            raise AssertionError(
                f"Codex command-skill fixture failed: {generated.stderr.strip()}"
            )

        for name in command_names:
            path = fixture / ".agents/skills" / f"graph-powers-{name}" / "SKILL.md"
            if not path.is_file():
                raise AssertionError(f"missing generated Codex command skill: {path}")
            body = path.read_text(encoding="utf-8")
            stale = standalone_command_refs(body, command_names)
            if stale:
                raise AssertionError(
                    f"{path.relative_to(fixture)} retains Claude slash command references: {stale[:3]}"
                )
            expected = f"$graph-powers-{name}"
            if expected not in body:
                raise AssertionError(
                    f"{path.relative_to(fixture)} does not advertise the Codex invocation {expected}"
                )
            if "/skills" not in body:
                raise AssertionError(
                    f"{path.relative_to(fixture)} does not advertise the Codex /skills picker"
                )
        debug_body = (
            fixture / ".agents/skills/graph-powers-debug/SKILL.md"
        ).read_text(encoding="utf-8")
        if "/commands/pr-review.md" not in debug_body or "$graph-powers-pr-review.md" in debug_body:
            raise AssertionError("Codex command rewrite corrupted a command-document path")


def assert_native_policy(name: str, data: dict, path: Path) -> None:
    _profile, expected_model, expected_effort = EXPECTED_POLICY[name]
    model = data.get("model")
    effort = data.get("model_reasoning_effort")
    if model != expected_model:
        raise AssertionError(
            f"{path.relative_to(ROOT)}: semantic policy mismatch for {name}: "
            f"expected model {expected_model!r}, got {model!r}"
        )
    if effort != expected_effort:
        raise AssertionError(
            f"{path.relative_to(ROOT)}: semantic policy mismatch for {name}: "
            f"expected effort {expected_effort!r}, got {effort!r}"
        )
    if effort == "ultra":
        raise AssertionError(f"{path.relative_to(ROOT)}: Ultra must never be emitted for {name}")
    assert "sandbox_mode" not in data, (
        f"{path.relative_to(ROOT)}: unsupported sandbox key would fake a runtime boundary"
    )
    instructions = data.get("developer_instructions") or ""
    assert instructions, f"{path.relative_to(ROOT)}: missing developer instructions"
    read_only_notice = "Graph Powers read-only intent:" in instructions
    assert read_only_notice == (name in READ_ONLY_AGENTS), (
        f"{path.relative_to(ROOT)}: read-only intent does not match source authority for {name}"
    )
    if name == "evaluator":
        assert "Graph Powers leaf intent:" in instructions, (
            f"{path.relative_to(ROOT)}: evaluator lost the explicit advisory leaf contract"
        )


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

    if "agents" in native_plugin:
        print("::error::.codex-plugin/plugin.json must not claim unsupported agent-role discovery")
        return 1

    if native_plugin.get("hooks") != "./hooks/hooks.json":
        print("::error::.codex-plugin/plugin.json must point at hooks/hooks.json, not a second list")
        return 1
    if native_plugin.get("skills") != ["./skills/", "./codex/native-command-skills/"]:
        print("::error::.codex-plugin/plugin.json must expose canonical and command skill roots")
        return 1
    if "commands" in native_plugin:
        print("::error::.codex-plugin/plugin.json must not trigger Codex's lossy command migration")
        return 1

    generated = subprocess.run(
        ["bun", "codex/native-plugin.mjs", "--dry-run"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        encoding="utf-8",
    )
    with TemporaryDirectory(prefix="graph-powers-native-ultra-") as tmp:
        companion_dir = Path(tmp) / "agents"
        companion_command = [
            "bun",
            "codex/native-plugin.mjs",
            "--out",
            str(companion_dir),
        ]
        first_companion = subprocess.run(
            companion_command,
            cwd=ROOT,
            check=False,
            capture_output=True,
            encoding="utf-8",
        )
        companion_files = {
            path.name: path.read_text(encoding="utf-8")
            for path in companion_dir.glob("*.toml")
        }
        if first_companion.returncode != 0 or set(companion_files) != {
            f"{name}.toml" for name in EXPECTED_POLICY
        }:
            print(first_companion.stderr)
            print("::error::native companion role directory was not emitted")
            return 1
        leaked = [name for name, body in companion_files.items() if "CLAUDE_PLUGIN_ROOT" in body]
        if leaked:
            print(f"::error::native companion roles retain Claude-only paths: {leaked}")
            return 1
        missing_root = [
            name for name, body in companion_files.items()
            if str(ROOT / "references") not in body
        ]
        if missing_root:
            print(f"::error::native companion roles did not resolve plugin references: {missing_root}")
            return 1
        second_companion = subprocess.run(
            companion_command,
            cwd=ROOT,
            check=False,
            capture_output=True,
            encoding="utf-8",
        )
        regenerated_companion = {
            path.name: path.read_text(encoding="utf-8")
            for path in companion_dir.glob("*.toml")
        }
        if second_companion.returncode != 0 or companion_files != regenerated_companion:
            print(second_companion.stderr)
            print("::error::native companion role regeneration is not idempotent")
            return 1

        ultra_command = [
            "bun",
            "codex/native-plugin.mjs",
            "--top-level-profile",
            "native-ultra",
            "--out",
            tmp,
        ]
        first_ultra = subprocess.run(
            ultra_command,
            cwd=ROOT,
            check=False,
            capture_output=True,
            encoding="utf-8",
        )
        ultra_path = Path(tmp) / "native-ultra.config.toml"
        if first_ultra.returncode != 0 or not ultra_path.is_file():
            print(first_ultra.stderr)
            print("::error::native-ultra top-level profile was not emitted")
            return 1
        first_contents = ultra_path.read_text(encoding="utf-8")
        second_ultra = subprocess.run(
            ultra_command,
            cwd=ROOT,
            check=False,
            capture_output=True,
            encoding="utf-8",
        )
        second_contents = ultra_path.read_text(encoding="utf-8")
        if second_ultra.returncode != 0 or first_contents != second_contents:
            print(second_ultra.stderr)
            print("::error::native-ultra top-level profile regeneration is not idempotent")
            return 1
        ultra_config = tomllib.loads(first_contents)
        if ultra_config != {
            "model": "gpt-5.6-sol",
            "model_reasoning_effort": "ultra",
        }:
            print(f"::error::unexpected native-ultra profile: {ultra_config}")
            return 1

        economic_command = [
            "bun",
            "codex/native-plugin.mjs",
            "--top-level-profile",
            "native-economic",
            "--out",
            tmp,
        ]
        economic = subprocess.run(
            economic_command,
            cwd=ROOT,
            check=False,
            capture_output=True,
            encoding="utf-8",
        )
        economic_path = Path(tmp) / "native-economic.config.toml"
        if economic.returncode != 0 or not economic_path.is_file():
            print(economic.stderr)
            print("::error::native-economic top-level profile was not emitted")
            return 1
        if tomllib.loads(economic_path.read_text(encoding="utf-8")) != {
            "model": "gpt-5.6-luna",
            "model_reasoning_effort": "low",
        }:
            print("::error::unexpected native-economic profile")
            return 1
    # --dry-run does not print JSON. Rebuild in-process via a small Bun snippet.
    built = subprocess.run(
        [
            "bun",
            "-e",
            """
import { readFileSync } from "node:fs";
import { agentToToml } from "./codex/install.mjs";
import {
  buildMarketplace,
  buildNativeAgents,
  buildNativeCommandSkills,
  buildPluginManifest,
} from "./codex/native-plugin.mjs";
import { resolveCodexAgentPolicy, resolveCodexTopLevelProfile } from "./codex/model-policy.mjs";
const claude = JSON.parse(readFileSync(".claude-plugin/plugin.json", "utf8"));
const market = JSON.parse(readFileSync(".claude-plugin/marketplace.json", "utf8"));
const agents = buildNativeAgents(".");
const cloneAgents = Object.fromEntries(Object.keys(agents).map((file) => [
  file,
  agentToToml(readFileSync(`agents/${file.replace(/\\.toml$/, ".md")}`, "utf8")),
]));
const paritySettings = {
  agents: { evaluator: { model: "CODEX_SECRET_OVERRIDE_SENTINEL", reasoningEffort: "ultra" } },
};
const nativeWarnings = [];
buildNativeAgents(".", paritySettings, (warning) => nativeWarnings.push(warning));
const cloneWarnings = [];
for (const file of Object.keys(agents)) {
  agentToToml(readFileSync(`agents/${file.replace(/\\.toml$/, ".md")}`, "utf8"), paritySettings,
    (warning) => cloneWarnings.push(warning));
}
const topLevelProfiles = Object.fromEntries(["native-economic", "native-ultra"].map((name) => {
  const profile = resolveCodexTopLevelProfile(name);
  return [name, [profile.model, profile.reasoningEffort]];
}));
const secretSentinel = "CODEX_SECRET_OVERRIDE_SENTINEL";
const warningResult = resolveCodexAgentPolicy("evaluator", {
  agents: { evaluator: { model: secretSentinel, reasoningEffort: "ultra" } },
}, { model: "opus", effort: "xhigh" });
let errorOutput = "";
try {
  resolveCodexAgentPolicy("evaluator", {
    agents: { evaluator: { model: `claude-${secretSentinel}` } },
  }, { model: "opus", effort: "xhigh" });
} catch (error) {
  errorOutput = String(error);
}
process.stdout.write(JSON.stringify({
  manifest: buildPluginManifest(claude),
  marketplace: buildMarketplace(market),
  agents,
  commandSkills: buildNativeCommandSkills("."),
  cloneAgents,
  topLevelProfiles,
  warningCategories: [...new Set(warningResult.warnings)].sort(),
  warningOutput: warningResult.warnings.join("|"),
  errorOutput,
  nativeWarnings,
  cloneWarnings,
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

    try:
        check_codex_command_skills()
    except (AssertionError, OSError) as exc:
        print(f"::error::{exc}")
        return 1

    data = json.loads(built.stdout)
    if data["manifest"] != native_plugin:
        print("::error::.codex-plugin/plugin.json is stale — run: bun codex/native-plugin.mjs")
        return 1
    if data["marketplace"] != native_market:
        print("::error::.codex-plugin/marketplace.json is stale — run: bun codex/native-plugin.mjs")
        return 1
    native_command_root = ROOT / "codex/native-command-skills"
    native_command_skills = {
        path.relative_to(native_command_root).as_posix(): path.read_text(encoding="utf-8")
        for path in native_command_root.rglob("SKILL.md")
    }
    if data.get("commandSkills") != native_command_skills:
        print("::error::codex/native-command-skills is stale — run: bun codex/native-plugin.mjs")
        return 1

    if data.get("topLevelProfiles") != EXPECTED_TOP_LEVEL_PROFILES:
        print(f"::error::top-level profile policy mismatch: {data.get('topLevelProfiles')}")
        return 1
    secret_sentinel = "CODEX_SECRET_OVERRIDE_SENTINEL"
    secret_output = "".join(
        str(data.get(key, ""))
        for key in ("warningOutput", "errorOutput", "nativeWarnings", "cloneWarnings")
    )
    if secret_sentinel in secret_output:
        print("::error::override diagnostics leaked a secret sentinel")
        return 1
    if data.get("nativeWarnings") != data.get("cloneWarnings"):
        print("::error::native/clone override diagnostics differ")
        return 1
    if data.get("warningCategories") != ["model-override-unverified", "top-level-only-effort"]:
        print(f"::error::unexpected warning categories: {data.get('warningCategories')}")
        return 1

    native_dir = ROOT / "codex/native-agents"
    if not native_dir.is_dir():
        print("::error::codex/native-agents/ is missing — run: bun codex/native-plugin.mjs")
        return 1

    errors = 0
    expected = set(data["agents"])
    tracked = {
        p.name for p in native_dir.iterdir()
        if p.is_file() and p.suffix.lower() in {".md", ".toml"}
    }
    if expected != tracked:
        print(f"::error::codex/native-agents file set mismatch: expected {sorted(expected)}, got {sorted(tracked)}")
        errors += 1

    for name, body in data["agents"].items():
        path = native_dir / name
        agent_name = name.removesuffix(".toml")
        current = path.read_text(encoding="utf-8") if path.is_file() else ""
        want = body if body.endswith("\n") else body + "\n"
        if current != want:
            print(f"::error::{path.relative_to(ROOT)} is stale — run: bun codex/native-plugin.mjs")
            errors += 1
        try:
            expected_profile = EXPECTED_POLICY[agent_name][0]
            if f"# Codex policy: profile={expected_profile};" not in current:
                raise AssertionError(
                    f"{path.relative_to(ROOT)}: missing policy-source trace for {expected_profile}"
                )
            native = tomllib.loads(current)
            assert_native_policy(agent_name, native, path)
            clone = tomllib.loads(data["cloneAgents"][name])
            native_profile, native_model, native_effort = EXPECTED_POLICY[agent_name]
            if clone.get("model") != native_model or clone.get("model_reasoning_effort") != native_effort:
                raise AssertionError(
                    f"{path.relative_to(ROOT)}: native-companion/clone mismatch for {agent_name} "
                    f"({native_profile}): native={native_model}/{native_effort}, "
                    f"clone={clone.get('model')}/{clone.get('model_reasoning_effort')}"
                )
            native_read_only = "Graph Powers read-only intent:" in (native.get("developer_instructions") or "")
            clone_read_only = "Graph Powers read-only intent:" in (clone.get("developer_instructions") or "")
            if clone_read_only != native_read_only:
                raise AssertionError(
                    f"{path.relative_to(ROOT)}: native-companion/clone read-only intent mismatch for {agent_name}"
                )
        except (AssertionError, KeyError, tomllib.TOMLDecodeError) as exc:
            print(f"::error::{exc}")
            errors += 1

    source_agents = list((ROOT / "agents").glob("*.md"))
    if not source_agents:
        print("::error::no agents/*.md to generate from")
        return 1
    if len(source_agents) != len(data["agents"]):
        print(f"::error::native companion count {len(data['agents'])} != source {len(source_agents)}")
        errors += 1

    if generated.returncode != 0:
        print(generated.stderr)
        errors += 1

    if errors:
        return 1
    print(
        f"codex-native: {len(data['agents'])} companion roles, semantic native/clone parity, "
        "explicit permission-limit contract, "
        f"manifest {native_plugin.get('version')}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
