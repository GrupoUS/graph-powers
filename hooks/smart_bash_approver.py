#!/usr/bin/env python3
"""smart_bash_approver.py - how much runs without stopping to ask.

Trigger: PreToolUse (Bash). Reads a JSON payload on stdin, writes a decision.

One question sorts every command: **does git undo it?**

  DESTRUCTIVE FLOOR   always denied while `autonomy.destructiveFloor` holds — what git cannot undo.
                      That includes the git subcommands that destroy uncommitted or unreachable
                      work: `clean -f`, `reset --hard`, `stash drop`, `reflog expire`, `gc
                      --prune=now`, `filter-branch`. Deleting a tracked file is NOT here: git
                      restores it.
  KNOWN SAFE          always allowed: reads, inspections, build artefacts, the project's tooling,
                      and the git subcommands the reflog undoes.
  EVERYTHING ELSE     `autonomy.bashDefault`. Under `guarded` it asks; under `autonomous` it runs.

Two rules keep the lists honest, and both were violated before this was rewritten:

  - **Reversible does not ask.** Asking before `git add` or before deleting `__pycache__` spends the
    user's attention on something `git reset` and a rebuild undo for free. Prompts that buy nothing
    are what teach people to stop reading them.
  - **One owner per decision.** A command another hook of this plugin gates is not this hook's to
    judge. `git commit` is `git_commit_gate`; `git push` is `git_push_gate`; landing on a protected
    branch is `git_branch_gate`. Asking here as well produced two prompts for one decision.

Fail-open, like every hook here: an unreadable config resolves to the guarded defaults rather than
taking the session down.
"""

import json
import re
import sys
import typing
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _config as gp

# The payload arrives on stdin as UTF-8, but Python decodes it with the locale code page unless
# told otherwise — cp1252 on a Windows machine. A file path or a branch name outside that page
# then raises `UnicodeDecodeError`, every hook here falls open, and `protect_files` permits a
# write it was meant to refuse. Reconfiguring costs nothing and is guarded because a stdin that
# is already detached has no `reconfigure`.
try:
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
except Exception:
    pass


LEADING_CD_PATTERN = re.compile(r"^cd\s+[^&;]+\s+&&\s+")


def normalize_command(raw_command: str) -> str:
    command = raw_command.strip()

    while True:
        normalized = LEADING_CD_PATTERN.sub("", command, count=1).strip()
        if normalized == command:
            return command
        command = normalized


# ── Dangerous patterns (always block) ──
DANGEROUS_PATTERNS = [
    # Destructive shell operations
    re.compile(r"^rm -rf /"),
    re.compile(r"^rm -rf ~"),
    re.compile(r"^rm -rf \$HOME"),
    re.compile(r"^:\(\)\{ :\|:& \};:"),
    re.compile(r"^chmod -R 777 /"),
    re.compile(r"^dd if=.*of=/dev/"),
    re.compile(r"^> /dev/sd"),
    re.compile(r"^sudo rm"),
    re.compile(r"^truncate -s 0"),
    re.compile(r"^> /etc/"),
    re.compile(r"^mkfs"),
    re.compile(r"^dd if=/dev/zero"),
    re.compile(r"rm --no-preserve-root"),
    re.compile(r"chmod -R 000"),
    # Database destructive commands
    re.compile(r"^DROP DATABASE", re.IGNORECASE),
    re.compile(r"^DROP TABLE", re.IGNORECASE),
    re.compile(r"^TRUNCATE", re.IGNORECASE),
    # A force-push rewrites history for everyone who already pulled it.
    re.compile(r"^git\s+push\b.*(--force|-f)\b"),
    # Git subcommands git itself cannot undo: they destroy uncommitted or unreachable work. These
    # were reaching `ask` under `guarded` and running unannounced under `autonomous` — the widest
    # hole this floor had, because the floor was written as if every `git` verb were recoverable.
    re.compile(r"^git\s+clean\b[^|;&]*(\s-\w*f|\s--force)"),
    re.compile(r"^git\s+reset\b[^|;&]*\s--hard\b"),
    re.compile(r"^git\s+stash\s+(drop|clear)\b"),
    re.compile(r"^git\s+reflog\s+(expire|delete)\b"),
    re.compile(r"^git\s+gc\b[^|;&]*--prune=now"),
    re.compile(r"^git\s+(filter-branch|filter-repo)\b"),
    re.compile(r"^git\s+update-ref\s+-d\b"),
    re.compile(r"^git\s+branch\b[^|;&]*\s-D\b"),
]

