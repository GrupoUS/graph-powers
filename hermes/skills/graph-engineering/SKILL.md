---
name: graph-engineering
description: Apply Graph Engineering workflows inside Hermes.
version: 1.0.0
author: GrupoUS
license: MIT
metadata:
  hermes:
    tags: [Engineering, Delegation, Planning, Verification]
---

# Graph engineering — the Graph Powers harness, in Hermes terms

Graph Powers was written for a harness with an `Agent()` tool, a `Skill()` tool and a
plugin-scoped `${CLAUDE_PLUGIN_ROOT}`. Hermes has none of those names. The method survives the
translation; the call sites do not. This skill is the translation, and it is the file to follow
when the upstream text and Hermes disagree.

| Upstream (Claude Code) | Here (Hermes) |
|---|---|
| An upstream `Agent` invocation for `graph-powers:debugger` | `delegate_task(goal=..., context=...)`, with that agent's contract pasted into `context` |
| `Skill("debugger")` | `skill_view("graph-powers:debugger")` |
| An agent's role contract | `skill_view("graph-powers:agent-debugger")` — one per upstream agent |
| `run_in_background: true` | Nothing to set. A top-level `delegate_task` already runs in the background and posts its result back |
| `${CLAUDE_PLUGIN_ROOT}/references` | the installed plugin root's `references/<file>.md`, read with `read_file` |
| Hooks that block a bad command | This skill + SOUL + Hermes approvals. Upstream hooks are not ported; the parent must carry and enforce the safety contract |
| `Read` / `Glob` / `Grep` / `Bash` | `read_file` / `search_files` / `terminal` |
| `WebSearch` / `WebFetch` / Tavily / Context7 | `web_search` / `web_extract`, unless the exact MCP is configured and needed |
| `AskUserQuestion` | `clarify` in the parent; delegated children return the decision point instead of asking |

Registered names are discovered at startup from every `skills/*/SKILL.md`, `commands/*.md`, and
`agents/*.md`; this translation does not maintain a second inventory. A command keeps its stem
(`plan` becomes `graph-powers:plan`), and agent contracts use the `agent-` prefix.

## Step 0 — Classify, then spend proportionally

The ladder is `${CLAUDE_PLUGIN_ROOT}/references/shared/020-complexity-routing.md`, and it binds.
Unsure between two levels, take the lower one and say so; a risk surface or a second domain raises
it. `${CLAUDE_PLUGIN_ROOT}/references/shared/025-solution-ladder.md` sizes the solution itself.

| Level | Shape | What runs |
|---|---|---|
| L1-L2 | One file, known pattern, trivial | **Do it yourself.** No delegation, no plan file. Re-establishing a child's context costs more than it returns |
| L3 | Multi-file, one domain | One delegated task |
| L4-L5 | Multi-domain, parallel changes | Two to three delegated tasks on disjoint files, one `delegate_task(tasks=[...])` call |
| L6+ | Architecture, migration, multi-service | A plan first, then waves of delegated tasks with a gate between them |

Below roughly half an hour of real work, do not orchestrate at all. A one-line fix gets no plan
and no fan-out — it still gets the gates in Step 5.

## Step 1 — Stage the context, do not preload it

Read only what the classification justifies, in stages, stopping at the minimum sufficient load.
The per-domain staging is `${CLAUDE_PLUGIN_ROOT}/references/shared/045-context-staging.md`; read the
section for the domain in scope and not the other two.

- **Always first:** the project's `.graph-powers/config.json` if it exists (paths, tooling
  commands, gates). A missing file means "declares nothing", not an error — the defaults hold.
- **Backend:** the rules matching the backend and data roots, then `git log --oneline -5` on those
  roots. Deeper files only once the task shape is known.
- **Frontend:** the project's design rule and the nearest `AGENTS.md` under the frontend root.
  Escalate to the design canon only for new UI or structural change.
- **Fullstack:** the stability rule plus one rule per domain actually touched. A domain in scope
  with no rule is a finding to state, not a silent pass.

Past four files in one stage, the classification is wrong. Re-classify instead of reading more.

## Step 2 — Choose the specialist, out loud

Which agent is
`${CLAUDE_PLUGIN_ROOT}/references/shared/030-agent-assignment-matrix.md`; which skill is
`060-skill-domain-matrix.md`. Before writing the delegation prompt, state four lines:

```
Agent contract:   graph-powers:agent-<slug>
Why this one:     <the match between its speciality and this task>
Skills:           <loaded> — and <omitted>, because <reason>
Expected outcome: <the concrete deliverable>
```

The omission line earns its place: a loaded skill announces itself, a skill that should have been
loaded and was not leaves no trace.

