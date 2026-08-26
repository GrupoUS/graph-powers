---
description: "Execute an implementation plan that already exists — in a plan file or in this conversation. Use when the user says to implement, build or execute the plan, to start a sprint, or to carry out what was agreed. Routes the plan through executing-plans, applies test-driven development to production behaviour, assigns agents, and runs the declared gates. Do not use to decide what to build (/plan) or to confirm the result holds (/verify)."
workflow_type: orchestrator-workers
---

# /implement

**ARGUMENTS**: $ARGUMENTS

> **Read before step 0 — never reconstruct these from memory:** `${CLAUDE_PLUGIN_ROOT}/references/shared/000-config-loader.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/005-method-bootstrap.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/007-path-conventions.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/010-quality-gates.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/015-verification-gate.md`
> Read `${CLAUDE_PLUGIN_ROOT}/references/execution-floor.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/020-complexity-routing.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/030-agent-assignment-matrix.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/060-skill-domain-matrix.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/070-parallel-agent-spawn.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/080-sequential-phase-gating.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/120-skill-invocation-order.md`.
>
> `/implement` is the harness adapter, not a second execution engine. The task loop, ledger, briefs,
> reviews and final review belong to `graph-powers:executing-plans`. The project-specific rolling
> dispatch and phase gates are `${CLAUDE_PLUGIN_ROOT}/skills/planning/references/phase-c-executing-plans.md`, read only for L3+ execution.

---

## 0. Pre-flight

Read `.graph-powers/config.json` for the branch, tooling, paths and autonomy policy. If
`${rulesDir}/routing-supplements.md` exists, read it for project-specific routing.

Use the file-search tool to locate the plan in this order:

| Source | Action |
|---|---|
| `$ARGUMENTS` names a plan file or directory | Invoke `Skill("graph-powers:executing-plans")` with that plan. |
| One active `${paths.planDir}/*/PLAN.md` or legacy `${paths.planDir}/*.md` matches the request | Invoke `Skill("graph-powers:executing-plans")` with that plan. |
| The approved plan is in this conversation | Preserve it verbatim in the canonical path from `007-path-conventions.md`, then invoke `Skill("graph-powers:executing-plans")`; do not re-plan it. |
| No approved plan exists | **STOP.** Route to `/plan`; `/implement` does not invent the missing plan. |

Parse **Tier**, **Layers**, `[SEQUENTIAL]` / `[PARALLEL-SAFE]`, task checkboxes, `Owns`, `Needs`,
`CHECK`, `EXPECT`, phase gates, sprint contracts and `[ASSUMED]` items. An old plan without the newer
fields is accepted only when its ordering, ownership and verification are still unambiguous.

Check the current branch and working tree before any write. Preserve existing user changes. Never
create, switch or delete a worktree as an implicit side effect; isolation belongs in the approved
plan or requires a separate decision.

**Flags:**

| Flag | Effect |
|---|---|
| `--codex` | For L5+ only, route an oversized implementation unit to `codex:codex-rescue` when that optional plugin is installed. |
| `--sprint=N` | Execute only sprint N of a multi-sprint plan. |
| `--dry-run` | Parse and display tasks, ownership, dependencies and agent assignments; write nothing. |

For `--dry-run`, stop after the routing table. Do not create the execution workspace.

---

## 1. Route skills and agents

The method skill is already selected in Step 0. Load domain skills only when the plan touches their
domain, in the order from `120-skill-invocation-order.md`:

- schema, migrations, API, handlers, services or a failing task → `graph-powers:debugger`, plus a
  host database skill only when `${rulesDir}/routing-supplements.md` declares one;
- UI components or styling → the project's design rule or declared design-system skill;
- performance, SEO or the security baseline → `performance-optimization`;
- skill authoring or harness wiring → `skill-improve`;
- an external API or provider → the configured host skill, otherwise the read-only
  `graph-powers:librarian` agent.

Use the plan's `Agent` field when present. Otherwise resolve the agent from
`030-agent-assignment-matrix.md`; never maintain a second assignment table here. Before an L3+ phase,
spawn `graph-powers:explorer` in the background for only the patterns the phase needs. External
facts, when needed, go to `graph-powers:librarian` in the same batch.

| Tier | Execution |
|---|---|
| L1-L2 | Inline in the main agent; no delegation. |
| L3-L5 | Subagent-driven through `graph-powers:executing-plans`. |
| L6+ | Coordinator plus specialists, still using the same engine, ownership and review contracts. |

