---
paths:
  - "{{PATHS_GLOB}}"
---

# Execution — commits, the terminal, and what to do when it fails

> Graph Powers template. Agent and skill routing comes from the plugin; only what belongs to this
> repository stays here.

## Commits `[HARD]`

**Nothing is committed or pushed without an explicit request in the current turn.** The final state
of any task is: working tree ready, gates green, report written. The commit is the reviewer's
decision.

The plugin's guardrails enforce this with code. When the approval comes, the opt-in travels with
the command — and the hook matches the key as **text**, not as shell syntax, so write whichever
form your shell accepts:

| Shell | Form |
|---|---|
| bash, zsh, Git Bash | `{{OPT_IN_PREFIX}}_ALLOW_COMMIT=1 git commit -m "..."` |
| PowerShell | `$env:{{OPT_IN_PREFIX}}_ALLOW_COMMIT=1; git commit -m "..."` |
| cmd.exe | `set {{OPT_IN_PREFIX}}_ALLOW_COMMIT=1 && git commit -m "..."` |

Only the first is also valid POSIX shell syntax. On Windows it releases the gate and then fails to
run the command, which reads as a broken guardrail and is not.

Format: Conventional Commits — `feat:`, `fix:`, `docs:`, `refactor:`, `chore:`, `test:`, `perf:`,
`build:`, `ci:`. The verb describes what the change does, not what you did.

## Before committing

In this order, and each result is evidence, not an impression:

```bash
{{PRECOMMIT_COMMANDS}}
```

If a gate fails, the commit did not happen — report which one, with the exact output, and fix the
cause. Never `git commit --amend` as a recovery: that rewrites the previous commit, which was not
the problem.

## Terminal

These are correctness facts, not ceremony — ignoring them breaks result capture:

- **Always with a timeout.** A hung command with no timeout hangs the whole session.
- **Non-interactive always**: `git commit -m`, never the editor; `--yes` where it exists;
  `GIT_TERMINAL_PROMPT=0` when git might ask for a credential.
- **Do not pipe output into `tail`/`grep` when you need the exit code** — the code becomes the last
  command's in the pipe. Use `; echo "EXIT=$?"` and filter afterwards.
- **Forward slashes in paths**, on every operating system.

## What this project refuses to merge

Root `REVIEW.md` — the gates and what each proves, the blocking findings with the incidents behind
them, the mechanical checks, and who approves what. `/pr-review` reads it; this rule does not
restate it.

## When something fails

Stop, understand, then fix. Repeating the same attempt with a small variation is the pattern that
burns the most time — after two attempts on the same hypothesis, the hypothesis is the problem.

## Branches

Work on `{{WORK_BRANCH}}`. `{{PROTECTED_BRANCHES}}` mirror what has already been approved: nothing
is written there directly. The path is branch → PR → review → merge by a person.

{{EXECUTION_PROJECT_NOTES}}
