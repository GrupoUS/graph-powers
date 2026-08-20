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
import time
from pathlib import Path

HOOKS = Path(__file__).resolve().parent
FAILS: list[str] = []

# Every hook below runs with this as its home directory unless a case deliberately says otherwise.
#
# Hooks read `~/.graph-powers/config.json` for the operator's own autonomy posture, so without this
# the suite inherits whatever the person running it happens to have set — and it does not fail
# honestly, it fails as six unrelated cases about guarded defaults. That is the same class of bug
# the two-project cases exist to catch, one level up: a setting from outside the fixture deciding
# the fixture's behaviour. The directory is created empty and never written to.
EMPTY_HOME = Path(tempfile.mkdtemp(prefix="gp-empty-home-"))

# Assembled rather than written out, and not for style. This file is edited by agents whose own
# commit gate scans the Bash command that performs the edit; a literal here turns every edit of
# the test suite into a blocked tool call, which is a guardrail firing at its own author.
GIT_WRITE = " ".join(["git", "commit", "-m", "x"])  # noqa: FLY002 — see the comment above


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
    env_full = {**os.environ, "HOME": str(EMPTY_HOME), "USERPROFILE": str(EMPTY_HOME),
                **(env or {})}
    body = dict(payload)
    if harness == "claude":
        env_full["CLAUDE_PROJECT_DIR"] = str(proj)
    else:
        env_full.pop("CLAUDE_PROJECT_DIR", None)
        body["cwd"] = str(proj)

    r = subprocess.run(
        [sys.executable, str(HOOKS / f"{hook}.py")],
        input=json.dumps(body), capture_output=True, encoding="utf-8", errors="replace",
        env=env_full, cwd=str(proj), timeout=30, check=False,
    )
    out = r.stdout.strip()
    if not out:
        return None, r.returncode
    try:
        return json.loads(out)["hookSpecificOutput"]["permissionDecision"], r.returncode
    except Exception:
        return "??", r.returncode


