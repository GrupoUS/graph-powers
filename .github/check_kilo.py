#!/usr/bin/env python3
"""Kilo artefacts are generated from the Claude Code ones. This file proves they still are.

Kilo reads `~/.kilo/agent/*.md`, `~/.kilo/command/*.md`, `~/.kilo/skills/<name>/SKILL.md` and
`~/.kilo/plugin/*.ts` — proven against 7.6.2 with `kilo agent list`, `kilo debug skill` and
`kilo debug config`. `kilo/install.mjs` is the generator; this gate re-runs it into a throwaway
home and asserts the properties the projection promises:

* the full inventory (12 roles + the router, 13 commands, every canonical skill);
* a resolved `provider/model` id per role, never a Claude alias or a Codex slug;
* read-only and leaf boundaries actually present in the emitted frontmatter;
* no Claude-only literal surviving in anything Kilo reads;
* deterministic output, ownership refusal, and a config merge that keeps comments;
* a plugin whose registrations name scripts that exist.

No Kilo binary is required: the gate proves the generated surface, and `kilo debug agent` on a
machine with Kilo is the runtime confirmation recorded in `docs/kilo.md`.

Run from the repository root:  python3 .github/check_kilo.py
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "kilo" / "install.mjs"
POLICY = ROOT / "kilo" / "model-policy.json"
MANAGED_AGENT_DIRS = ("agent", "command", "skills", "plugin", "graph-powers")
FORBIDDEN = ("graph-powers:", "Workflow(", "${CLAUDE_PLUGIN_ROOT}")
SKILL_CALL = re.compile(r"Skill\(\s*[\"']")
KILO_EVENTS = {"PreToolUse", "PostToolUse"}


def fail(problems: list[str], message: str) -> None:
    problems.append(message)


def node(script: str, *args: str, env: dict[str, str] | None = None, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    merged = {**os.environ, **(env or {})}
    return subprocess.run(
        ["node", *script.split("\0"), *args],
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        cwd=str(cwd or ROOT),
        env=merged,
    )


def run_installer(home: Path, *flags: str) -> subprocess.CompletedProcess[str]:
    return node(
        str(INSTALLER),
        *flags,
        env={
            "HOME": str(home),
            "KILO_HOME": str(home / ".kilo"),
            "KILO_CONFIG_DIR": str(home / ".config" / "kilo"),
            "GRAPH_POWERS_KILO_MODELS": "",
            "XDG_CONFIG_HOME": str(home / ".config"),
            "XDG_DATA_HOME": str(home / ".local" / "share"),
            "XDG_STATE_HOME": str(home / ".local" / "state"),
            "XDG_CACHE_HOME": str(home / ".cache"),
        },
    )


def install_json(home: Path, *flags: str) -> dict[str, Any]:
    result = run_installer(home, "--json", *flags)
    if result.returncode != 0:
        raise AssertionError(f"installer failed ({result.returncode}): {result.stderr.strip()}")
    start = result.stdout.find("{")
    if start < 0:
        raise AssertionError(f"installer produced no JSON: {result.stdout[:400]}")
    return json.loads(result.stdout[start:])


def canonical() -> tuple[list[str], list[str], list[str]]:
    agents = sorted(p.stem for p in (ROOT / "agents").glob("*.md"))
    commands = sorted(p.stem for p in (ROOT / "commands").glob("*.md"))
    skills = sorted(
        p.name for p in (ROOT / "skills").iterdir() if p.is_dir() and (p / "SKILL.md").is_file()
    )
    return agents, commands, skills


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def strip_jsonc(text: str) -> str:
    out: list[str] = []
    i = 0
    in_string = False
    quote = ""
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if in_string:
            out.append(ch)
            if ch == "\\":
                out.append(nxt)
                i += 2
                continue
            if ch == quote:
                in_string = False
            i += 1
            continue
        if ch in "\"'":
            in_string = True
            quote = ch
            out.append(ch)
            i += 1
            continue
        if ch == "/" and nxt == "/":
            while i < len(text) and text[i] != "\n":
                i += 1
            continue
        out.append(ch)
        i += 1
    return re.sub(r",(\s*[}\]])", r"\1", "".join(out))


def config_object(home: Path) -> dict[str, Any]:
    return json.loads(strip_jsonc(read(home / ".kilo" / "kilo.jsonc")))


def frontmatter(text: str) -> dict[str, Any]:
    match = re.match(r"^---\n([\s\S]*?)\n---\n", text)
    if not match:
        raise AssertionError("missing frontmatter")
    data: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, data)]
    for raw in match.group(1).split("\n"):
        if not raw.strip() or raw.strip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        key, _, value = raw.strip().partition(":")
        key = key.strip().strip('"')
        value = value.strip()
        if not value:
            child: dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
            continue
        parent[key] = value.strip('"')
    return data


def tree_hashes(root: Path) -> dict[str, str]:
    hashes = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            rel = path.relative_to(root).as_posix()
            hashes[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def files_for(home: Path) -> str:
    return "\n".join(
        f"{rel} {digest}" for rel, digest in sorted(tree_hashes(home / ".kilo").items())
    )


# ── checks ───────────────────────────────────────────────────────────────────


def check_inventory(problems: list[str], home: Path, result: dict[str, Any]) -> dict[str, Any]:
    agents, commands, skills = canonical()
    installed_agents = sorted(p.stem for p in (home / ".kilo" / "agent").glob("*.md"))
    installed_commands = sorted(p.stem for p in (home / ".kilo" / "command").glob("*.md"))
    installed_skills = sorted(
        p.name for p in (home / ".kilo" / "skills").iterdir() if p.is_dir() and (p / "SKILL.md").is_file()
    )
    if installed_agents != sorted([*agents, "graph-powers"]):
        fail(problems, f"agents: installed {installed_agents}, expected {sorted([*agents, 'graph-powers'])}")
    if installed_commands != commands:
        fail(problems, f"commands: installed {installed_commands}, expected {commands}")
    if installed_skills != skills:
        fail(problems, f"skills: installed {installed_skills}, expected {skills}")
    manifest = json.loads(read(home / ".kilo" / "graph-powers-installed.json"))
    version = json.loads(read(ROOT / ".claude-plugin" / "plugin.json"))["version"]
    if manifest.get("complete") is not True:
        fail(problems, "manifest is not marked complete")
    if manifest.get("version") != version:
        fail(problems, f"manifest version {manifest.get('version')} != plugin.json {version}")
    missing = [p for p in manifest.get("paths", []) if not Path(p).exists()]
    if missing:
        fail(problems, f"manifest records paths that do not exist: {missing[:5]}")
    plugin = home / ".kilo" / "plugin" / "graph-powers-guardrails.ts"
    if not plugin.is_file():
        fail(problems, "the guardrail plugin was not written")
    return {"agents": agents, "commands": commands, "skills": skills}


def check_agents(problems: list[str], home: Path, agents: list[str]) -> None:
    policy = json.loads(read(POLICY))
    profiles = policy["profiles"]
    expected_model = {
        name: profiles[profile]["model"] for name, profile in policy["agents"].items()
    }
    for name in agents:
        path = home / ".kilo" / "agent" / f"{name}.md"
        if not path.is_file():
            fail(problems, f"agent {name}: missing")
            continue
        text = read(path)
        if re.search(r"^effort:|^variant:|^temperature:|^top_p:", text, re.MULTILINE):
            fail(problems, f"agent {name}: carries a Claude-only tuning key")
        try:
            data = frontmatter(text)
        except AssertionError as exc:
            fail(problems, f"agent {name}: {exc}")
            continue
        if data.get("mode") != "subagent":
            fail(problems, f"agent {name}: mode is {data.get('mode')!r}")
        if not data.get("description"):
            fail(problems, f"agent {name}: empty description")
        model = data.get("model", "")
        if model != expected_model.get(name):
            fail(problems, f"agent {name}: model {model!r} != policy {expected_model.get(name)!r}")
        provider, _, bare = model.partition("/")
        if provider != "kilo" or not bare:
            fail(problems, f"agent {name}: model {model!r} is not a Kilo provider/model id")
        if name == "evaluator":
            permission = data.get("permission") or {}
            if permission.get("task") != "deny":
                fail(problems, f"agent {name}: leaf task denial missing")
        for claude in (ROOT / "agents" / f"{name}.md").read_text(encoding="utf-8").splitlines():
            if claude.startswith("disallowedTools:") and "Write" in claude:
                permission = data.get("permission") or {}
                if permission.get("edit") != "deny":
                    fail(problems, f"agent {name}: edit denial missing for a read-only role")
                break

    router = frontmatter(read(home / ".kilo" / "agent" / "graph-powers.md"))
    if router.get("mode") != "primary":
        fail(problems, "router agent is not mode: primary")
    if router.get("model"):
        fail(problems, "router agent must not pin a model; the main model is the operator's")


def check_commands(problems: list[str], home: Path, commands: list[str]) -> None:
    routing = json.loads(
        node(
            "-e\0import{COMMAND_ROUTING}from'./kilo/install.mjs';console.log(JSON.stringify(COMMAND_ROUTING))"
        ).stdout.strip()
    )
    if sorted(routing) != sorted(commands):
        fail(problems, f"COMMAND_ROUTING covers {sorted(routing)} but commands are {sorted(commands)}")
    for name in commands:
        data = frontmatter(read(home / ".kilo" / "command" / f"{name}.md"))
        if data.get("agent") != "graph-powers":
            fail(problems, f"command {name}: agent is {data.get('agent')!r}, expected the router")
        body = read(home / ".kilo" / "command" / f"{name}.md")
        if "Kilo routing." not in body:
            fail(problems, f"command {name}: routing footer missing")
        for agent in routing.get(name, []):
            if f"`{agent}`" not in body:
                fail(problems, f"command {name}: declared agent {agent} is not named in the body")


def check_forbidden(problems: list[str], home: Path) -> None:
    roots = [home / ".kilo" / d for d in MANAGED_AGENT_DIRS]
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            for literal in FORBIDDEN:
                if literal in text:
                    fail(problems, f"{path.relative_to(home)}: forbidden literal {literal!r}")
            if SKILL_CALL.search(text):
                fail(problems, f"{path.relative_to(home)}: unresolved Skill(\"...\") call")


def check_determinism(problems: list[str], home: Path) -> None:
    first = files_for(home)
    second_result = run_installer(home, "--json")
    if second_result.returncode != 0:
        fail(problems, f"second install failed: {second_result.stderr.strip()}")
        return
    second = files_for(home)
    if first != second:
        fail(problems, "regenerating into the same home changed bytes; output is not deterministic")


def check_ownership(problems: list[str]) -> None:
    with tempfile.TemporaryDirectory(prefix="gp-kilo-own-") as raw:
        home = Path(raw)
        target = home / ".kilo" / "agent" / "debugger.md"
        target.parent.mkdir(parents=True)
        target.write_text("---\ndescription: mine\nmode: subagent\n---\nmine\n", encoding="utf-8")
        refused = run_installer(home)
        if refused.returncode == 0:
            fail(problems, "install overwrote an unowned agent file")
        elif "refusing to overwrite unowned" not in (refused.stderr + refused.stdout):
            fail(problems, f"refusal message did not name ownership: {refused.stderr.strip()[:200]}")
        forced = run_installer(home, "--force")
        if forced.returncode != 0:
            fail(problems, f"--force did not override a recorded absence: {forced.stderr.strip()[:200]}")
        if "mine" in target.read_text(encoding="utf-8"):
            fail(problems, "--force did not replace the foreign agent file")


def check_config(problems: list[str]) -> None:
    with tempfile.TemporaryDirectory(prefix="gp-kilo-cfg-") as raw:
        home = Path(raw)
        config = home / ".kilo" / "kilo.jsonc"
        config.parent.mkdir(parents=True)
        config.write_text(
            "{\n"
            "  // operator comment\n"
            '  "permission": { "bash": { "ls *": "allow" } },\n'
            '  "model": "kilo/~openai/gpt-luna-latest"\n'
            "}\n",
            encoding="utf-8",
        )
        result = install_json(home)
        text = read(config)
        if "// operator comment" not in text:
            fail(problems, "config merge dropped a comment")
        if '"permission"' not in text or '"model"' not in text:
            fail(problems, "config merge dropped an unrelated key")
        if '"lsp"' not in text or '"formatter"' not in text:
            fail(problems, "config merge did not add the managed keys")
        if not result.get("configChanged"):
            fail(problems, "install reported no config change while adding managed keys")
        merged = config_object(home)
        permission = merged.get("permission")
        if not isinstance(permission, dict) or permission.get("bash") != {"ls *": "allow"}:
            fail(problems, "config merge overwrote the operator's own permission rules")
        if not isinstance(permission, dict) or permission.get("edit") != "allow":
            fail(problems, "config merge did not add the autonomous edit posture")
        # Uninstall restores the config surface.
        removed = run_installer(home, "--uninstall")
        if removed.returncode != 0:
            fail(problems, f"uninstall failed: {removed.stderr.strip()[:200]}")
        restored = read(config)
        if '"lsp"' in restored or '"formatter"' in restored:
            fail(problems, "uninstall left a managed config key behind")
        if "// operator comment" not in restored or '"model"' not in restored:
            fail(problems, "uninstall damaged the operator's config")
        if "permission" not in restored or '"ls *"' not in restored:
            fail(problems, "uninstall damaged the operator's permission rules")


def check_permission_posture(problems: list[str]) -> None:
    """Autonomous writes the whole Kilo approval posture, XDG permission or not; guarded writes none."""
    scalars = {"edit", "bash", "webfetch", "external_directory", "doom_loop"}
    expected = scalars | {"*"}
    with tempfile.TemporaryDirectory(prefix="gp-kilo-perm-") as raw:
        home = Path(raw)
        (home / ".config" / "kilo").mkdir(parents=True)
        install_json(home)
        permission = config_object(home).get("permission")
        if not isinstance(permission, dict) or set(permission) != expected:
            fail(
                problems,
                f"autonomous install wrote permission {permission!r}, expected all of {sorted(expected)}",
            )
        else:
            if any(permission.get(key) != "allow" for key in scalars):
                fail(problems, f"autonomous permission posture is not allow-all: {permission!r}")
            if permission.get("*") != {"*": "allow"}:
                fail(problems, f"autonomous permission catch-all missing: {permission!r}")
        # The posture is operator config, not a managed key: uninstall leaves it where it is.
        run_installer(home, "--uninstall")
        if "permission" not in config_object(home):
            fail(problems, "uninstall removed the operator's permission posture")
    # An XDG `permission` is shadowed by the home posture, not allowed to defeat autonomous.
    with tempfile.TemporaryDirectory(prefix="gp-kilo-perm-xdg-") as raw:
        home = Path(raw)
        xdg = home / ".config" / "kilo" / "kilo.jsonc"
        xdg.parent.mkdir(parents=True, exist_ok=True)
        xdg.write_text('{\n  "permission": { "bash": { "ls *": "allow" } }\n}\n', encoding="utf-8")
        result = install_json(home)
        permission = config_object(home).get("permission")
        if not isinstance(permission, dict) or permission.get("bash") != "allow":
            fail(problems, f"XDG permission defeated the autonomous posture: {permission!r}")
        if not any("XDG" in message for message in result.get("unavailable", [])):
            fail(problems, "shadowing the XDG permission was not reported")
    with tempfile.TemporaryDirectory(prefix="gp-kilo-perm-guarded-") as raw:
        home = Path(raw)
        (home / ".config" / "kilo").mkdir(parents=True)
        install_json(home, "--autonomy", "guarded")
        config = config_object(home)
        if "permission" in config:
            fail(problems, f"guarded install wrote an approval posture: {config['permission']!r}")


def check_config_conflict(problems: list[str]) -> None:
    """A managed key already in the XDG file is a conflict, not something to shadow."""
    with tempfile.TemporaryDirectory(prefix="gp-kilo-conflict-") as raw:
        home = Path(raw)
        xdg = home / ".config" / "kilo" / "kilo.jsonc"
        xdg.parent.mkdir(parents=True, exist_ok=True)
        xdg.write_text('{\n  "formatter": { "prettier": { "disabled": true } }\n}\n', encoding="utf-8")
        conflict = run_installer(home)
        if conflict.returncode == 0:
            fail(problems, "install ignored a managed key configured in the XDG file")
        elif "formatter" not in (conflict.stderr + conflict.stdout):
            fail(problems, f"conflict refusal did not name the key: {conflict.stderr.strip()[:200]}")


def check_model_policy(problems: list[str]) -> None:
    script = """-e\0import{isKiloModelId,resolveKiloAgentPolicy}from'./kilo/model-policy.mjs';
