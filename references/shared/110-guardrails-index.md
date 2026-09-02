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
| Turbo `--dry=json` on a captured stdout pipe (EPIPE abort cascade) | `smart_bash_approver.py` | `Bash` | run debugger `turbo_dry_json.py` instead — not an env-var release |
| Agent-issued pre-commit verification and legacy audit | `commit_audit_gate.py` | `Bash` (`git commit`/`git push`) | commit: `<PREFIX>_ALLOW_VERIFY=1` · audit: `<PREFIX>_ALLOW_AUDIT=1`; fixed core order, one combined commit budget, push audit only under its audit timeout |
| Writes to `.env`, lockfiles, `.git/`, secrets, declared paths | `protect_files.py` | `Edit`/`Write` | nothing |
| Final project-declared lint | `stop_verify.py` | `Stop` | `<PREFIX>_ALLOW_LINT=1` in the client environment |

`<PREFIX>` is `git.optInPrefix` from the project's config, and it is per project on purpose: an
approval given in one repository must not count in another. Every one of these fails **open** — a
missing or malformed config falls back to defaults. Configured commands share machine-local trust,
and model-facing responses are fixed summaries without checker output, commands, paths or exceptions.
Stop semantics: Claude=block; Cursor=bounded follow-up with generated marker and loop limit 5;
Grok=passive/unsupported; Codex has a Stop schema contract but runtime parity is `NOT CONFIRMED`.
The exact pre-commit cache artifact is self-excluded from its fingerprint; only fresh green results
are cached, never failures, timeouts or unavailable tools.

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

Advisory, same registration, no denial: `auto_update.py` (Claude plus native Codex/Desktop
refresh), `branch_session_notice.py`,
`session_context.py` (SessionStart), `subagent_context.py` (SubagentStart — the solution ladder,
`025-solution-ladder.md`, into every subagent), `ultracite.py` (PostToolUse), `notify.py`
(Notification).

`ultracite.py` formats edits; `stop_verify.py` runs the declared global lint and trusts its exit
code. An unavailable command is skipped, never reported as covered.

The Windows handler benchmark is report-only evidence, not telemetry. No dispatcher, Git-native
hooks or staged-snapshot execution is active; `SubagentStart` is the one lifecycle registration
added since, and it is advisory.

### Convention — rules the project writes, and nobody enforces but you

| Guardrail | Canonical location | Trigger |
|---|---|---|
| Stability checklist | `${rulesDir}/stability.md` | any code change |
| Design tokens, no colour literals, scroll ownership | `${rulesDir}/design.md` | style changes |
| Execution and dispatch limits | `${rulesDir}/execution.md` | spawning agents |
| UX floor | `${rulesDir}/ux.md` | user-facing changes |
| Anything the project added | `${rulesDir}/` | as the file declares |
| Known bug patterns | `${CLAUDE_PLUGIN_ROOT}/skills/debugger/references/anti-patterns.md` | debugging |
| Other declared gates | `${tooling.commands}` | before commit/release |

The plugin ships templates for the first four in `templates/rules/`. Rows for a project's own
domain — its database invariants, its integrations, its tenancy model — are added there by the
project and are not the plugin's to name.