# ── The same categories, in the grammar Windows shells speak ─────────────────
# Everything above describes POSIX. On a machine whose Bash tool maps to PowerShell or cmd, none
# of it matches, so `Remove-Item -Recurse -Force C:\` fell through every list to `bashDefault` —
# which under `autonomous` is **allow**. The floor this file promises is "always denied" did not
# exist on that platform, and the mirror image was just as bad: `Get-ChildItem`, a pure read, fell
# through to `ask`. Windows got prompted for the harmless and waved through the catastrophic.
#
# These are appended rather than merged so the POSIX lists stay readable as POSIX, and so the
# split between "floor" and "cleanup" is the same on both sides: deleting a whole drive is the
# floor, `Remove-Item -Recurse .\dist` is cleanup.
_WIN_ROOT = r"(?:[A-Za-z]:\\?|\$env:SystemDrive|\$env:USERPROFILE|\$HOME|%USERPROFILE%|%SystemRoot%)"
DANGEROUS_PATTERNS += [
    # Deleting a drive root or the whole user profile.
    re.compile(rf"(?i)^\s*(remove-item|ri|rm|del|erase|rd|rmdir)\b[^|;&]*\s{_WIN_ROOT}\s*$"),
    # Formatting, repartitioning, wiping free space, or destroying shadow copies.
    re.compile(r"(?i)^\s*format\s+[A-Za-z]:"),
    re.compile(r"(?i)^\s*(diskpart|clear-disk|format-volume|initialize-disk|remove-partition)\b"),
    re.compile(r"(?i)^\s*vssadmin\s+delete\s+shadows\b"),
    re.compile(r"(?i)^\s*cipher\s+/w"),
    # Boot configuration, and handing everyone write access.
    re.compile(r"(?i)^\s*bcdedit\b"),
    re.compile(r"(?i)\bicacls\b[^|;&]*\s/grant\b[^|;&]*\beveryone\b"),
    # Turning off the execution policy is not a build step.
    re.compile(r"(?i)^\s*set-executionpolicy\b[^|;&]*\bbypass\b"),
]

# ── Build artefacts: never versioned, always regenerated by the build that needs them ──
# Checked before CLEANUP, so the generic `rm -r` below does not swallow them. Asking before a
# `__pycache__` delete costs a prompt and protects nothing — the directory is reproduced by the
# next run, and no repository tracks it.
BUILD_ARTIFACT_PATTERNS = [
    re.compile(r"\.turbo(/|$)"),
    re.compile(r"\.old_modules"),
    re.compile(r"\.sisyphus/.*\.log"),
    re.compile(r"node_modules[\\/]\.cache"),
    re.compile(r"__pycache__"),
    re.compile(r"\.pytest_cache"),
    re.compile(r"\.ruff_cache"),
    re.compile(r"\.mypy_cache"),
    re.compile(r"\.next[\\/]cache"),
    re.compile(r"\.nuxt(/|$)"),
    re.compile(r"\.svelte-kit(/|$)"),
    re.compile(r"\.astro(/|$)"),
    re.compile(r"\.vite(/|$)"),
    re.compile(r"dist[\\/].*\.log"),
    re.compile(r"coverage(/|$)"),
]

