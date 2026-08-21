## Section 11: Guardrails Index

> What actually stops you, and where the rule that stops you is written. Read the canonical source
> before applying — this is a map, not the text.

The distinction that matters: the first table **denies**, in code, whether or not anyone read it.
The second table is convention — real, but enforced by attention. An index that mixes them teaches
people to expect a block that never comes, or to be surprised by one that does.

### Enforced — hooks, declared in `hooks/hooks.json`

| Guardrail | Hook | Fires on | Released by |
|---|---|---|---|
| Kill switch · spawn ceiling · round ceiling · write lease | `graph_guardrails.py` | every tool call | `rm AGENT_STOP` · `<PREFIX>_ALLOW_SPAWN_OVER=1` · `<PREFIX>_ALLOW_OFF_LEASE=1` |
| Commit without approval | `git_commit_gate.py` | `Bash` | `<PREFIX>_ALLOW_COMMIT=1` |
| Push, and push to a protected branch | `git_push_gate.py` | `Bash` | `<PREFIX>_ALLOW_PUSH=1` (+ `_ALLOW_PUSH_MAIN=1`) |
| Landing HEAD on a protected branch; deleting one | `git_branch_gate.py` | `Bash` | `<PREFIX>_ALLOW_MAIN_CHECKOUT=1` |
| Bash autonomy and the destructive floor — what git cannot undo | `smart_bash_approver.py` | `Bash` at `PreToolUse` and `PermissionRequest` | `autonomy`; the floor still holds under `autonomous` |
| The project's own pre-commit audit | `commit_audit_gate.py` | `Bash` | `<PREFIX>_ALLOW_AUDIT=1` |
| Writes to `.env`, lockfiles, `.git/`, secrets, declared paths | `protect_files.py` | `Edit`/`Write` | nothing |

`<PREFIX>` is `git.optInPrefix` from the project's config, and it is per project on purpose: an
approval given in one repository must not count in another. Every one of these fails **open** — a
missing or malformed config falls back to the defaults rather than taking the session down.

**Releasing a gate, on any operating system.** The hook looks for the literal text `<KEY>=1` in the
command, or for the variable in the environment (`hooks/_config.py`, `opted_in`). It never asks the
shell to interpret anything, so all three of these work — write the one your shell accepts:

| Shell | Form |
|---|---|
| POSIX (bash, zsh, Git Bash) | `<PREFIX>_ALLOW_COMMIT=1 git commit -m "…"` |
| PowerShell | `$env:<PREFIX>_ALLOW_COMMIT=1; git commit -m "…"` |
| cmd.exe | `set <PREFIX>_ALLOW_COMMIT=1 && git commit -m "…"` |

The POSIX form is the one most of this documentation shows, and it is the only one that is *also*
shell syntax rather than just text the hook recognises. On Windows the first form releases the gate
and then fails to run, which looks like the guardrail misbehaving and is not.

Advisory, same registration, no denial: `auto_update.py`, `branch_session_notice.py`,
`session_context.py` (SessionStart), `ultracite.py` (PostToolUse), `notify.py` (Notification).

`ultracite.py` runs `tooling.commands.format` after an edit and `tooling.commands.lint` at a stop.
Both need the tool they name to be installed and on PATH — the plugin runs the command and nothing
more. A missing tool is skipped rather than swallowed, and `session_context.py` names it in the
session tag (`NOT INSTALLED: lint needs \`oxlint\``); install globally so it works in every
repository a session visits.

### Convention — rules the project writes, and nobody enforces but you

| Guardrail | Canonical location | Trigger |
|---|---|---|
| Stability checklist | `${rulesDir}/stability.md` | any code change |
| Design tokens, no colour literals, scroll ownership | `${rulesDir}/design.md` | style changes |
| Execution and dispatch limits | `${rulesDir}/execution.md` | spawning agents |
| UX floor | `${rulesDir}/ux.md` | user-facing changes |
| Anything the project added | `${rulesDir}/` | as the file declares |
| Known bug patterns | `${CLAUDE_PLUGIN_ROOT}/skills/debugger/references/anti-patterns.md` | debugging |
| Formatter and linter | `${tooling.commands.lint}` | before every commit |

The plugin ships templates for the first four in `templates/rules/`. Rows for a project's own
domain — its database invariants, its integrations, its tenancy model — are added there by the
project and are not the plugin's to name.