Every spawn uses the seven sections in `references/execution-floor.md § 4`. Read-only work runs in
the background. Writers own disjoint paths, and no caller overrides the model declared by an agent.

---

## 2. Execute the plan

Follow the selected mode in `graph-powers:executing-plans`. Supply the resolved config, plan fields,
agent routing and domain skills; the engine owns its ledger, dispatch, task review, fix rounds and
final review. For L1-L2, use its inline path without manufacturing subagent overhead. Do not
paraphrase or replace either loop here.

### TDD gate

When a task implements a feature, bug fix, refactor or behaviour change, invoke `Skill("graph-powers:test-driven-development")`
in the writer's prompt before any production edit:

```
one behaviour → focused test → verify expected RED → minimum GREEN → verify GREEN → refactor only while green
```

The RED and GREEN commands and deciding output go in the task report, or in the inline evidence for
L1-L2. A passing test that was never seen failing is not TDD. Generated code, configuration-only
work and throwaway prototypes are exceptions only after the user accepts the exception, exactly as
the skill requires.

KISS and YAGNI bind every task: implement only the current `EXPECT` and failing test; reuse an
existing seam; add no speculative option, compatibility layer, abstraction, refactor or adjacent
feature. A later task can earn a later capability.

### Review and evidence

Treat every agent report as unverified until its diff and focused `CHECK` support it. A checked task
with `EVIDENCE: pending` remains incomplete; an impossible check stays visible as
`ABANDON: <task id> <reason>`.

Continuous execution means progress updates, not approval pauses. Stop only on the conditions in
§ 5 or on a boundary that `safety-floor.md` reserves for the user.

---

## 3. Gates

Run literal commands from `tooling.commands`; never reconstruct a package-manager command.

| Boundary | Gate |
|---|---|
| After each task | Its focused `CHECK` only. |
| After each phase | Resolved type-check and lint, once; confirm the next phase's required interfaces exist. |
| After a sprint with a contract | Every `verify:` command in its Done Definition. |
| Final | Resolved type-check, lint and serial full tests, once. |

Apply `${CLAUDE_PLUGIN_ROOT}/references/shared/015-verification-gate.md` to every PASS or completion
claim: fresh command, full output, exit code read, then the claim. If UI changed, also use
`webapp-testing` for the plan's browser criterion. A missing declared command is `NOT DECLARED`, not
passing.

---

## 4. Schema apply

`${database.commands.generate}`, when declared, is a repository write and follows the ordinary task
loop. `${database.commands.apply}` is the irreversible edge:

1. Missing command → print `NOT DECLARED` and stop.
2. Missing policy or `${database.applyPolicy} = never` → show the apply and rollback commands; do
   not run them.
3. `${database.applyPolicy} = optIn` → require explicit approval in this turn, then apply and run
   `${database.commands.status}`. Only if this branch runs, classify the result with
   `Skill("performance-optimization")` and claim success on PASS.

`/verify` never applies a schema. Do not invent an opt-in key.

---

## 5. Failure and stopping conditions

- No approved plan → route to `/plan` and stop.
- An `[ASSUMED]` item blocks the next task → validate it or ask; never guess silently.
- A task needs a path outside `Owns` → stop that task, correct the plan and re-dispatch.
- A report says PASS but its `CHECK` fails → the task failed.
- A phase or sprint gate fails → do not advance to a dependent phase.
- Never retry the same worker with the same context. Follow the engine's fix-round cap; if repeated
  attempts reveal a deeper defect, route to `/debug recover`.
- Destructive, security-sensitive, credential or outward-facing work — including stage, commit,
  push, PR, merge and publish — requires the user's current-turn approval.
- A plan whose requirements or ownership cannot be made unambiguous is BLOCKED; report the exact
  missing decision.

---

## 6. Completion

Collect every live agent, finish the engine's final review, run the final gates, then run
`/verify quick`. It must pass before the implementation is called ready. Leave the working tree
reviewed and unstaged; do not commit, push, open a PR or merge.

```
Implementation complete.

Working tree reviewed and left unstaged. Git actions require separate user authorization.

Evidence:
  - Focused task checks: <results>
  - Type check: <result or NOT DECLARED>
  - Lint: <result or NOT DECLARED>
  - Tests: <result or NOT DECLARED>
  - Sprint contracts: <result or not applicable>
  - Final review: <result>

Rulings I made:
  - <decision — why — cost if wrong, or none>

Next: /verify
```