# ── Cleanup: a recursive delete this hook cannot vouch for. The net, not the catalogue. ──
CLEANUP_PATTERNS = [
    re.compile(r"(^|\s)rm\s+-rf\s+"),
    re.compile(r"(^|\s)rm\s+-r\s+"),
    # The Windows spellings of the same thing: a recursive delete this hook cannot vouch for.
    re.compile(r"(?i)(^|[\s;&|])(remove-item|ri)\b[^|;&]*\s-(recurse|r)\b"),
    re.compile(r"(?i)(^|[\s;&|])(rd|rmdir)\b[^|;&]*\s/s\b"),
    re.compile(r"(?i)(^|[\s;&|])del\b[^|;&]*\s/s\b"),
]

# ── Safe patterns (auto-approve) ──
SAFE_PATTERNS = [
    # Git read commands only
    re.compile(r"^git( --no-pager)? status(\s|$)"),
    re.compile(r"^git( --no-pager)? diff(\s|$)"),
    re.compile(r"^git( --no-pager)? log(\s|$)"),
    re.compile(r"^git( --no-pager)? branch(\s+(-a|-r|-v|-vv|--show-current))*\s*$"),
    re.compile(r"^git( --no-pager)? fetch(\s|$)"),
    re.compile(r"^git( --no-pager)? show(\s|$)"),
    re.compile(r"^git( --no-pager)? stash (list|show)(\s|$)"),
    re.compile(r"^git( --no-pager)? remote(\s|$)"),
    re.compile(r"^git( --no-pager)? reflog(\s|$)"),
    re.compile(r"^git( --no-pager)? rev-parse(\s|$)"),
    re.compile(r"^git( --no-pager)? blame(\s|$)"),
    re.compile(r"^git( --no-pager)? grep(\s|$)"),
    # Reversible git. The reflog or a plain `git reset` undoes every one of these, so a prompt
    # here buys nothing. The three that git does NOT undo — commit, push, landing on a protected
    # branch — are refused by their own dedicated hooks, which is the owner of that decision.
    re.compile(r"^git( --no-pager)? add(\s|$)"),
    re.compile(r"^git( --no-pager)? (merge|rebase|cherry-pick|revert)(\s|$)"),
    re.compile(r"^git( --no-pager)? pull(\s|$)"),
    re.compile(r"^git( --no-pager)? reset(\s|$)"),      # `--hard` is caught by the floor above
    re.compile(r"^git( --no-pager)? stash(\s|$)"),      # `drop`/`clear` caught by the floor above
    re.compile(r"^git( --no-pager)? restore\s+--staged(\s|$)"),
    re.compile(r"^git( --no-pager)? (tag|worktree|describe|shortlog|bisect|notes)(\s|$)"),
    # Owned by a dedicated hook, so this one does not get a second vote. Claude Code merges
    # PreToolUse decisions by "most restrictive wins" — `deny` > `defer` > `ask` > `allow`, with
    # every matching hook run to completion in parallel — so `git_commit_gate`, `git_push_gate`
    # and `git_branch_gate` still refuse exactly what they refused before. What disappears is the
    # second prompt for the same decision, which is the one nobody was reading.
    re.compile(r"^git( --no-pager)? (commit|push|checkout|switch)(\s|$)"),
    re.compile(r"^gh pr (view|list|status)(\s|$)"),
    re.compile(r"^gh (pr|issue) create(\s|$)"),
    re.compile(r"^gh run (view|list)(\s|$)"),
    re.compile(r"^gh issue (view|list)(\s|$)"),
    re.compile(r"^gh repo view(\s|$)"),
    # Filesystem read
    re.compile(r"^ls(\s|$)"),
    re.compile(r"^cat "),
    re.compile(r"^head "),
    re.compile(r"^tail "),
    re.compile(r"^grep "),
    re.compile(r"^rg "),
    re.compile(r"^find "),
    re.compile(r"^which "),
    re.compile(r"^pwd$"),
    re.compile(r"^echo "),
    re.compile(r"^tree(\s|$)"),
    re.compile(r"^stat "),
    re.compile(r"^wc -"),
    re.compile(r"^cut "),
    re.compile(r"^sort "),
    re.compile(r"^uniq "),
    re.compile(r"^column -t"),
    re.compile(r"^less "),
    re.compile(r"^more "),
    # Toolchain binaries that are not package managers (those are handled by PACKAGE_MANAGER_RE
    # below, which covers every manager instead of naming one — a plugin that hardcodes `bun`
    # asks a pnpm project for permission it never asks a bun project for).
    re.compile(r"^tsgo(\s|$)"),
    re.compile(r"^tsc(\s|$)"),
    re.compile(r'^python(3)?( -X [^ ]+)? "?\.claude[\\/]'),
    re.compile(r'^python(3)?( -X [^ ]+)? "?scripts[\\/]'),
    re.compile(r'^py -3 "?\.claude[\\/]'),
    re.compile(r'^py -3 "?scripts[\\/]'),
    # Optional local CLIs (read-only introspection)
    re.compile(r"^(psql|mysql|sqlite3) "),
    # Version checks (Bun-only for package managers)
    re.compile(r"^(python3?|bun|node|deno|docker|git|tsgo|tsc) --version"),
    # Local reversible filesystem helpers
    re.compile(r"^mkdir -p"),
    re.compile(r"^touch "),
    re.compile(r"^cp (-r )?"),
    re.compile(r"^mv "),          # tracked file: git restores it. Untracked: it still exists
    re.compile(r"^chown "),
    re.compile(r"^ln -s"),
    re.compile(r"^rsync\b(?![^|;&]*--delete)"),   # additive; `--delete` falls through to the default
    re.compile(r"^chmod \+x"),
    re.compile(r"^chmod (755|644)"),
    # Process / system read
    re.compile(r"^ps (aux|-ef)"),
    re.compile(r"^(top|htop|free|df|du|uptime|whoami|id) "),
    re.compile(r"^(free|df|du|uptime|whoami|id)$"),
    # Network read
    re.compile(r"^curl -"),
    re.compile(r"^wget -"),
    re.compile(r"^ping -"),
    re.compile(r"^(ssh -V|nc -zv|telnet)"),
    # Build / lint tools
    re.compile(r"^biome(\s|$)"),
    re.compile(r"^vite --version"),
    # PowerShell and cmd reads. Without these every inspection on Windows fell through to the
    # default and asked — the prompt-fatigue this file's docstring exists to avoid.
    re.compile(r"(?i)^(get-childitem|gci|dir)(\s|$)"),
    re.compile(r"(?i)^(get-content|gc|type)(\s|$)"),
    re.compile(r"(?i)^(select-string|findstr)(\s|$)"),
    re.compile(r"(?i)^(test-path|get-location|get-item|get-command|measure-object|write-output)(\s|$)"),
    re.compile(r"(?i)^(where\.exe|resolve-path|split-path|join-path)(\s|$)"),
    re.compile(r"(?i)^new-item\b[^|;&]*-itemtype\s+directory"),
    re.compile(r"(?i)^(copy-item|move-item|set-location|push-location|pop-location)(\s|$)"),
    re.compile(r"(?i)^py\s+-3(\s|$)"),
]

