#!/usr/bin/env python3
"""Assertions on generated Codex artefacts, shared by both scopes of the CI job.

Kept as a file rather than a heredoc for one reason: the same checks have to run against two
different roots, and a duplicated heredoc is how the second copy drifts from the first.
"""

import collections
import glob
import json
import os
import sys
import tomllib

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
READ_ONLY_AGENTS = {
    "evaluator",
    "security-reviewer",
    "skill-improver",
    "ui-ux-designer",
    "explorer",
    "librarian",
    "verification",
}

root, project, scope = sys.argv[1], sys.argv[2], sys.argv[3]
codex_home = os.path.join(root, ".codex")
skills_dir = os.path.join(root, ".agents/skills")

with open(os.path.join(codex_home, "hooks.json"), encoding="utf-8") as fh:
    hooks = json.load(fh)
entries = [
    (event, g.get("matcher"), h["command"])
    for event, groups in hooks["hooks"].items()
    for g in groups
    for h in g["hooks"]
]
commands = [command for _, _, command in entries]
dupes = [entry for entry, n in collections.Counter(entries).items() if n > 1]
assert not dupes, f"duplicate hook entries after a second install: {dupes}"
assert any("/other/tool.mjs" in c for c in commands), "third-party hook was clobbered"
hook_names = {
    "auto_update",
    "branch_session_notice",
    "commit_audit_gate",
    "git_branch_gate",
    "git_commit_gate",
    "git_push_gate",
    "graph_guardrails",
    "notify",
    "protect_files",
    "session_context",
    "smart_bash_approver",
    "stop_verify",
    "subagent_context",
    "tool_approver",
    "ultracite",
}
ours = [c for c in commands if any(f"/hooks/{name}.py" in c for name in hook_names)]
assert len(ours) == 16, f"expected 16 Graph Powers registrations, found {len(ours)}"
assert {name for name in hook_names if any(f"/hooks/{name}.py" in c for c in ours)} == hook_names, (
    f"one of the {len(hook_names)} Graph Powers hook scripts is not registered"
)

agents = sorted(glob.glob(os.path.join(codex_home, "agents/*.toml")))
assert agents, f"no Codex subagents generated under {codex_home}"
efforts = set()
found = set()
for path in agents:
    with open(path, "rb") as fh:
        d = tomllib.load(fh)
    with open(path, encoding="utf-8") as fh:
        raw_agent = fh.read()
    assert d.get("name") and d.get("description") and d.get("developer_instructions"), path
    name = d["name"]
    assert name in EXPECTED_POLICY, f"{path}: unknown Codex agent {name!r}"
    profile, expected_model, expected_effort = EXPECTED_POLICY[name]
    assert f"# Codex policy: profile={profile};" in raw_agent, (
        f"{path}: missing policy-source trace for semantic profile {profile}"
    )
    assert d.get("model") == expected_model, (
        f"{path}: semantic policy mismatch for {name}: expected model {expected_model!r}, "
        f"got {d.get('model')!r}"
    )
    assert d.get("model_reasoning_effort") == expected_effort, (
        f"{path}: semantic policy mismatch for {name}: expected effort {expected_effort!r}, "
        f"got {d.get('model_reasoning_effort')!r}"
    )
    found.add(name)
    # A description that stopped at the first comma is the signature of the frontmatter reader
    # treating every key as a list. It is invisible in the file and fatal to discovery.
    assert len(d["description"]) > 40, f"{path}: description truncated -> {d['description']!r}"
    model = str(d.get("model") or "").lower()
    assert model not in {"haiku", "sonnet", "opus", "fable"}, (
        f"{path}: Claude family {model!r} is not a Codex slug — it spends the Spark / "
        "Bengal Fox window instead of the user's own limit"
    )
    assert "sandbox_mode" not in d, (
        f"{path}: unsupported per-role sandbox key would fake a boundary Codex does not apply"
    )
    read_only_notice = "Graph Powers read-only intent:" in d["developer_instructions"]
    assert read_only_notice == (name in READ_ONLY_AGENTS), (
        f"{path}: read-only intent does not match source authority for {name}"
    )
    if name == "evaluator":
        assert "Graph Powers leaf intent:" in d["developer_instructions"], (
            f"{path}: evaluator lost its explicit advisory leaf contract"
        )
    efforts.add(d.get("model_reasoning_effort"))
assert found == set(EXPECTED_POLICY), (
    f"expected exactly the 12 canonical agents, found {sorted(found)}"
)
assert len(efforts) > 1, (
    f"every subagent got the same reasoning effort ({efforts}) — frontmatter ignored"
)

# `${CLAUDE_PLUGIN_ROOT}` is a Claude Code variable. Codex never sets it, so a copy that still
# carries it points at nothing: the reference reads as present and loads as empty.
leaked = []
for base in (skills_dir, codex_home):
    for path in glob.glob(os.path.join(base, "**/*"), recursive=True):
        if not os.path.isfile(path) or not path.endswith((".md", ".toml", ".json")):
            continue
        with open(path, encoding="utf-8", errors="replace") as fh:
            if "CLAUDE_PLUGIN_ROOT" in fh.read():
                leaked.append(path)
assert not leaked, f"unresolved plugin-root placeholder in {len(leaked)} file(s): {leaked[:3]}"

manifest_path = (
    os.path.join(codex_home, "graph-powers-installed.json")
    if scope == "user"
    else os.path.join(project, ".graph-powers/installed.json")
)
with open(manifest_path, encoding="utf-8") as fh:
    manifest = json.load(fh)
assert manifest.get("complete") is True, "the manifest does not record a finished install"
assert manifest.get("paths"), "the manifest records no paths — removal would be a guess"
assert not any(p.rstrip("/").endswith((".agents/skills", "skills")) for p in manifest["paths"]), (
    "the manifest records a shared parent directory; removal would delete other tools' skills"
)

with open(os.path.join(project, "AGENTS.md"), encoding="utf-8") as fh:
    text = fh.read()
assert text.count("graph-powers:start") == 1, "AGENTS.md block duplicated"

print(
    f"{scope}: {len(agents)} subagents, {len(commands)} hook entries, "
    f"{len(efforts)} distinct efforts, no placeholders, block idempotent"
)