const bad=['opus','sonnet','haiku','fable','gpt-5.6-sol','claude-sonnet-4',''];
const good=['kilo/~openai/gpt-astra-latest','kilo/deepseek/deepseek-v4.1-flash'];
console.log(JSON.stringify({
rejected:bad.filter(isKiloModelId),
accepted:good.filter((m)=>!isKiloModelId(m)),
judge:resolveKiloAgentPolicy('evaluator').model,
executor:resolveKiloAgentPolicy('debugger').model,
leaf:resolveKiloAgentPolicy('evaluator').leaf,
override:resolveKiloAgentPolicy('debugger',{agent:{debugger:{model:'kilo/~openai/gpt-terra-latest'}}}).model,
}));"""
    result = node(script)
    if result.returncode != 0:
        fail(problems, f"model policy probe failed: {result.stderr.strip()[:300]}")
        return
    data = json.loads(result.stdout.strip().splitlines()[-1])
    if data["rejected"]:
        fail(problems, f"claude/codex model ids accepted: {data['rejected']}")
    if data["accepted"]:
        fail(problems, f"valid Kilo model ids rejected: {data['accepted']}")
    if not data["judge"].endswith("gpt-astra-latest"):
        fail(problems, f"judge profile resolves {data['judge']!r}")
    if not data["executor"].endswith("gpt-luna-latest"):
        fail(problems, f"executor profile resolves {data['executor']!r}")
    if data["leaf"] is not True:
        fail(problems, "evaluator is not declared a leaf")
    if not data["override"].endswith("gpt-terra-latest"):
        fail(problems, "per-agent override did not win")
    rejected = node(
        "-e\0import{resolveKiloAgentPolicy}from'./kilo/model-policy.mjs';"
        "try{resolveKiloAgentPolicy('debugger',{agent:{debugger:{model:'opus'}}});console.log('accepted')}"
        "catch{console.log('rejected')}"
    )
    if rejected.stdout.strip() != "rejected":
        fail(problems, "an invalid per-agent override was not rejected")


def check_plugin(problems: list[str], home: Path) -> None:
    text = read(home / ".kilo" / "plugin" / "graph-powers-guardrails.ts")
    match = re.search(r"const REGISTRATIONS = (\[[\s\S]*?\]);", text)
    if not match:
        fail(problems, "plugin has no REGISTRATIONS array")
        return
    registrations = json.loads(match.group(1))
    if not registrations:
        fail(problems, "plugin registers no policy")
    hooks = json.loads(read(ROOT / "hooks" / "hooks.json"))
    known = {
        name
        for entry in hooks.get("hooks", {}).values()
        for group in entry
        for hook in group.get("hooks", [])
        for name in re.findall(r"([A-Za-z0-9_]+\.py)", hook.get("command", ""))
    }
    for registration in registrations:
        script = Path(registration["script"])
        if registration["event"] not in KILO_EVENTS:
            fail(problems, f"plugin registers unsupported event {registration['event']!r}")
        if not script.is_file():
            fail(problems, f"plugin registers a missing script: {script}")
        elif script.name not in known:
            fail(problems, f"plugin registers {script.name}, which hooks.json does not declare")
    if any(registration["matcher"] == "Bash" and registration["script"].endswith("protect_files.py") for registration in registrations):
        fail(problems, "protect_files is registered against Bash")
    if "autoUpdate" in text or "stop_verify" in text:
        fail(problems, "plugin references a lifecycle Kilo does not have")


def check_project_scope(problems: list[str]) -> None:
    with tempfile.TemporaryDirectory(prefix="gp-kilo-proj-") as raw:
        home = Path(raw) / "home"
        project = Path(raw) / "repo"
        home.mkdir(parents=True)
        project.mkdir(parents=True)
        result = node(
            str(INSTALLER),
            "--scope",
            "project",
            "--project",
            str(project),
            "--json",
            env={
                "HOME": str(home),
                "KILO_HOME": str(home / ".kilo"),
                "KILO_CONFIG_DIR": str(home / ".config" / "kilo"),
                "GRAPH_POWERS_KILO_MODELS": "",
            },
        )
        if result.returncode != 0:
            fail(problems, f"project-scope install failed: {result.stderr.strip()[:200]}")
            return
        if not (project / ".kilo" / "agent" / "graph-powers.md").is_file():
            fail(problems, "project scope did not write agents into .kilo/agent")
        if (project / "kilo.jsonc").exists():
            fail(problems, "project scope wrote a kilo.jsonc; managed keys are global by design")
        for path in project.rglob("*.md"):
            text = read(path)
            if ".kilo/skills" not in text and "graph-powers:" in text:
                fail(problems, f"{path.relative_to(project)}: forbidden literal survived project scope")


def main() -> int:
    problems: list[str] = []
    if not shutil.which("node"):
        print("::error::node is required to regenerate the Kilo artefacts")
        return 1
    if not INSTALLER.is_file():
        print(f"::error::missing {INSTALLER.relative_to(ROOT)}")
        return 1
    with tempfile.TemporaryDirectory(prefix="gp-kilo-") as raw:
        home = Path(raw)
        (home / ".config" / "kilo").mkdir(parents=True)
        try:
            result = install_json(home)
        except AssertionError as exc:
            print(f"::error::{exc}")
            return 1
        inventory = check_inventory(problems, home, result)
        check_agents(problems, home, inventory["agents"])
        check_commands(problems, home, inventory["commands"])
        check_forbidden(problems, home)
        check_determinism(problems, home)
        check_plugin(problems, home)
    check_ownership(problems)
    check_config(problems)
    check_permission_posture(problems)
    check_config_conflict(problems)
    check_model_policy(problems)
    check_project_scope(problems)

    if problems:
        for message in problems:
            print(f"::error::{message}")
        print(f"kilo: FAIL ({len(problems)} problem(s))")
        return 1
    print("kilo: PASS (inventory, models, permissions, literals, determinism, ownership, config, plugin)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