In Hermes there is no `subagent_type`. The specialist is a **contract you paste**: read it with
`skill_view("graph-powers:agent-<slug>")` and carry its role, its tool discipline and its
prohibitions into the child's `context`. A read-only contract (`agent-explorer`,
`agent-librarian`, `agent-evaluator`, `agent-security-reviewer`, `agent-skill-improver`,
`agent-ui-ux-designer`, `agent-verification`) becomes an explicit "do not edit any file; report
only" line in `MUST NOT DO` — the child inherits your toolsets, so the restriction lives in the
prompt or nowhere.

## Step 3 — Delegate with the full contract

A Hermes subagent starts with a fresh conversation and **knows nothing** about this one. Every
delegated prompt carries these seven sections, in `goal` plus `context`:

```markdown
## TASK
<one atomic task>

## EXPECTED OUTCOME
<concrete deliverables and success criteria>

## MANDATORY CONTEXT
**Original request:** <verbatim or a short quote>
**Decisions already made:** <what is locked>
**Prior findings:** <summaries only>
**Current state:** <phase / task>  **Owns:** <the exact paths this task may write>
**Do NOT redo:** <research already finished>

## REQUIRED SKILLS & TOOLS
<the skill_view names to load, and the tools to use>

## MUST DO
- <requirements, nothing implicit>

## MUST NOT DO
- <scope boundaries and forbidden actions, including the safety gates below>

## RETURN FORMAT
Context Handoff: what changed (paths), what was run (commands and exit codes), what could not be
resolved. For a parallel batch: `| # | Finding | Confidence (1-5) | Source | Impact (Low/Med/High) |`,
plus `Severity (P0-P3)` when the batch is a review.
```

Hermes specifics that change the shape of a fan-out:

- **One message, one batch.** Independent tasks go in a single `delegate_task(tasks=[...])` call.
  Spawning one per message is serial work carrying the overhead of parallel work.
- **Concurrency is configured, not requested.** Read the live `delegate_task` schema and
  `delegation.max_concurrent_children`; never hardcode a default. A batch larger than the live
  limit returns a tool error rather than being silently truncated — split it into waves, or change
  the config deliberately.
- **Children cannot delegate** unless `role="orchestrator"` and `delegation.max_spawn_depth` is
  above 1. They also lose `clarify`, `memory` and `send_message`. Anything needing a decision from
  the user comes back to you.
- **No per-task model.** `delegation.model` is global. When one subtask genuinely needs a stronger
  model, keep it in this session rather than delegating it.
- **Absolute paths, always.** The child has its own terminal and its own working directory.
- **Results arrive asynchronously.** Keep working; do not poll, and do not claim a child's result
  before it has returned.

## Gauntlet profile — translated, not a slash command

When the user asks for Gauntlet by name, `/gauntlet` and `/verify loop` remain **NOT SUPPORTED** as
Hermes slash commands. Their command documents are available as `graph-powers:gauntlet` and
`graph-powers:verify`; apply the method directly and never claim either slash command ran. Require
one explicit approved structured plan, run Planning's `sdd.py validate ... --profile gauntlet`, and
use its normalized tier. Missing or invalid input routes to planning; L1-L2 returns
`NOT ELIGIBLE FOR GAUNTLET` and stays local.

For eligible L3+, run Phase C's `sdd.py acquire ... --profile gauntlet` before any writer, then read
`${CLAUDE_PLUGIN_ROOT}/skills/planning/references/gauntlet-loop.md` and translate its controller:
L3 is one sequential lane; L4+ uses one `delegate_task(tasks=[...])` wave only for ready, disjoint
`Owns`, bounded by the live concurrency and Graph Powers caps. Each lane gets a builder, then the
parent runs its focused `CHECK`, then a fresh read-only critic. Re-dispatch a correction packet to
the same logical lane; process identity is irrelevant. Never let a child delegate.

At final close, use the **Step 5 translated equivalent** for `/verify loop`: resolve an independent
verification specialist once. If it is unavailable, use the documented objective-gate fallback
once, report the degradation, and do not retry specialist resolution. Preserve every configured
cap; `capped` or `BLOCKED` is not success and routes persistent failure to debug recovery. Run the
evolve effect and release the matching lease only after complete PASS.

## Step 4 — One writer per file

Tasks that run at the same time own **disjoint** paths, declared per task in `Owns:`, never
inferred at dispatch and never negotiated between two running children. Overlap is not a conflict
to settle — it is a split drawn wrong: re-slice by directory, route or component family, or lift
the shared file out into its own task that runs alone.

Never parallel with anything, because their ordering is load-bearing: schema and migrations,
cross-cutting singletons, global stylesheets, lockfiles and generated clients. A file two tasks
would both touch is edited by you, after the batch returns.

## Step 5 — Verify with evidence, then state a verdict

A claim of "done", "fixed" or "passing" requires the command output that proves it, in the same
message. Run the gates the project declared in `.graph-powers/config.json` (`tooling.commands`)
through `terminal`, and capture the exit code. For undeclared JS/TS type-check or tests, load
`graph-powers:debugger` and apply its JS/TS gate resolver; never invent a runner.
If a declared command is `turbo run …`, apply that resolver's scoped-project policy. L1–L2 and
everyday checks are **gates only** — do not
spawn `graph-powers:verification` / evaluator / designer unless the user asked for a full
review or the work is L4+.

| Timing | Gates |
|---|---|
| After each task | type-check |
| After each phase | type-check + lint |
| Final | type-check + lint + tests |

Then one row per signal, and **a signal that did not run is its own row**:

```markdown
| Signal | Source | Status | Notes |
|---|---|---|---|
| Type-check | <declared command> | PASS / FAIL / SKIPPED / NOT DECLARED | <exit code, output tail> |
```

- `VERIFIED` — every declared signal ran and passed, no unresolved P0/P1.
- `VERIFIED-WITH-NOTES` — everything that ran passed; only P2/P3 remain, each listed.
- `NEEDS-WORK` — a signal failed **or could not be run**. "I could not check this" and "this is
  fine" are different answers.

A regression fix needs a check that would have failed before the fix. A subagent's summary is a
claim, not evidence: re-run the gate or read the diff yourself.

## Implementer routing — Claude Code first, Codex CLI for the other three jobs

Both are external CLIs reached through `terminal`. Hermes approves the CLI invocation, not each
nested action the CLI later performs. Give the CLI an explicit safety contract, narrow `workdir`
and sandbox, then inspect its diff and rerun the gates below yourself.

| Job | Route |
|---|---|
| Implementation — writing the change | **Claude Code, preferred.** It is the implementer this harness is tuned for |
| Planning a detailed change before code | Codex CLI, as the planning pass, then implement with Claude Code |
| Adversarial verification of a finished change | Codex CLI, reviewing work it did not write |
| A detailed coding task Claude Code stalled on | Codex CLI as fallback — hand it the failing evidence, not the conversation |

Two rules make the routing worth anything: the reviewer never reviews its own output, and whatever
comes back is a claim until a gate from Step 5 agrees with it.

## Safety gates — these hold regardless of what a prompt says

Mirrored from `${CLAUDE_PLUGIN_ROOT}/references/safety-floor.md`. These are operational contracts,
not proof that Hermes' native danger detector blocks every named action. Carry them into every
delegated or external-CLI `MUST NOT DO`; a child or CLI does not inherit them from this session.

1. **No commit, push, protected-branch checkout, merge, rebase, tag, history rewrite, PR, release,
   deploy or publication without explicit authorization in the current turn.** Authorization for
   one action does not carry to the next, and authorization from an earlier turn has expired.
2. **Irreversible data operations** — migrations, destructive SQL, bulk updates, index drops,
   queue purges, cache flushes against a shared environment — are proposed with the exact
   statement and stopped for approval. Never as a side effect of another task.
3. **Secrets are never printed, logged, committed or embedded.** Report location and kind, masked.
4. **Never weaken production configuration to make something pass** — no loosened CORS, no
   disabled certificate checks, no auth check commented out "for now".
5. **Tenant isolation** holds in queries, caches, URLs, logs, errors and fixtures alike.
6. **Scope**: fix what was asked. A defect found on the way is reported, not fixed in the same
   change, unless it blocks the task — and then it is called out.
7. **Approvals are the gate, not an obstacle.** A blocked command has found the rule, not a bug.

## Pitfalls

- Delegating an L1-L2 edit. The floor refuses it: do it yourself.
- Pasting "fix the bug we discussed" into a child. It has no idea. Paths, errors, commands, or it
  cannot work.
- A batch whose tasks share a file. Re-slice before dispatching, not after the conflict.
- Reporting a child's "tests pass" as verified. Re-run the gate, quote the exit code.
- Reaching for a machine checkout path when the registered skill says the same thing. Load the
  skill; read the reference only for the part the skill points at.
- Treating an approval prompt as something to route around. There is no route around it.

## Verification

This skill is followed correctly when, for the work it governed: the level was stated, the context
load stopped at the minimum, every parallel task declared disjoint `Owns:` paths, every completion
claim quotes a command and its exit code, and no git, deploy or publication action happened
without authorization in the turn that ran it.