# What is left after the two rules in the docstring: state-changing, owned by nobody else, and not
# undone by git. Everything that used to be here for being merely *unfamiliar* was moved out — an
# `ask` that the user always answers the same way is a prompt that trains them not to read prompts.
ASK_PATTERNS = [
    # Discards uncommitted work in the working tree, and has no dedicated gate.
    # `restore --staged` is only an unstage, and is allowed above.
    re.compile(r"^git\s+restore\b"),
    # `clean -f` is on the floor; what remains here is the dry run and the ambiguous form.
    re.compile(r"^git\s+clean\b"),
]

# Any package manager. Which ones a project accepts is `autonomy.allowPackageManagers`; by default
# all of them do, because a plugin that hardcodes one breaks every project that chose another.
PACKAGE_MANAGER_RE = re.compile(r"^(bun|bunx|npm|npx|pnpm|pnpx|yarn|corepack|uv|uvx|pip|pipx|poetry|cargo|go)\b")
DANGEROUS_PM_PATTERN = re.compile(r"(rm -rf|cache clean|publish.*--force)")
COMMAND_SEPARATOR_PATTERN = re.compile(r"\s*(?:&&|\|\||;)\s*")


def read_input() -> dict[str, object]:
    try:
        raw = sys.stdin.read()
        return typing.cast(dict[str, object], json.loads(raw)) if raw.strip() else {}
    except Exception:
        return {}


