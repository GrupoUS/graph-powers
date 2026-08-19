#!/usr/bin/env python3
"""Proves the guardrails adapt to the project — and that one project never leaks into another.

Run from the plugin root:  python3 hooks/test_hooks.py

There is one copy of each hook, installed in N repositories with different branches and
different opt-in keys. The claim that needs proof is not "the hook works", it is "the same
bytes behave correctly in two projects at once" — including refusing the neighbouring
project's approval key, which is what stops an authorisation given in one repository from
counting in another.

The same files run under Claude Code and under Codex CLI. Claude exports CLAUDE_PROJECT_DIR;
Codex does not, and passes `cwd` in the hook payload instead. Both resolutions are covered
below, because a guardrail that silently resolves the wrong project is worse than one that
does not run at all: it denies and permits against somebody else's rules.

Everything runs in temporary directories. The kill-switch case in particular: created at the
root of a real repository it would deny every tool call of the session running this test.

Exit 0 = all passed. Exit 1 = at least one guarantee fell.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HOOKS = Path(__file__).resolve().parent
FAILS: list[str] = []


def mkproj(cfg: dict, *, location: str = ".graph-powers") -> Path:
    d = Path(tempfile.mkdtemp(prefix="gp-proj-"))
    (d / location).mkdir(parents=True)
    (d / location / "config.json").write_text(json.dumps(cfg), encoding="utf-8")
    return d


def call(hook: str, payload: dict, proj: Path, *, harness: str = "claude", env: dict | None = None):
    """Invoke a hook the way the named harness would.

    claude: CLAUDE_PROJECT_DIR in the environment, nothing in the payload.
    codex:  no CLAUDE_PROJECT_DIR at all, `cwd` in the payload — the Codex contract.
    """
    env_full = {**os.environ, **(env or {})}
    body = dict(payload)
    if harness == "claude":
        env_full["CLAUDE_PROJECT_DIR"] = str(proj)
    else:
        env_full.pop("CLAUDE_PROJECT_DIR", None)
        body["cwd"] = str(proj)

    r = subprocess.run(
        [sys.executable, str(HOOKS / f"{hook}.py")],
        input=json.dumps(body), capture_output=True, text=True,
        env=env_full, cwd=str(proj), timeout=30,
    )
    out = r.stdout.strip()
    if not out:
        return None, r.returncode
    try:
        return json.loads(out)["hookSpecificOutput"]["permissionDecision"], r.returncode
    except Exception:
        return "??", r.returncode


def check(label: str, got, want) -> None:
    ok = got == want
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}: {got!r} (expected {want!r})")
    if not ok:
        FAILS.append(label)


def main() -> int:
    # Two projects deliberately different in everything the plugin parameterises.
    a = mkproj({"git": {"optInPrefix": "PROJA", "workBranch": "dev-test",
                        "protectedBranches": ["main", "master"]}})
    b = mkproj({"git": {"optInPrefix": "PROJB", "workBranch": "develop",
                        "protectedBranches": ["main", "producao"]}})
    legacy = mkproj({"git": {"optInPrefix": "LEGACY"}}, location=".claude")
    no_config = Path(tempfile.mkdtemp(prefix="gp-no-config-"))

    commit = {"tool_name": "Bash", "tool_input": {"command": "git commit -m x"}}
    key_a = {"tool_name": "Bash", "tool_input": {"command": "PROJA_ALLOW_COMMIT=1 git commit -m x"}}
    key_b = {"tool_name": "Bash", "tool_input": {"command": "PROJB_ALLOW_COMMIT=1 git commit -m x"}}
    read = {"tool_name": "Read", "session_id": "s"}

    print("### Git rails — every project has its own key")
    check("A denies a commit with no opt-in", call("git_commit_gate", commit, a)[0], "deny")
    check("B denies a commit with no opt-in", call("git_commit_gate", commit, b)[0], "deny")
    check("A accepts its own key", call("git_commit_gate", key_a, a)[0], None)
    check("B accepts its own key", call("git_commit_gate", key_b, b)[0], None)
    check("B's key does not count in A", call("git_commit_gate", key_b, a)[0], "deny")
    check("A's key does not count in B", call("git_commit_gate", key_a, b)[0], "deny")

    print("### Same bytes under Codex — project resolved from the payload cwd")
    check("A denies (codex)", call("git_commit_gate", commit, a, harness="codex")[0], "deny")
    check("A accepts its own key (codex)", call("git_commit_gate", key_a, a, harness="codex")[0], None)
    check("B's key still does not count in A (codex)",
          call("git_commit_gate", key_b, a, harness="codex")[0], "deny")
    check("B denies A's key (codex)", call("git_commit_gate", key_a, b, harness="codex")[0], "deny")

    print("### Protected branches — 'producao' exists only in project B")
    prod = {"tool_name": "Bash", "tool_input": {"command": "git switch producao"}}
    check("A allows it (not protected there)", call("git_branch_gate", prod, a)[0], None)
    check("B denies it", call("git_branch_gate", prod, b)[0], "deny")
    check("B denies it under codex too", call("git_branch_gate", prod, b, harness="codex")[0], "deny")

    print("### Kill switch — stops the right project, and only it")
    (a / "AGENT_STOP").touch()
    check("A stopped", call("graph_guardrails", read, a)[0], "deny")
    check("B continues", call("graph_guardrails", read, b)[0], None)
    check("A stopped under codex", call("graph_guardrails", read, a, harness="codex")[0], "deny")
    (a / "AGENT_STOP").unlink()
    check("A back to normal", call("graph_guardrails", read, a)[0], None)

    print("### Legacy config location — .claude/config.json still read")
    legacy_key = {"tool_name": "Bash", "tool_input": {"command": "LEGACY_ALLOW_COMMIT=1 git commit -m x"}}
    check("legacy project denies without its key", call("git_commit_gate", commit, legacy)[0], "deny")
    check("legacy project accepts its key", call("git_commit_gate", legacy_key, legacy)[0], None)

    print("### Autonomy — the level decides how much stops to ask")
    auton = mkproj({"git": {"optInPrefix": "AUTON"},
                    "autonomy": {"level": "autonomous"}})
    partial = mkproj({"git": {"optInPrefix": "PART"},
                      "autonomy": {"level": "autonomous", "git": {"push": "ask"}}})
    push = {"tool_name": "Bash", "tool_input": {"command": "git push origin dev-test"}}
    unknown = {"tool_name": "Bash", "tool_input": {"command": "some-unknown-tool --flag"}}
    cleanup = {"tool_name": "Bash", "tool_input": {"command": "rm -rf build"}}
    nuke = {"tool_name": "Bash", "tool_input": {"command": "rm -rf /"}}

    check("guarded still denies a bare commit", call("git_commit_gate", commit, a)[0], "deny")
    check("autonomous commits without a key", call("git_commit_gate", commit, auton)[0], None)
    check("autonomous pushes without a key", call("git_push_gate", push, auton)[0], None)
    check("per-action override keeps push asking",
          call("git_push_gate", push, partial)[0], "deny")
    check("...while commit stays automatic", call("git_commit_gate", commit, partial)[0], None)
    check("guarded asks about an unknown command",
          call("smart_bash_approver", unknown, a)[0], "ask")
    check("autonomous runs an unknown command",
          call("smart_bash_approver", unknown, auton)[0], "allow")
    check("autonomous cleans up without asking",
          call("smart_bash_approver", cleanup, auton)[0], "allow")
    check("the destructive floor holds even when autonomous",
          call("smart_bash_approver", nuke, auton)[0], "deny")

    print("### Package managers — the plugin does not pick one for the project")
    pm_free = mkproj({"git": {"optInPrefix": "PMFREE"}})
    pm_bun = mkproj({"git": {"optInPrefix": "PMBUN"},
                     "autonomy": {"allowPackageManagers": ["bun", "bunx"]}})
    npm = {"tool_name": "Bash", "tool_input": {"command": "npm install"}}
    bun = {"tool_name": "Bash", "tool_input": {"command": "bun install"}}
    check("npm runs when the project declares nothing",
          call("smart_bash_approver", npm, pm_free)[0], "allow")
    check("npm is refused when the project declared bun only",
          call("smart_bash_approver", npm, pm_bun)[0], "deny")
    check("...and bun still runs there", call("smart_bash_approver", bun, pm_bun)[0], "allow")

    print("### Fail-open — a project with no config does not break")
    check("defaults still protect the commit", call("git_commit_gate", commit, no_config)[0], "deny")
    check("guardrails exits 0", call("graph_guardrails", read, no_config)[1], 0)

    print("### Malformed config never raises, and never silently disarms a guardrail")
    # Both of these were real: a wrong-typed section raised TypeError inside the hook, breaking the
    # fail-open contract; and `protectedBranches` written as a string was iterated character by
    # character, so no branch ever matched and the branch gate quietly stopped protecting anything.
    for label, body in (
        ("section of the wrong type", '{"git": "dev-test"}'),
        ("protectedBranches as a string", '{"git": {"protectedBranches": "producao"}}'),
        ("protectedFiles as a number", '{"protectedFiles": 5}'),
        ("ceiling as a word", '{"graphGuardrails": {"maxSpawnsPerSession": "many"}}'),
        ("autonomy as a string", '{"autonomy": "autonomous"}'),
        ("the whole config is a list", "[1, 2, 3]"),
    ):
        d = Path(tempfile.mkdtemp(prefix="gp-bad-"))
        (d / ".graph-powers").mkdir()
        (d / ".graph-powers/config.json").write_text(body, encoding="utf-8")
        check(f"{label}: the commit gate still denies",
              call("git_commit_gate", commit, d)[0], "deny")
        check(f"{label}: guardrails exit 0", call("graph_guardrails", read, d)[1], 0)
        shutil.rmtree(d, ignore_errors=True)

    # The likely intent of a bare string is one branch, not four characters.
    one = mkproj({"git": {"optInPrefix": "ONE", "protectedBranches": "producao"}})
    switch = {"tool_name": "Bash", "tool_input": {"command": "git switch producao"}}
    check("a single protected branch written as a string still protects it",
          call("git_branch_gate", switch, one)[0], "deny")
    shutil.rmtree(one, ignore_errors=True)

    print("### Fail-open — invalid payload never takes the session down")
    for hook in ("git_commit_gate", "git_push_gate", "git_branch_gate", "graph_guardrails",
                 "protect_files", "smart_bash_approver", "session_context", "notify"):
        r = subprocess.run(
            [sys.executable, str(HOOKS / f"{hook}.py")],
            input="this is not json", capture_output=True, text=True,
            env={**os.environ, "CLAUDE_PROJECT_DIR": str(a)}, timeout=30,
        )
        check(f"{hook} exits 0 on garbage input", r.returncode, 0)

    print("### protect_files — the generic floor plus what the project declared")
    guarded = mkproj({"protectedFiles": {"exact": ["ops/secrets.yaml"]}})
    env_file = {"tool_name": "Write", "tool_input": {"file_path": str(guarded / ".env")}}
    declared = {"tool_name": "Write", "tool_input": {"file_path": str(guarded / "ops/secrets.yaml")}}
    ordinary = {"tool_name": "Write", "tool_input": {"file_path": str(guarded / "src/app.ts")}}
    check("generic default denies .env", call("protect_files", env_file, guarded)[0], "deny")
    check("declared path denied", call("protect_files", declared, guarded)[0], "deny")
    check("an ordinary file is not denied", call("protect_files", ordinary, guarded)[0], None)

    for d in (a, b, legacy, no_config, guarded, auton, partial, pm_free, pm_bun):
        shutil.rmtree(d, ignore_errors=True)

    print("\n" + ("FAILURES: " + ", ".join(FAILS) if FAILS else "EVERY GUARANTEE HELD"))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
