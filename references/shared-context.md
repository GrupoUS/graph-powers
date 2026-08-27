# Shared context — index

The sections that lived here are now one file each under `references/shared/`, extracted byte for
byte with their headings, so a citation of `§ 7` still lands on the same words — inside
`070-parallel-agent-spawn.md`.

The split happened because of a number. Every command opened by loading this file whole, all 22 KB
of it, before doing anything; `/plan` used one section, and the delegation command of the day used
essentially none. Each
command now names only the fragments it reads, and together they load 45 % less on every invocation — `python3 .github/check_context_budget.py --compare`,
measured against a worktree of the pre-split tree with the same script.

| § | under `${CLAUDE_PLUGIN_ROOT}/references/shared/` | Carries |
|---|---|---|
| 0 | `000-config-loader.md` | how a command resolves `${…}` placeholders from the project's config |
| 0.5 | `005-method-bootstrap.md` | the method floor: skill before action, plan/TDD execution minimum, KISS/YAGNI |
| 0.7 | `007-path-conventions.md` | where plans, maps and runtime state are written |
| 1 | `010-quality-gates.md` | which gate runs after a task, after a phase, and at the end |
| 1.5 | `015-verification-gate.md` | no completion claim without an exit code from this session |
| 2 | `020-complexity-routing.md` | L1-L6, and the execution mode each one implies |
| 3 | `030-agent-assignment-matrix.md` | task to agent, and which ones run in the background |
| 3.5 | `035-agent-resolution-recovery.md` | recovery after a plugin agent name fails to resolve |
| 4 | `040-wisc-context-load.md` | how much context `/prime` loads at each tier |
| 4.5 | `045-context-staging.md` | how far into that tier to go, per domain, and when to stop |
| 5 | `050-tool-usage.md` | which tool for which job, and when not to reach for one |
| 6 | `060-skill-domain-matrix.md` | domain signal to the skill that owns it |
| 7 | `070-parallel-agent-spawn.md` | one message, background by default, and the wave width |
| 8 | `080-sequential-phase-gating.md` | gating a phase that depends on the previous one |
| 9 | `090-verdict-matrix.md` | the consolidated ship / hold verdict template |
| 10 | `100-autoresearch-loop.md` | the research cycle, its sources and its stop condition |
| 11 | `110-guardrails-index.md` | each guardrail and the rule file that states it |
| 11.5 | `115-code-graph.md` | the code-graph contract, its cookbook and its `[HARD]` limits |
| 12 | `120-skill-invocation-order.md` | meta, then method, then harness, then domain |
| 13 | `130-workflow-authoring.md` | writing a workflow script by hand, and checking it before it runs |

## Two rules that survive the split

**Never duplicate a fragment inside a command.** A pattern that lives in two files diverges, and
this plugin exists because that is exactly what happened last time. Point at the fragment.

**A command's header names what it reads, and nothing else.** The header this file replaced listed
five section themes for every command, whether or not that command used any of them — which is how
a file nobody's command needed stayed loaded by all twelve for as long as it did. Adding a fragment
to a header is a claim that the command acts on it; if it does not, the line is wrong.

## Why this path still exists

Nothing inside the plugin cites `shared-context.md § N` any more. The path stays live because
things outside it do: `codex/install.mjs` writes it into the generated `AGENTS.md`, the
installed copies of older versions point here. An index is what
they should find — not a 22 KB file, and not a 404.