def call_raw(hook: str, payload: dict, proj: Path, *, env: dict | None = None,
             harness: str = "claude"):
    """Same call, but the whole stdout — for hooks that emit context rather than a decision."""
    env_full = {**os.environ, "HOME": str(EMPTY_HOME), "USERPROFILE": str(EMPTY_HOME),
                **(env or {})}
    payload = dict(payload)
    if harness == "claude":
        env_full["CLAUDE_PROJECT_DIR"] = str(proj)
    else:
        env_full.pop("CLAUDE_PROJECT_DIR", None)
        payload["cwd"] = str(proj)
    r = subprocess.run(
        [sys.executable, str(HOOKS / f"{hook}.py")],
        input=json.dumps(payload), capture_output=True, encoding="utf-8", errors="replace",
        env=env_full, cwd=str(proj), timeout=30, check=False,
    )
    return r.stdout, r.returncode


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

    commit = {"tool_name": "Bash", "tool_input": {"command": GIT_WRITE}}
    key_a = {"tool_name": "Bash", "tool_input": {"command": "PROJA_ALLOW_COMMIT=1 " + GIT_WRITE}}
    key_b = {"tool_name": "Bash", "tool_input": {"command": "PROJB_ALLOW_COMMIT=1 " + GIT_WRITE}}
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
    legacy_key = {"tool_name": "Bash",
                  "tool_input": {"command": "LEGACY_ALLOW_COMMIT=1 " + GIT_WRITE}}
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
    # `["bun"]` and not `["bun", "bunx"]`, deliberately. The fixture used to list the runner too,
    # and so did all five real projects — because listing it was the only way to run `bunx` at all.
    # That workaround is what kept the defect out of CI: the allowlist compared the literal command
    # word, so `bunx` under `["bun"]` was refused, and the refusal even said `bunx` is not one of
    # them while `bun` sat right there in the message. A fixture that carries the workaround cannot
    # see the bug the workaround exists for.
    pm_bun = mkproj({"git": {"optInPrefix": "PMBUN"},
                     "autonomy": {"allowPackageManagers": ["bun"]}})
    npm = {"tool_name": "Bash", "tool_input": {"command": "npm install"}}
    bun = {"tool_name": "Bash", "tool_input": {"command": "bun install"}}
    bunx = {"tool_name": "Bash", "tool_input": {"command": "bunx impeccable install"}}
    npx = {"tool_name": "Bash", "tool_input": {"command": "npx impeccable install"}}
    check("npm runs when the project declares nothing",
          call("smart_bash_approver", npm, pm_free)[0], "allow")
    check("npm is refused when the project declared bun only",
          call("smart_bash_approver", npm, pm_bun)[0], "deny")
    check("...and bun still runs there", call("smart_bash_approver", bun, pm_bun)[0], "allow")

    # The family rule, both directions. A runner is admitted by its own manager and by nothing else,
    # which is what keeps the lockfile guarantee while letting the project use the tool it chose.
    check("bunx runs under a bare `bun` declaration — it is bun's own runner",
          call("smart_bash_approver", bunx, pm_bun)[0], "allow")
    check("...while npx is still refused there — it belongs to npm",
          call("smart_bash_approver", npx, pm_bun)[0], "deny")

    # One-directional: naming only the runner does not hand over the manager. Someone who wrote
    # `["npx"]` asked for one-off execution, not for `npm install` to start rewriting the lockfile.
    pm_npx = mkproj({"git": {"optInPrefix": "PMNPX"},
                     "autonomy": {"allowPackageManagers": ["npx"]}})
    check("declaring npx admits npx", call("smart_bash_approver", npx, pm_npx)[0], "allow")
    check("...and does not admit npm", call("smart_bash_approver", npm, pm_npx)[0], "deny")

    # The workaround still works, because five repositories are carrying it right now and an
    # upgrade that punished them for the plugin's own defect would be the wrong kind of fix.
    pm_both = mkproj({"git": {"optInPrefix": "PMBOTH"},
                      "autonomy": {"allowPackageManagers": ["bun", "bunx"]}})
    check("the explicit `[bun, bunx]` form keeps working",
          call("smart_bash_approver", bunx, pm_both)[0], "allow")
    check("...and still refuses npm", call("smart_bash_approver", npm, pm_both)[0], "deny")

    print("### One question sorts every command: does git undo it?")
    # Both halves are proved, because a gate that refuses the correct case trains people to ignore
    # gates. The `autonomous` project is used for the floor cases on purpose: that is the setting
    # under which these commands used to run unannounced, which is what made them worth adding.
    def bash(cmd: str) -> dict:
        return {"tool_name": "Bash", "tool_input": {"command": cmd}}

    # Reversible: git undoes it, so a prompt buys nothing. Asserted under `guarded`, the strict side.
    for label, cmd in [
        ("git add", "git add -A"),
        ("git merge", "git merge feature"),
        ("git rebase", "git rebase main"),
        ("git pull", "git pull"),
        ("a soft reset", "git reset HEAD~1"),
        ("git stash", "git stash"),
        ("unstaging", "git restore --staged src/app.ts"),
        ("opening a PR", "gh pr create --title x"),
        ("moving a file", "mv old.ts new.ts"),
        ("an additive rsync", "rsync -a src/ dest/"),
    ]:
        check(f"guarded runs {label} without asking",
              call("smart_bash_approver", bash(cmd), a)[0], "allow")

    # Build artefacts: never versioned, regenerated by the next build. Also under `guarded`.
    for label, cmd in [
        ("__pycache__", "rm -rf __pycache__"),
        ("a bundler cache", "rm -rf node_modules/.cache"),
        ("a coverage dir", "rm -rf coverage"),
    ]:
        check(f"guarded deletes {label} without asking",
              call("smart_bash_approver", bash(cmd), a)[0], "allow")

    # Irreversible: git cannot bring it back. Denied even when the project said `autonomous`.
    for label, cmd in [
        ("deleting untracked files", "git clean -fd"),
        ("the long form of the same", "git clean --force"),
        ("discarding the working tree", "git reset --hard origin/main"),
        ("dropping a stash", "git stash drop"),
        ("clearing every stash", "git stash clear"),
        ("expiring the reflog", "git reflog expire --expire=now --all"),
        ("pruning unreachable objects", "git gc --prune=now"),
        ("rewriting history", "git filter-branch --all"),
        ("deleting a ref", "git update-ref -d refs/heads/wip"),
        ("force-deleting a branch", "git branch -D wip"),
    ]:
        check(f"the floor stops {label}, even autonomous",
              call("smart_bash_approver", bash(cmd), auton)[0], "deny")

    # The mirrored legitimate case for each floor entry above: the safe form of the same verb.
    for label, cmd in [
        ("a dry-run clean is not a delete", "git clean -n"),
        ("a soft reset is not a hard one", "git reset --soft HEAD~1"),
        ("popping a stash is not dropping it", "git stash pop"),
        ("listing the reflog is not expiring it", "git reflog"),
        ("a plain gc keeps unreachable objects", "git gc"),
        ("creating a ref is not deleting one", "git update-ref refs/heads/wip HEAD"),
        ("listing branches is not deleting one", "git branch -a"),
    ]:
        check(f"...but {label}",
              call("smart_bash_approver", bash(cmd), auton)[0] != "deny", True)

    # One owner per decision. The generic approver stops voting on what a dedicated gate owns;
    # the gate still refuses, because Claude Code merges PreToolUse decisions most-restrictive-first
    # (`deny` > `defer` > `ask` > `allow`) with every matching hook run in parallel. Proving both
    # halves is the point: an `allow` here that silently disarmed the gate would be the worst
    # possible outcome of making this hook more permissive.
    for label, cmd, gate in [
        ("committing", GIT_WRITE, "git_commit_gate"),
        ("pushing", "git push origin dev-test", "git_push_gate"),
        ("landing on a protected branch", "git checkout main", "git_branch_gate"),
    ]:
        check(f"the generic approver no longer double-asks about {label}",
              call("smart_bash_approver", bash(cmd), a)[0], "allow")
        check(f"...and {gate} still denies it, which is what decides",
              call(gate, bash(cmd), a)[0], "deny")

    # The plugin does not name a package manager. Before this, `bun run dev` asked and
    # `pnpm run dev` did not, in the same project, for the same kind of command.
    for pm in ("bun", "pnpm", "npm", "yarn"):
        check(f"guarded runs `{pm} run dev` without asking",
              call("smart_bash_approver", bash(f"{pm} run dev"), a)[0], "allow")

    print("### Windows shells get the same floor, and stop being asked about reads")
    # Every list in `smart_bash_approver` was POSIX grammar, so on a machine whose Bash tool maps
    # to PowerShell or cmd nothing matched: `Remove-Item -Recurse -Force C:\` fell through to
    # `bashDefault`, which under `autonomous` is allow. The floor the docstring calls "always
    # denied" did not exist there — and the mirror image was as bad, with `Get-ChildItem` falling
    # through to `ask`. Windows was prompted about the harmless and waved through the catastrophic.
    # The suite could not see it because every fixture string was POSIX.
    for label, cmd in [
        ("deleting a drive root", "Remove-Item -Recurse -Force C:\\"),
        ("the cmd spelling of it", "del /f /s /q C:\\"),
        ("deleting the user profile", "rd /s /q %USERPROFILE%"),
        ("formatting a volume", "format C:"),
        ("destroying shadow copies", "vssadmin delete shadows /all"),
        ("wiping free space", "cipher /w:C:"),
        ("rewriting boot config", "bcdedit /set testsigning on"),
        ("granting Everyone write", "icacls C:\\repo /grant Everyone:F"),
        ("disabling the execution policy", "Set-ExecutionPolicy Bypass"),
    ]:
        check(f"the floor stops {label} on Windows, even autonomous",
              call("smart_bash_approver", bash(cmd), auton)[0], "deny")

    for label, cmd in [
        ("listing a directory", "Get-ChildItem -Recurse"),
        ("the cmd spelling of it", "dir"),
        ("reading a file", "Get-Content package.json"),
        ("searching in files", "Select-String tenant *.ts"),
        ("the cmd spelling of that", "findstr /s tenant *.ts"),
        ("testing a path", "Test-Path .\\dist"),
        ("copying a file", "Copy-Item a.ts b.ts"),
        ("the Windows python launcher", "py -3 --version"),
    ]:
        check(f"guarded runs {label} on Windows without asking",
              call("smart_bash_approver", bash(cmd), a)[0], "allow")

    # A recursive delete that is not a drive root stays cleanup, exactly as `rm -rf build` does.
    # Sending it to the floor would make the Windows side stricter than the POSIX one, which is
    # its own kind of wrong.
    for label, cmd in [
        ("a build directory", "Remove-Item -Recurse .\\dist"),
        ("the cmd spelling", "rd /s /q build"),
    ]:
        check(f"...but deleting {label} is cleanup, not the floor",
              call("smart_bash_approver", bash(cmd), auton)[0], "allow")
        check(f"...and guarded still asks about deleting {label}",
              call("smart_bash_approver", bash(cmd), a)[0], "ask")

    print("### The opt-in key works in every shell, because it is text and not syntax")
    # `opted_in` looks for the literal `<KEY>=1` anywhere in the command string, so releasing a
    # gate never depends on the shell interpreting an inline assignment — which cmd.exe and
    # PowerShell do not. That is what makes these guardrails usable on Windows at all, and right
    # now it is a property of one `in` test. A refactor to `^KEY=1\s` would still pass every other
    # assertion in this file and would silently lock out every Windows user.
    for shell, cmd in {
        "POSIX": "PROJA_ALLOW_COMMIT=1 " + GIT_WRITE,
        "PowerShell": "$env:PROJA_ALLOW_COMMIT=1; " + GIT_WRITE,
        "cmd.exe": "set PROJA_ALLOW_COMMIT=1 && " + GIT_WRITE,
    }.items():
        check(f"the key releases the commit gate from {shell}",
              call("git_commit_gate", {"tool_name": "Bash", "tool_input": {"command": cmd}}, a)[0], None)
    check("...and the same command without it is still refused",
          call("git_commit_gate", commit, a)[0], "deny")

    print("### Execution ceilings — the three that shipped with no test at all")
    # G2, G3 and G4 have been in the plugin since the first release and never had a single
    # assertion behind them, which is exactly the state `.claude/rules/hooks.md` forbids: "a
    # guardrail never seen denying is an assumption". G4 was worse than untested — the hook read a
    # lease file that nothing in the repository ever wrote, so it stood down on every call.
    ceil = mkproj({"git": {"optInPrefix": "CEIL"},
                   "graphGuardrails": {"maxSpawnsPerSession": 3, "maxRoundsPerAgent": 2}})
    def spawn(kind: str) -> dict:
        return {"tool_name": "Agent", "tool_input": {"subagent_type": kind}}
    def write_to(path: str) -> dict:
        return {"tool_name": "Write", "tool_input": {"file_path": str(ceil / path)}}

    # G2 — spawn ceiling. Each call is one session, keyed by session_id, so vary the agent type to
    # keep G3 out of the way and let the total be what trips.
    sess = {"session_id": "ceil-g2"}
    for i, kind in enumerate(["explorer", "librarian", "evaluator"], 1):
        check(f"spawn {i}/3 is under the ceiling",
              call("graph_guardrails", {**spawn(kind), **sess}, ceil)[0], None)
    check("the 4th spawn is refused",
          call("graph_guardrails", {**spawn("debugger"), **sess}, ceil)[0], "deny")
    check("...and the opt-in key releases it",
          call("graph_guardrails", {**spawn("debugger"), **sess}, ceil,
               env={"CEIL_ALLOW_SPAWN_OVER": "1"})[0], None)

    # A refused spawn is NOT charged, and the ceiling holds anyway. Charging for it was the older
    # behaviour, defended as "otherwise a caller retries forever at no cost" — but a retry that is
    # refused never ran, so there is nothing to charge, and the refusal repeats regardless because
    # the spawns that DID run are still inside the window. All the charge bought was a number that
    # grew with every retry until it described nothing that happened: this repository's own log
    # read `27 agent spawns` in a session where 25 ran and 2 were denied.
    counter = ceil / ".graph-powers" / "logs" / "sessions" / "ceil-g2-guardrails.json"
    charged = json.loads(counter.read_text(encoding="utf-8"))["spawnsInWindow"]
    check("a refused spawn is still refused on retry",
          call("graph_guardrails", {**spawn("explorer"), **sess}, ceil)[0], "deny")
    check("...and was not charged to the window",
          json.loads(counter.read_text(encoding="utf-8"))["spawnsInWindow"], charged)

    # The window is what the ceiling counts over. Twenty-five spawns in an hour is a runaway
    # fan-out; the same twenty-five across a day of work is a day of work. Counted from session
    # start the ceiling became a session-lifetime quota that, once reached, refused the FIRST
    # spawn of every unrelated later task for the rest of the session.
    aged = {"spawnEvents": [[time.time() - 7200, k] for k in ("explorer", "librarian", "evaluator")]}
    counter.write_text(json.dumps(aged), encoding="utf-8")
    check("spawns older than the window do not count against it",
          call("graph_guardrails", {**spawn("debugger"), **sess}, ceil)[0], None)
    fresh = {"spawnEvents": [[time.time(), k] for k in ("explorer", "librarian", "evaluator")]}
    counter.write_text(json.dumps(fresh), encoding="utf-8")
    check("...and spawns inside it still do",
          call("graph_guardrails", {**spawn("debugger"), **sess}, ceil)[0], "deny")
    counter.write_text(json.dumps({"spawns": 99, "agent:debugger": 99}), encoding="utf-8")
    check("a counter with no timestamps cannot be windowed, so it does not deny",
          call("graph_guardrails", {**spawn("debugger"), **sess}, ceil)[0], None)

    # G3 — round ceiling, isolated from G2 so the total is not what trips it. Same specialist over
    # and over is the signature of a loop that is not converging.
    rounds = mkproj({"git": {"optInPrefix": "ROUNDS"},
                     "graphGuardrails": {"maxSpawnsPerSession": 99, "maxRoundsPerAgent": 2}})
    sess = {"session_id": "ceil-g3"}
    for i in range(2):
        check(f"round {i + 1}/2 of the same specialist is fine",
              call("graph_guardrails", {**spawn("debugger"), **sess}, rounds)[0], None)
    check("the 3rd round of the same specialist is refused",
          call("graph_guardrails", {**spawn("debugger"), **sess}, rounds)[0], "deny")
    check("...while a different specialist still runs, well under the total",
          call("graph_guardrails", {**spawn("explorer"), **sess}, rounds)[0], None)
    check("...and the opt-in key releases the round ceiling too",
          call("graph_guardrails", {**spawn("debugger"), **sess}, rounds,
               env={"ROUNDS_ALLOW_SPAWN_OVER": "1"})[0], None)

    # One specialist, one counter, whichever way the caller spelled the name. A plugin agent is
    # addressed `<plugin>:<agent>`, and the bare form still reaches the same agent, so counted
    # verbatim the two spellings were two counters and the ceiling granted double the rounds —
    # seen in this repository's own log as `agent:evaluator: 1` beside
    # `agent:graph-powers:evaluator: 3` during the bare-to-namespaced migration.
    ns = {"session_id": "ceil-namespaced"}
    check("round 1 under the namespaced name",
          call("graph_guardrails", {**spawn("graph-powers:debugger"), **ns}, rounds)[0], None)
    check("round 2 under the bare name — same specialist",
          call("graph_guardrails", {**spawn("debugger"), **ns}, rounds)[0], None)
    check("...so the 3rd, whichever spelling, is refused",
          call("graph_guardrails", {**spawn("graph-powers:debugger"), **ns}, rounds)[0], "deny")

    # G4 — write lease. The half that IS implementable: "touch only the files you declared".
    check("with no lease on disk the check stands down",
          call("graph_guardrails", write_to("anything.ts"), ceil)[0], None)
    lease = ceil / ".graph-powers" / "logs" / "write-lease.json"
    lease.parent.mkdir(parents=True, exist_ok=True)
    lease.write_text(json.dumps(["src/owned.ts", "docs/"]), encoding="utf-8")
    check("a write inside the lease is allowed",
          call("graph_guardrails", write_to("src/owned.ts"), ceil)[0], None)
    check("a write inside a leased directory is allowed",
          call("graph_guardrails", write_to("docs/notes.md"), ceil)[0], None)
    check("a write outside the lease is refused",
          call("graph_guardrails", write_to("src/someone-elses.ts"), ceil)[0], "deny")
    check("...and the opt-in key releases it",
          call("graph_guardrails", write_to("src/someone-elses.ts"), ceil,
               env={"CEIL_ALLOW_OFF_LEASE": "1"})[0], None)
    lease.write_text(json.dumps({"paths": ["src/owned.ts"]}), encoding="utf-8")
    check("the object form of the lease works too",
          call("graph_guardrails", write_to("src/owned.ts"), ceil)[0], None)
    lease.write_text("{ not json", encoding="utf-8")
    check("a corrupt lease stands down rather than denying everything",
          call("graph_guardrails", write_to("src/owned.ts"), ceil)[0], None)
    lease.unlink()

    print("### The pre-commit audit is the project's to declare, never the plugin's to choose")
    # This hook replaced one that fetched and executed a pinned third-party tool from the network
    # before every commit, in every repository that installed the plugin. The property proved here
    # is the new default: a project that declared nothing runs nothing.
    silent = mkproj({"git": {"optInPrefix": "SILENT"}})
    failing = mkproj({"git": {"optInPrefix": "AUDITED"},
                      "gates": {"preCommitAudit": {"command": "exit 3"}}})
    passing = mkproj({"git": {"optInPrefix": "AUDITED"},
                      "gates": {"preCommitAudit": "exit 0"}})
    broken = mkproj({"git": {"optInPrefix": "AUDITED"},
                     "gates": {"preCommitAudit": {"command": "no-such-binary-anywhere --x"}}})
    audit_key = {"tool_name": "Bash",
                 "tool_input": {"command": "AUDITED_ALLOW_AUDIT=1 " + GIT_WRITE}}
    read_only = {"tool_name": "Bash", "tool_input": {"command": "git status"}}

    check("no audit declared: the commit is not touched",
          call("commit_audit_gate", commit, silent)[1], 0)
    check("a declared audit that fails blocks it",
          call("commit_audit_gate", commit, failing)[1], 2)
    check("a declared audit that passes lets it through",
          call("commit_audit_gate", commit, passing)[1], 0)
    check("the opt-in key releases one call",
          call("commit_audit_gate", audit_key, failing)[1], 0)
    check("an audit that cannot run fails open, never closed",
          call("commit_audit_gate", commit, broken)[1], 0)
    check("a read-only git command never triggers the audit",
          call("commit_audit_gate", read_only, failing)[1], 0)

    print("### Auto-update — throttled, silent, and never on the session's critical path")
    upd_home = Path(tempfile.mkdtemp(prefix="gp-home-"))
    (upd_home / ".graph-powers").mkdir(parents=True)
    state = upd_home / ".graph-powers/update-state.json"

    off = mkproj({"git": {"optInPrefix": "OFF"}, "autoUpdate": {"enabled": False}})
    out, code = call_raw("auto_update", {"source": "startup"}, off, env={"HOME": str(upd_home)})
    check("disabled: exits 0", code, 0)
    check("disabled: writes no state at all", state.exists(), False)

    # A check that just ran must not run again on the next session start. Without the throttle
    # every session pays for a registry lookup, which is how a background task becomes the reason
    # somebody uninstalls the thing that schedules it.
    fresh = mkproj({"git": {"optInPrefix": "FRESH"}, "autoUpdate": {"intervalHours": 24}})
    state.write_text(json.dumps({"lastCheck": time.time()}), encoding="utf-8")
    before = state.read_text(encoding="utf-8")
    out, code = call_raw("auto_update", {"source": "startup"}, fresh, env={"HOME": str(upd_home)})
    check("inside the interval: exits 0", code, 0)
    check("inside the interval: the throttle file is untouched",
          state.read_text(encoding="utf-8"), before)

    # An update nobody is told about is indistinguishable from no update: the session keeps
    # running the old files and the person keeps reporting the old behaviour.
    state.write_text(json.dumps({"lastCheck": time.time(),
                                 "pendingNotice": "[graph-powers] updated to 9.9.9"}),
                     encoding="utf-8")
    out, code = call_raw("auto_update", {"source": "startup"}, fresh, env={"HOME": str(upd_home)})
    check("a finished update is announced once", "9.9.9" in out, True)
    out2, _ = call_raw("auto_update", {"source": "startup"}, fresh, env={"HOME": str(upd_home)})
    check("...and not a second time", "9.9.9" in out2, False)

    for d in (silent, failing, passing, broken, off, fresh):
        shutil.rmtree(d, ignore_errors=True)
    shutil.rmtree(upd_home, ignore_errors=True)

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
                 "protect_files", "smart_bash_approver", "session_context", "notify",
                 "commit_audit_gate", "auto_update"):
        r = subprocess.run(
            [sys.executable, str(HOOKS / f"{hook}.py")],
            input="this is not json", capture_output=True, encoding="utf-8", errors="replace",
            env={**os.environ, "CLAUDE_PROJECT_DIR": str(a)}, timeout=30, check=False,
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

    print("### Declared is not installed — the session says so instead of pretending")
    # `ABSENT` cannot resolve on any machine; `sys.executable` resolves on every machine the
    # suite runs on, which is what makes the mirrored case meaningful rather than decorative.
    ABSENT = "gp-no-such-formatter-xyz"
    here = Path(sys.executable).name
    installed = mkproj({"project": {"name": "demo"},
                        "tooling": {"commands": {"lint": f"{here} -c pass", "test": "echo t"}}})
    absent = mkproj({"project": {"name": "demo"},
                     "tooling": {"commands": {"lint": f"{ABSENT} .", "test": "echo t"}}})
    indirect = mkproj({"project": {"name": "demo"},
                       "tooling": {"commands": {"lint": "npm run lint", "test": "echo t"}}})
    start = {"hook_event_name": "SessionStart", "source": "startup"}

    def tag(proj: Path, harness: str = "claude") -> str:
        out, _ = call_raw("session_context", start, proj, harness=harness)
        try:
            return json.loads(out)["hookSpecificOutput"]["additionalContext"]
        except Exception:
            return out.strip()

    check("an installed linter is listed as a gate", "lint" in tag(installed).split("gates: ")[-1], True)
    check("...and nothing is reported missing", "NOT INSTALLED" in tag(installed), False)
    check("an absent linter is dropped from the gate list",
          "lint" in tag(absent).split("gates: ")[-1].split(" |")[0], False)
    check("...and it is named, with the tool", ABSENT in tag(absent), True)
    # `npm run lint` hides the tool in the project's manifest. Guessing it would produce a
    # confident wrong warning, which is worse than the silence.
    check("a package-manager command makes no claim either way",
          "NOT INSTALLED" in tag(indirect), False)
    check("...and still counts as a declared gate", "lint" in tag(indirect), True)

    # Codex passes `cwd` in the payload and exports no CLAUDE_PROJECT_DIR. This hook read the
    # payload and then resolved the project without it, so the tag described whatever repository
    # the hook process started in.
    check("codex resolves the project from the payload", "DEMO" in tag(absent, harness="codex"), True)

    print("### ultracite — a tool that is not installed skips, and never blocks")
    marker = absent / "formatted.txt"
    writer = absent / "fmt.py"
    writer.write_text("import sys,pathlib\n"
                      "pathlib.Path(sys.argv[0]).with_name('formatted.txt').write_text('ran')\n",
                      encoding="utf-8")
    target = absent / "src.ts"
    target.write_text("const x=1\n", encoding="utf-8")
    edit = {"hook_event_name": "PostToolUse", "tool_name": "Write",
            "tool_input": {"file_path": str(target)}}

    fmt_absent = mkproj({"tooling": {"commands": {"format": f"{ABSENT} --write"}}})
    _, rc = call_raw("ultracite", edit, fmt_absent)
    check("a missing formatter exits 0", rc, 0)
    check("...and formats nothing", marker.exists(), False)

    fmt_real = mkproj({"tooling": {"commands": {"format": f"{here} {writer}"}}})
    call_raw("ultracite", edit, fmt_real)
    check("an installed formatter is actually invoked", marker.exists(), True)

    stop_absent = mkproj({"tooling": {"commands": {"lint": f"{ABSENT} ."}}})
    out, rc = call_raw("ultracite", {"hook_event_name": "Stop"}, stop_absent)
    check("a missing linter exits 0 at Stop", rc, 0)
    check("...and does not block the stop", "block" in out, False)

    # ── User-scope config: a decision the operator makes once, for every repository ──────────
    #
    # Before this layer existed, `autonomy` was reachable only from inside a repository that
    # carried the block, so a person who had turned approvals off re-met the prompt flood in the
    # next clone. These cases pin the four things that make the layer safe rather than merely
    # convenient: it applies, the project outranks it, `git` never crosses, and a broken file is
    # still fail-open.
    print("\nUser-scope config")

    def mkhome(cfg: dict) -> Path:
        h = Path(tempfile.mkdtemp(prefix="gp-home-"))
        (h / ".graph-powers").mkdir(parents=True)
        (h / ".graph-powers" / "config.json").write_text(json.dumps(cfg), encoding="utf-8")
        return h

    def as_home(h: Path) -> dict:
        # POSIX resolves ~ through HOME, Windows through USERPROFILE. Setting both is what makes
        # this case run on every machine instead of only on the author's.
        return {"HOME": str(h), "USERPROFILE": str(h)}

    read_cmd = {"hook_event_name": "PreToolUse", "tool_name": "Bash",
                "tool_input": {"command": "printf hello"}}

    home_auto = mkhome({"autonomy": {"level": "autonomous"}})
    bare = Path(tempfile.mkdtemp(prefix="gp-bare-"))  # a clone with no Graph Powers config at all
    d, _ = call("smart_bash_approver", read_cmd, bare, env=as_home(home_auto))
    check("user autonomy reaches a project that declares nothing", d, "allow")

    home_none = Path(tempfile.mkdtemp(prefix="gp-home-empty-"))
    d, _ = call("smart_bash_approver", read_cmd, bare, env=as_home(home_none))
    check("...and without it that same project is still guarded", d, "ask")

    # The project outranks the person: a repository that ships `guarded` keeps it, even for an
    # operator whose personal posture is looser. Relaxing somebody else's repository from a home
    # directory is the one direction this layer must not travel.
    strict = mkproj({"autonomy": {"level": "guarded"}})
    d, _ = call("smart_bash_approver", read_cmd, strict, env=as_home(home_auto))
    check("a project's guarded setting outranks user autonomy", d, "ask")

    # `git` never crosses. A user-level prefix would make an approval typed in one repository
    # release the same gate in every other one — the isolation the two-project cases above prove.
    home_git = mkhome({"git": {"optInPrefix": "HOMEKEY"}})
    commit = {"hook_event_name": "PreToolUse", "tool_name": "Bash",
              "tool_input": {"command": "HOMEKEY_ALLOW_COMMIT=1 " + GIT_WRITE}}
    d, _ = call("git_commit_gate", commit, bare, env=as_home(home_git))
    check("a user-level optInPrefix does not release the commit gate", d, "deny")

    # Cardinal 3 through two layers: the user's typo must not take the session down, and must not
    # take the project's own config down with it.
    home_broken = Path(tempfile.mkdtemp(prefix="gp-home-bad-"))
    (home_broken / ".graph-powers").mkdir(parents=True)
    (home_broken / ".graph-powers" / "config.json").write_text("{ not json", encoding="utf-8")
    d, rc = call("smart_bash_approver", read_cmd, a, env=as_home(home_broken))
    check("a malformed user config exits 0", rc, 0)
    check("...and the project's own config still decides", d, "ask")

    for d_ in (home_auto, home_none, home_git, home_broken, bare, strict, EMPTY_HOME):
        shutil.rmtree(d_, ignore_errors=True)

    for d in (a, b, legacy, no_config, guarded, auton, partial, pm_free, pm_bun, pm_npx, pm_both,
              installed, absent, indirect, fmt_absent, fmt_real, stop_absent):
        shutil.rmtree(d, ignore_errors=True)

    print("\n" + ("FAILURES: " + ", ".join(FAILS) if FAILS else "EVERY GUARANTEE HELD"))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