def _allow() -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "allow",
                }
            }
        )
    )


def _deny(reason: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
        )
    )


def _ask(reason: str | None = None) -> None:
    payload: dict[str, object] = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
        }
    }
    if reason:
        typing.cast(dict[str, object], payload["hookSpecificOutput"])[
            "permissionDecisionReason"
        ] = reason
    print(json.dumps(payload))


def _matches(patterns: list[re.Pattern[str]], command: str) -> bool:
    return any(pattern.search(command) for pattern in patterns)


def _classify(command: str, policy: dict[str, typing.Any]) -> tuple[str, str | None]:
    """Return (allow|ask|deny, optional reason) for one shell segment.

    `policy` is whatever `_config.autonomy()` resolved: strings for the decisions, a bool for
    the destructive floor, a list for the package managers. Typing it as `object` made every
    `return policy[...]` a type error against the declared `tuple[str, str | None]`.
    """
    if policy["destructiveFloor"] and _matches(DANGEROUS_PATTERNS, command):
        return (
            "deny",
            "BLOCKED: Dangerous, non-Bun, or branch-protected command detected",
        )

    if _matches(BUILD_ARTIFACT_PATTERNS, command):
        return "allow", None

    if _matches(CLEANUP_PATTERNS, command):
        return policy["cleanup"], (
            None if policy["cleanup"] == "allow" else "Cleanup operation — requires approval"
        )

    if _matches(SAFE_PATTERNS, command):
        if PACKAGE_MANAGER_RE.match(command) and DANGEROUS_PM_PATTERN.search(command):
            return "deny", "BLOCKED: destructive package-manager command"
        return "allow", None

    if _matches(ASK_PATTERNS, command):
        return policy["bashDefault"], (
            None if policy["bashDefault"] == "allow"
            else "State-changing or external command — requires approval"
        )

    if PACKAGE_MANAGER_RE.match(command):
        if DANGEROUS_PM_PATTERN.search(command):
            return "deny", "BLOCKED: destructive package-manager command"
        return "allow", None

    return policy["bashDefault"], None


def main() -> None:
    data: dict[str, object] = read_input()
    command: str = normalize_command(
        str(
            data.get("command")
            or typing.cast(dict[str, object], data.get("tool_input", {})).get(
                "command", ""
            )
        )
    )

    if not command:
        _ask()
        return

    policy = gp.autonomy(gp.load(payload=data))

    # A project that declares which package managers it accepts gets the others refused — a
    # lockfile that forks is a real defect. A project that declares none accepts all of them.
    allowed_pms = policy.get("allowPackageManagers") or []
    if allowed_pms:
        pm = PACKAGE_MANAGER_RE.match(command)
        if pm and pm.group(1) not in allowed_pms:
            _deny(
                f"BLOCKED: this project declares its package managers as "
                f"{', '.join(allowed_pms)}; `{pm.group(1)}` is not one of them "
                "(autonomy.allowPackageManagers)."
            )
            return

    segments = [
        segment.strip()
        for segment in COMMAND_SEPARATOR_PATTERN.split(command)
        if segment.strip()
    ]

    final_decision = "allow"
    ask_reason: str | None = None
    for segment in segments or [command]:
        decision, reason = _classify(segment, policy)
        if decision == "deny":
            _deny(reason or "BLOCKED: Dangerous command")
            return
        if decision == "ask":
            final_decision = "ask"
            ask_reason = ask_reason or reason

    if final_decision == "allow":
        _allow()
        return

    # Unknown or state-changing commands require user approval. Never fall
    # through to allow — unknown commands may be destructive tools, typos, or
    # untrusted invocations.
    _ask(ask_reason)


if __name__ == "__main__":
    main()
    sys.exit(0)
