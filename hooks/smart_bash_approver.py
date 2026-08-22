#!/usr/bin/env python3
"""smart_bash_approver.py - how much runs without stopping to ask.

Triggers: PreToolUse and PermissionRequest (Bash). Reads a JSON payload on stdin, writes the
decision shape that event accepts.

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
import os
import re
import shlex
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
    # The same class, one pass later. `checkout` reads as navigation, so it was sorted with the
    # branch verbs and handed to `git_branch_gate` — but `git checkout -- <paths>` is not
    # navigation, it is `git clean`'s twin: it overwrites the working tree from the index and the
    # discarded edits exist in no object git can name. `git_branch_gate` returns nothing for it,
    # because its own `target_branch()` gives up as soon as `--` appears, so the form was reaching
    # `allow` with no hook refusing it at all.
    #
    # Each spelling is listed rather than one loose `checkout` pattern, so `git checkout -b feat`
    # and `git checkout main` stay out of the floor and keep their real owner.
    re.compile(r"^git\s+checkout\b[^|;&]*\s--\s"),
    re.compile(r"^git\s+checkout\b[^|;&]*\s(-f|--force)\b"),
    re.compile(r"^git\s+checkout\s+\.(\s|$)"),
    re.compile(r"^git\s+switch\b[^|;&]*\s--discard-changes\b"),
    # `restore` is the modern spelling of the same destruction and was sitting in ASK_PATTERNS,
    # which resolves to `bashDefault` — `allow` under `autonomous`. The staged form is only an
    # unstage and has to stay out of the floor.
    #
    # It is NOT a pattern here, because the exemption is a property of the flag SET and no
    # substring test can read one. The lookahead that used to sit here, `(?![^|;&]*--staged)`,
    # asked whether the text `--staged` appeared anywhere — so `git restore --staged --worktree`
    # was exempted, which overwrites the working tree, while `git restore -SW`, the identical
    # command, was denied. `_git_restore_kind` below answers the real question: is `--staged`/`-S`
    # set AND `--worktree`/`-W` unset.
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
#
# These describe ONE PATH each. They used to be matched with `.search()` against the whole command
# line, which turned every entry into an unconditional permit for any command containing the word:
# `rm -rf ../../important coverage` deleted a path two levels above the repository, and
# `<anything> # __pycache__` ran unprompted. `_is_build_artifact_delete` below is what makes the
# allowance mean what this comment always claimed it meant.
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

# The verbs that delete, in both grammars — same split as every other list in this file.
DELETE_VERBS = frozenset({"rm", "rmdir", "del", "erase", "rd", "remove-item", "ri"})

# A cmd.exe switch (`/s`, `/q`, `/f`) is a flag; `/etc` is an operand. One letter is what tells
# them apart, and treating every `/`-token as a flag is what would have let
# `rd /s /q /home coverage` read as a delete of nothing but artefacts.
_CMD_SWITCH_PATTERN = re.compile(r"^/[A-Za-z]$")


def _is_build_artifact(operand: str) -> bool:
    """True when this ONE operand names a build artefact, at a path-element boundary.

    The boundary check is the difference between `coverage` and `mycoverage-data`: an unanchored
    `.search()` accepted the second, which is a directory this hook knows nothing about.
    """
    for pattern in BUILD_ARTIFACT_PATTERNS:
        found = pattern.search(operand)
        if found and (found.start() == 0 or operand[found.start() - 1] in "/\\"):
            return True
    return False


def _is_build_artifact_delete(command: str) -> bool:
    """True only when the command IS a delete and EVERY operand is a build artefact.

    Both halves are load-bearing. Without the verb the word `coverage` permitted any command that
    contained it; without "every operand" one artefact name at the end of the line permitted the
    paths beside it.

    `posix=` is passed explicitly (cardinal 8): without it `shlex` eats the backslashes in
    `.\\.pytest_cache` on the very platform that writes paths that way. A split that raises means
    this hook cannot read the operands, and a permit it cannot justify is one it does not issue —
    the command falls through to the cleanup rung and the project's policy decides.
    """
    try:
        tokens = shlex.split(command, posix=(os.name != "nt"))
    except Exception:
        return False
    if not tokens:
        return False
    verb = tokens[0].strip("\"'").replace("\\", "/").rsplit("/", 1)[-1].lower()
    verb = verb.removesuffix(".exe")
    if verb not in DELETE_VERBS:
        return False
    operands = [
        token for token in tokens[1:]
        if not token.startswith("-") and not _CMD_SWITCH_PATTERN.match(token)
    ]
    if not operands:
        return False
    return all(_is_build_artifact(operand) for operand in operands)

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
# Every `git` line reaching these lists has already been through `gp.strip_git_global_flags`, so
# the global-option prefix is gone and the verb sits directly after `git`. The optional
# ` --no-pager` group each of these entries used to carry is therefore not merely redundant, it is
# the defect: the floor patterns above never had one, so the two lists disagreed about what
# `git --no-pager reset --hard` was and the more permissive list won. Removing it is what stops
# them drifting apart again — there is now one place where a global flag is described.
SAFE_PATTERNS = [
    # Git read commands only
    re.compile(r"^git status(\s|$)"),
    re.compile(r"^git diff(\s|$)"),
    re.compile(r"^git log(\s|$)"),
    re.compile(r"^git branch(\s+(-a|-r|-v|-vv|--show-current))*\s*$"),
    re.compile(r"^git fetch(\s|$)"),
    re.compile(r"^git show(\s|$)"),
    re.compile(r"^git stash (list|show)(\s|$)"),
    re.compile(r"^git remote(\s|$)"),
    re.compile(r"^git reflog(\s|$)"),
    re.compile(r"^git rev-parse(\s|$)"),
    re.compile(r"^git blame(\s|$)"),
    re.compile(r"^git grep(\s|$)"),
    # Reversible git. The reflog or a plain `git reset` undoes every one of these, so a prompt
    # here buys nothing. The three that git does NOT undo — commit, push, landing on a protected
    # branch — are refused by their own dedicated hooks, which is the owner of that decision.
    re.compile(r"^git add(\s|$)"),
    re.compile(r"^git (merge|rebase|cherry-pick|revert)(\s|$)"),
    re.compile(r"^git pull(\s|$)"),
    re.compile(r"^git reset(\s|$)"),      # `--hard` is caught by the floor above
    re.compile(r"^git stash(\s|$)"),      # `drop`/`clear` caught by the floor above
    # `restore` is NOT a pattern here either. `^git restore\s+--staged` matched
    # `git restore --staged --worktree <path>`, which discards the working tree — the safe list
    # and the floor were reading the same command two different ways. `_git_restore_kind` is the
    # one place that decides it now, and `_classify` consults it for both verdicts.
    re.compile(r"^git (tag|worktree|describe|shortlog|bisect|notes)(\s|$)"),
    # Owned by a dedicated hook, so this one does not get a second vote. Claude Code merges
    # PreToolUse decisions by "most restrictive wins" — `deny` > `defer` > `ask` > `allow`, with
    # every matching hook run to completion in parallel — so `git_commit_gate`, `git_push_gate`
    # and `git_branch_gate` still refuse exactly what they refused before. What disappears is the
    # second prompt for the same decision, which is the one nobody was reading.
    # `checkout` and `switch` are deliberately NOT here. Their branch forms do have a dedicated
    # owner, but their pathspec forms discard the working tree, and no rule this file can write
    # separates `git checkout main` from `git checkout main.py` without asking the filesystem.
    # The unambiguous destructive spellings are on the floor above; the ambiguous remainder is in
    # ASK_PATTERNS, so `guarded` stops and `autonomous` proceeds — which is what the level means.
    re.compile(r"^git (commit|push)(\s|$)"),
    re.compile(r"^gh pr (view|list|status)(\s|$)"),
    re.compile(r"^gh run (view|list)(\s|$)"),
    re.compile(r"^gh issue (view|list)(\s|$)"),
    re.compile(r"^gh repo view(\s|$)"),
    # Filesystem read
    re.compile(r"^ls(\s|$)"),
    # These take an argument or they read stdin, and reading stdin is what they do in a pipeline.
    # The trailing space each of these patterns used to require made the bare form — `… | sort`,
    # `… | uniq`, `… | head` — an unknown command, which mattered from the moment the splitter
    # started judging each stage of a pipeline separately: `cat notes.txt | sort | uniq` asked
    # twice for two reads. Anything that writes (`tee`, `xargs`) is deliberately not here.
    re.compile(r"^cat(\s|$)"),
    re.compile(r"^head(\s|$)"),
    re.compile(r"^tail(\s|$)"),
    re.compile(r"^grep "),
    re.compile(r"^rg "),
    re.compile(r"^find "),
    re.compile(r"^which "),
    re.compile(r"^pwd$"),
    # `(\s|$)` and not a trailing space: cutting a substitution out for separate judgement leaves
    # the enclosing command holding nothing, so `echo $(git rev-parse HEAD)` reaches this list as
    # the bare segment `echo`. A verb that prints its arguments and has none prints a blank line.
    re.compile(r"^echo(\s|$)"),
    re.compile(r"^tree(\s|$)"),
    re.compile(r"^stat "),
    re.compile(r"^wc(\s|$)"),
    re.compile(r"^cut "),
    re.compile(r"^sort(\s|$)"),
    re.compile(r"^uniq(\s|$)"),
    re.compile(r"^column -t"),
    re.compile(r"^less(\s|$)"),
    re.compile(r"^more(\s|$)"),
    # Toolchain binaries that are not package managers (those are handled by PACKAGE_MANAGER_RE
    # below, which covers every manager instead of naming one — a plugin that hardcodes `bun`
    # asks a pnpm project for permission it never asks a bun project for).
    re.compile(r"^tsgo(\s|$)"),
    re.compile(r"^tsc(\s|$)"),
    re.compile(r'^python(3)?( -X [^ ]+)? "?\.claude[\\/]'),
    re.compile(r'^python(3)?( -X [^ ]+)? "?scripts[\\/]'),
    # `py` is the Windows launcher for the two entries above, and it gets the same rule for the
    # same reason: what runs is the argument, not the command. A blanket `^py\s+-3(\s|$)` replaced
    # these two for one release and made `py -3 -c "<anything>"` an allow — an interpreter with no
    # script named is a permit for whatever the model decided to write on the line.
    re.compile(r'^py -3 "?\.claude[\\/]'),
    re.compile(r'^py -3 "?scripts[\\/]'),
    # Which interpreter a session has is a read, and `py` is missing from the version list below
    # because that list names the POSIX spellings.
    re.compile(r"^py -3 (--version|-V)(\s|$)"),
    # Optional local CLIs (read-only introspection)
    re.compile(r"^(psql|mysql|sqlite3) "),
    # Version checks (Bun-only for package managers)
    re.compile(r"^(python3?|bun|node|deno|docker|git|tsgo|tsc) --version"),
    # Local reversible filesystem helpers
    re.compile(r"^mkdir -p"),
    re.compile(r"^touch "),
    re.compile(r"^cp (-r )?"),
    re.compile(r"^mv "),          # tracked file: git restores it. Untracked: it still exists
    re.compile(r"^ln -s"),
    # Local-to-local only. `--delete` and a remote target (`host:path`, `user@host:path`) are both
    # excluded here and land in ASK_PATTERNS: the first removes files, the second is egress.
    re.compile(r"^rsync\b(?![^|;&]*--delete)(?![^|;&]*\s[\w.@-]+:)"),
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
    # `py -3` is NOT here. It was, as a blanket `(?i)^py\s+-3(\s|$)`, and a blanket interpreter is
    # a blanket allow: `py -3 -c "import shutil;shutil.rmtree(...)"` matched it. The launcher's
    # real entries are up beside `python`/`python3` — a script path inside the project, or the
    # version check.
]

# What is left after the two rules in the docstring: state-changing, owned by nobody else, and not
# undone by git. Everything that used to be here for being merely *unfamiliar* was moved out — an
# `ask` that the user always answers the same way is a prompt that trains them not to read prompts.
ASK_PATTERNS = [
    # `restore` and the destructive `checkout`/`switch` spellings moved to the floor: they are not
    # "ask" material, they are unrecoverable. What is left here is the half no pattern can classify
    # — `git checkout <name>` is a branch or a path depending on what exists on disk — plus the
    # dry runs. Ambiguity is exactly what a prompt is for.
    re.compile(r"^git\s+(checkout|switch)\b"),
    # `clean -f` is on the floor; what remains here is the dry run and the ambiguous form.
    re.compile(r"^git\s+clean\b"),
    # No hook in this plugin gates `gh`, and `safety-floor.md §1` requires approval in the turn
    # before anything leaves the machine. It was moved to the safe list as if it had an owner;
    # it does not.
    re.compile(r"^gh\s+(pr|issue)\s+create\b"),
    # Ownership is outside git entirely — the sorting question ("does git undo it?") answers no.
    re.compile(r"^chown\b"),
    # Additive on the destination filesystem, which says nothing about the destination *host*.
    # A remote target is egress of whatever the source contains.
    re.compile(r"^rsync\b[^|;&]*\s[^\s]+:"),
]

# Any package manager. Which ones a project accepts is `autonomy.allowPackageManagers`; by default
# all of them do, because a plugin that hardcodes one breaks every project that chose another.
PACKAGE_MANAGER_RE = re.compile(r"^(bun|bunx|npm|npx|pnpm|pnpx|yarn|corepack|uv|uvx|pip|pipx|poetry|cargo|go)\b")

# A package runner belongs to the manager that ships it, and the allowlist names families.
#
# Without this, a project declaring `["bun"]` had `bunx` refused — bun's own package runner, the
# correct tool there, denied by the rule that exists to keep the project on bun. The message said
# "`bunx` is not one of them" while `bun` sat in the list, which reads as the guardrail being
# broken rather than as a rule being applied.
#
# What the setting protects is the lockfile: `npm install` in a bun project forks it, and that is a
# real defect. Running a package through the manager the project already chose forks nothing. So
# the check resolves the command to its family first — `["bun"]` accepts `bunx` and still refuses
# `npx`, which belongs to npm.
#
# The resolution is one-directional on purpose: listing `npx` does not admit `npm`. A project that
# wants only the runner gets only the runner, and the broader permission stays something you have
# to write down.
#
# `pipx` is the judgment call. It is a separate project rather than pip's own runner, but it
# installs into isolated environments and never touches the project's dependency set, so under a
# `["pip"]` declaration it is in-family for the thing being protected.
PACKAGE_MANAGER_FAMILY = {
    "bunx": "bun",
    "npx": "npm",
    "pnpx": "pnpm",
    "uvx": "uv",
    "pipx": "pip",
}
DANGEROUS_PM_PATTERN = re.compile(r"(rm -rf|cache clean|publish.*--force)")

# Every pattern in this file is `^`-anchored and matched against one segment, so what counts as a
# segment boundary decides what the floor can see at all. This used to be `&&`, `||` and `;` — and
# a shell has more separators than that. A pipe, a newline and a command substitution each put the
# real command somewhere no `^` reached: `echo $(rm -rf $HOME)` and a second line after `echo hi`
# were both **allow**, on a list whose whole purpose is to deny exactly those two commands.
#
# `\r` is in the class because a heredoc written on Windows arrives with CRLF, and a `\r` left at
# the end of a segment defeats every `(\s|$)` that closes a safe pattern.
COMMAND_SEPARATOR_PATTERN = re.compile(r"\s*(?:&&|\|\||;|\||\n|\r)\s*")


def _split_substitutions(text: str) -> tuple[str, list[str]]:
    """Pull `$( … )` and backtick bodies out of a command line.

    Returns the line with each substitution replaced by a space, plus the bodies. A substitution
    IS a command — the shell runs it and pastes its output — so it is judged as one rather than
    read as an argument to the command that encloses it.

    Deliberately not quote-aware, and that is the safe direction: `echo "; rm -rf /"` is read as
    two segments and asks, where a quote-tracking splitter that met one unbalanced quote would
    read the rest of the line as inert text. This file already treated `;` that way.
    """
    outer: list[str] = []
    bodies: list[str] = []
    index = 0
    length = len(text)
    while index < length:
        char = text[index]
        if char == "$" and index + 1 < length and text[index + 1] == "(":
            depth = 1
            scan = index + 2
            while scan < length and depth:
                if text[scan] == "(":
                    depth += 1
                elif text[scan] == ")":
                    depth -= 1
                scan += 1
            # An unclosed `$(` means the rest of the line is the body. Reading it as one is what
            # keeps a truncated or malformed line from becoming an unexamined remainder.
            bodies.append(text[index + 2: scan - 1] if depth == 0 else text[index + 2:])
            outer.append(" ")
            index = scan
            continue
        if char == "`":
            close = text.find("`", index + 1)
            bodies.append(text[index + 1: close] if close != -1 else text[index + 1:])
            outer.append(" ")
            index = close + 1 if close != -1 else length
            continue
        outer.append(char)
        index += 1
    return "".join(outer), bodies


def command_segments(command: str) -> list[str]:
    """Every command the shell would run for this line, each on its own.

    Recursive, because a substitution can contain one. Termination is structural: a body is always
    shorter than the text it was cut out of.
    """
    try:
        outer, bodies = _split_substitutions(command)
        segments = [part.strip() for part in COMMAND_SEPARATOR_PATTERN.split(outer) if part.strip()]
        for body in bodies:
            segments.extend(command_segments(body))
        return segments
    except Exception:
        # Cardinal 3, strict side: an unreadable line is still judged, as one whole segment —
        # which is what this hook did before it could split at all.
        stripped = (command or "").strip()
        return [stripped] if stripped else []


def read_input() -> dict[str, object]:
    try:
        raw = sys.stdin.read()
        return typing.cast(dict[str, object], json.loads(raw)) if raw.strip() else {}
    except Exception:
        return {}


def _emit_decision(
    decision: str,
    reason: str | None = None,
    *,
    event: str = "PreToolUse",
    codex_turn: bool = False,
) -> None:
    """Emit the decision vocabulary accepted by this event and harness.

    Plain PreToolUse `ask` and `allow` decisions are valid in Claude Code but deliberately
    unsupported by Codex (`allow` is accepted there only alongside an input rewrite). Codex marks
    either hook run failed and then continues, creating noise without changing the outcome. A Codex
    payload carries the Codex-specific `turn_id`, so on that path we emit only denials here and let
    the PermissionRequest registration own approval.

    PermissionRequest has a different response shape. Silence means "use the normal approval
    flow"; an allow means Codex proceeds without surfacing the prompt. Keeping classification in
    this one script is the repository's one-thing-one-place rule applied to permissions.
    """
    if event == "PermissionRequest":
        if decision == "ask":
            return
        body: dict[str, object] = {"behavior": decision}
        if reason and decision == "deny":
            body["message"] = reason
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": event,
                        "decision": body,
                    }
                }
            )
        )
        return

    if decision != "deny" and codex_turn:
        return

    specific: dict[str, object] = {
        "hookEventName": "PreToolUse",
        "permissionDecision": decision,
    }
    if reason:
        specific["permissionDecisionReason"] = reason
    print(json.dumps({"hookSpecificOutput": specific}))


def _allow(*, event: str = "PreToolUse", codex_turn: bool = False) -> None:
    _emit_decision("allow", event=event, codex_turn=codex_turn)


def _deny(
    reason: str, *, event: str = "PreToolUse", codex_turn: bool = False
) -> None:
    _emit_decision("deny", reason, event=event, codex_turn=codex_turn)


def _ask(
    reason: str | None = None,
    *,
    event: str = "PreToolUse",
    codex_turn: bool = False,
) -> None:
    _emit_decision("ask", reason, event=event, codex_turn=codex_turn)


def _matches(patterns: list[re.Pattern[str]], command: str) -> bool:
    return any(pattern.search(command) for pattern in patterns)


_GIT_RESTORE_PATTERN = re.compile(r"^git\s+restore\b(.*)$", re.DOTALL)


def _skip_option_value(tokens: list[str], index: int) -> int:
    """Step past the value of an option that takes one — unless it looks like an option itself.

    `git restore -s HEAD~1 --staged x` has to skip `HEAD~1`, or the `~` and the rest get read as
    flag letters. But refusing to skip a token that starts with `-` is what keeps a malformed
    line from hiding a `--worktree` behind an option that was expecting a value.
    """
    if index < len(tokens) and not tokens[index].startswith("-"):
        return index + 1
    return index


def _git_restore_kind(command: str) -> str | None:
    """`unstage`, `worktree`, or None when this is not a `git restore` at all.

    `git restore` writes the index, the working tree, or both, and only the index-only form is
    recoverable — `git add` puts it straight back. Everything else overwrites files whose edits
    exist in no object git can name, which is the floor's definition of what it stops.

    So the question is the flag SET: `--staged`/`-S` present and `--worktree`/`-W` absent. Short
    flags cluster, which is what made the substring test unfixable — `-SW` and `--staged
    --worktree` are the same command and no `in` test sees that.

    Unreadable flags mean `worktree`, not `unstage`: an exemption this hook cannot justify is one
    it does not grant.
    """
    found = _GIT_RESTORE_PATTERN.match(command)
    if found is None:
        return None
    try:
        tokens = shlex.split(found.group(1), posix=(os.name != "nt"))
    except Exception:
        return "worktree"
    staged = False
    worktree = False
    index = 0
    while index < len(tokens):
        token = tokens[index]
        index += 1
        if token == "--":
            break  # everything after this is a pathspec, however it is spelled
        if token.startswith("--"):
            name = token.split("=", 1)[0]
            if name == "--staged":
                staged = True
            elif name == "--worktree":
                worktree = True
            elif name == "--source" and "=" not in token:
                index = _skip_option_value(tokens, index)
            continue
        if token.startswith("-") and len(token) > 1:
            # Short flags cluster: `-SW` is `--staged --worktree`. `-S` is staged, `-W` worktree,
            # and lowercase `-s` is `--source`, which takes the next token as its value.
            letters = token[1:]
            if "S" in letters:
                staged = True
            if "W" in letters:
                worktree = True
            if letters.endswith("s"):
                index = _skip_option_value(tokens, index)
            continue
        # A pathspec. `my---staged-notes.txt` is a filename, not a flag, and reading it as one is
        # exactly what the substring test did.
    return "unstage" if staged and not worktree else "worktree"


def _package_manager_verdict(
    command: str, policy: dict[str, typing.Any]
) -> tuple[str, str | None] | None:
    """How a declared `allowPackageManagers` answers one segment, or None when it has no opinion.

    Two answers, not one. A manager the project did not declare is refused, because that is the
    lockfile fork the setting exists to prevent. A *runner* whose manager was declared is asked,
    not waved through: `bunx <package>` resolves and executes code from a registry that the
    project never named, and the consent on record was about which lockfile to keep — a narrower
    thing than arbitrary execution. Denying it outright was the other error, and the one that
    produced `BLOCKED: ... bunx is not one of them` while `bun` sat in the list.
    """
    allowed = policy.get("allowPackageManagers") or []
    if not allowed:
        return None
    match = PACKAGE_MANAGER_RE.match(command)
    if not match:
        return None
    name = match.group(1)
    if name in allowed:
        return None
    family = PACKAGE_MANAGER_FAMILY.get(name)
    if family in allowed:
        if policy.get("bashDefault") == "allow":
            return "allow", None
        return "ask", (
            f"`{name}` is {family}'s package runner and {family} is declared, so the lockfile is "
            f"safe — but a runner fetches and executes a package this project never named. "
            f"Approve only if you know what `{command.split()[1] if len(command.split()) > 1 else name}` is."
        )
    belongs = f" (`{name}` belongs to `{family}`)" if family else ""
    return "deny", (
        f"BLOCKED: this project declares its package managers as {', '.join(allowed)}; "
        f"`{name}` is not one of them{belongs} (autonomy.allowPackageManagers)."
    )


def _classify(command: str, policy: dict[str, typing.Any]) -> tuple[str, str | None]:
    """Return (allow|ask|deny, optional reason) for one shell segment.

    `policy` is whatever `_config.autonomy()` resolved: strings for the decisions, a bool for
    the destructive floor, a list for the package managers. Typing it as `object` made every
    `return policy[...]` a type error against the declared `tuple[str, str | None]`.
    """
    # Before any list is consulted, and for all of them at once. A prefix of git global options is
    # not part of any rule written below — every rule is about the verb — but it used to be part of
    # the *matching*, and inconsistently: the floor anchored on `^git\s+<verb>` and the safe list
    # allowed an optional ` --no-pager`, so `git --no-pager reset --hard` fell out of the floor and
    # into the safe list. `gp.strip_git_global_flags` is the one description of that prefix.
    command = gp.strip_git_global_flags(command)

    # `git restore` is the one verb whose verdict depends on a flag set rather than on a shape, so
    # it is resolved once here and consulted by the floor below and by the safe rung further down.
    restore_kind = _git_restore_kind(command)

    if policy["destructiveFloor"] and (
        _matches(DANGEROUS_PATTERNS, command) or restore_kind == "worktree"
    ):
        return (
            "deny",
            "BLOCKED: Dangerous, non-Bun, or branch-protected command detected",
        )

    # Per segment, not per command line. This check used to run once in `main()` against the whole
    # string, so it only ever saw the first word: `npm install` was refused and
    # `echo ok && npm install` was allowed, which is the refusal defeated by one prefix.
    verdict = _package_manager_verdict(command, policy)
    if verdict:
        return verdict

    if _is_build_artifact_delete(command):
        return "allow", None

    if _matches(CLEANUP_PATTERNS, command):
        return policy["cleanup"], (
            None if policy["cleanup"] == "allow" else "Cleanup operation — requires approval"
        )

    # The index-only restore, at the rung the `^git restore --staged` pattern used to occupy. It
    # is an unstage: `git add` puts it straight back, so a prompt buys nothing.
    if restore_kind == "unstage":
        return "allow", None

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
    event = str(data.get("hook_event_name") or "PreToolUse")
    codex_turn = bool(data.get("turn_id"))
    command: str = normalize_command(
        str(
            data.get("command")
            or typing.cast(dict[str, object], data.get("tool_input", {})).get(
                "command", ""
            )
        )
    )

    if not command:
        # No opinion, not an approval request. The `Bash` matcher is a regex the harness applies by
        # substring, so this hook is also handed `BashOutput` and `KillBash` — payloads that carry a
        # shell id and no command line. Asking about them produced a confirmation prompt per poll of
        # a background shell, attributed to this plugin and citing a command that was never there:
        # "Hook PreToolUse:Bash requires confirmation for this command." Silence is the fail-open
        # answer for a payload this classifier cannot read; the normal approval flow still owns it,
        # and nothing is granted here that the harness would not have granted on its own.
        return

    policy = gp.autonomy(gp.load(payload=data))

    # `allowPackageManagers` is applied inside `_classify`, once per segment — see
    # `_package_manager_verdict`. Applying it here, to the whole line, is what let a leading
    # `echo ok &&` carry an undeclared manager past the refusal.
    segments = command_segments(command)

    final_decision = "allow"
    ask_reason: str | None = None
    for segment in segments or [command]:
        decision, reason = _classify(segment, policy)
        if decision == "deny":
            _deny(
                reason or "BLOCKED: Dangerous command",
                event=event,
                codex_turn=codex_turn,
            )
            return
        if decision == "ask":
            final_decision = "ask"
            ask_reason = ask_reason or reason

    if final_decision == "allow":
        _allow(event=event, codex_turn=codex_turn)
        return

    # Unknown or state-changing commands require user approval. Never fall
    # through to allow — unknown commands may be destructive tools, typos, or
    # untrusted invocations.
    _ask(ask_reason, event=event, codex_turn=codex_turn)


if __name__ == "__main__":
    main()
    sys.exit(0)
