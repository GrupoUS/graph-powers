# Phase C — Executing-plans

> Sequential guide for the third phase of the planning chain.
> **Direct-invokes `graph-powers:executing-plans` as the engine, in subagent-driven mode** — fresh subagent per
> task, two-stage review, continuous execution — executed through this plugin's `/implement`.
> For inline execution the engine is the same skill in inline mode.

---

## Entry contract

- Phase B complete. `<plan dir>/PLAN.md` GATE-2-approved and user-approved.
- Tier **L5+** (at L4 the plan is the deliverable; the user invokes `/implement` when ready).
- Branch is `${git.workBranch}`. **Never a protected branch.**

## Exit contract

- Every task verified with evidence, every phase gate met, `/verify quick` PASS, `/evolve auto` run.
- Stop at "reviewed working tree ready". Git actions stay separate and need current-turn
  authorization. **Never auto-merge.**

## Loop contract

> Model and guards: `references/loop-engineering.md`.

- **trigger:** plan approved, tier L5+, branch `${git.workBranch}`.
- **goal (binary):** *per task* — implementer PASS **AND** GATE A PASS **AND** GATE B PASS **AND**
  its `EVIDENCE` line carries real output; *per phase* — every gate box checked with evidence;
  *overall* — `/verify quick` PASS and `/evolve auto` done.
- **terminal:** overall goal PASS → "reviewed working tree ready", stop. Any guard trips → escalate.

---

## Step 1 — Invoke the engine, then `/implement`

**`Skill("graph-powers:executing-plans")`** in subagent-driven mode first — it loads the doctrine (read the plan
once, per-task implementer → spec review → quality review, no inter-task pause). Then:

```
/implement <plan dir>
```

`/implement` parses the checkbox tasks and their `Owns` / `Needs` / `CHECK` fields, and the
`[SEQUENTIAL]` / `[PARALLEL-SAFE]` phase markers. The Phase B format is exactly its expected input.
The engine supplies the *why*; `/implement` and the steps below supply the *how*.

## Step 2 — Rolling dispatch

One rule replaces the old three-barrier protocol, and it is what makes a plan of disjoint tasks run
in the time of its longest chain rather than the sum of its waves:

> **Dispatch every task whose `Needs` are verified and whose `Owns` collide with nothing in flight**,
> up to `graphGuardrails.maxParallelWave`. **When a task returns, review it immediately** — GATE A,
> then GATE B — and **its verification releases whatever it unblocked.** Never wait for a sibling
> that this task does not read.

Waiting for a whole wave before reviewing anything is the failure this replaces: the slowest task in
a wave delayed every review in it, though the reviews were independent.

### 2a — Implementer (fresh subagent, foreground, write-capable)

```ts
Agent({
  subagent_type: <the task's Agent lane, prefixed graph-powers:>,
  prompt: <§ Subagent prompt templates → Implementer, with the task block pasted verbatim>,
})
```

The subagent reads its own task block and nothing else — not the plan, not a sibling's output.

### 2b — GATE A — spec compliance (fresh, read-only). Only if 2a returned PASS.

PASS → 2c. FAIL → append the gaps to the task block under `## Reviewer feedback` and re-dispatch 2a
(max 3 retries per task across both gates). BLOCKED → halt that task, escalate; siblings continue.

### 2c — GATE B — code quality (fresh, read-only). Only if 2b returned PASS.

Nits are FYI and never trigger a re-dispatch; only a cited rule or anti-pattern does. PASS → 2d.

### 2d — Close the task

Run the task's own `CHECK`, paste the deciding output into its `EVIDENCE:` line, and check the box.
**A checked box with `EVIDENCE: pending` is unmet** — the box is a claim and the evidence is the
proof. Record changed paths, the base `HEAD` and the suggested conventional-commit subject; confirm
nothing outside `Owns` changed; leave everything unstaged. Then dispatch what this task unblocked.

If a check turns out to be impossible, do not delete it: add `ABANDON: <task id> <reason>` and
surface it in the report. Visible surrender is honest; silent scope-narrowing is not.

## Step 3 — Continuous execution

Per the engine: *"Do not pause to check in between tasks. Execute all tasks without stopping. Only
stop on: BLOCKED you cannot resolve, ambiguity that prevents progress, or all tasks complete."*
Surface progress as status, not as an approval request.

## Step 4 — The phase gate, once per phase

When every task in a phase is verified, work that phase's gate block. It holds the checks that are
about the tree rather than one task — the repository-wide type-check and lint, "nothing outside the
phase's `Owns` sets changed", and "the interfaces the next phase `Needs` exist and match".

**These commands run here and nowhere else.** A task that runs the whole project's type-check to
prove one local claim pays for the whole project, once per task. Cross-task failures are resolved in
a new sequential task; never by re-dispatching the batch.

## Step 4.5 — Reasoning gate before escalation (L5+)

When a task fails its **2nd** retry, invoke `mcp__sequential-thinking__sequentialthinking` to
decompose the error surface — root cause, why the earlier fixes missed, candidate paths — **before**
the 3rd attempt or `/debug recover`. It prevents a blind third retry burning the spawn cap.

## Step 5 — Post-execution gate

Every phase gate met → `/verify quick`. The gate commands are the ones the project declared in
`tooling.commands`; one it did not declare is reported `NOT DECLARED`, never as passing. Plus the
negative checks in `${rulesDir}/`, and a browser flow per `Skill("webapp-testing")` if UI changed and
the project has a staging URL.

## Step 6 — `/evolve auto`

On `/verify quick` PASS: captures learnings, may append a row to `.graph-powers/logs/progress.md`
with the base `HEAD` and working-tree status. It stages and commits nothing.

## Step 7 — Closing message

```
Phase C complete.
- Every task verified with evidence; every phase gate met
- /verify quick PASS · /evolve auto done
- Base HEAD: <SHA> · Suggested commit subject: <subject>
- Working tree ready for review. Stage/commit/push/PR/merge need separate authorization.
```

**STOP.** Do not push, do not open a PR, do not merge.

---

## Stopping conditions — phase-unique rows

The shared table is `../SKILL.md § Stopping & red flags`; these are the rows that only apply here.

| Condition | Action |
|---|---|
| `/verify quick` FAILs after every task passed | Halt — this is a cross-task interaction. Do not auto-fix inside the `/implement` loop |
| A task's `Owns` set turns out to be wrong mid-flight | Halt that task, fix the plan, re-dispatch. Never let a subagent widen its own ownership |
| A task returns PASS but its `CHECK` fails when re-run | Treat as FAIL and re-dispatch. Self-report never outranks the command |

---

## Subagent prompt templates

> Fill `{{...}}` per dispatch. Shared contract first, then one block per gate. All three return
> < 2000 tokens; longer detail goes to `.claude/agent-memory/<agent>/`.

### Shared dispatch contract

- **One task = one fresh subagent.** No context carry-over between tasks.
- **Subagents receive pasted content, not file paths** — the task block, the spec excerpt, the diff.
  The implementer is the exception: it reads the files in its own `Owns`.
- **Gate order:** implementer (write-capable) → spec reviewer (read-only) → quality reviewer
  (read-only). Quality runs only after spec PASS.
- **Re-dispatch:** FAIL with feedback appended under `## Reviewer feedback`. Max 3 retries per task
  across both gates. BLOCKED → halt that task and escalate.

### Implementer (write-capable)

```
You are an implementer subagent for `${project.name}`.

## Scene context (read once, do not re-derive)

Fill these from the project config before dispatching — a subagent inherits nothing, so a
placeholder left here is a fact the implementer will invent.

- Repo: `${project.name}`. Branch: `${git.workBranch}` — never a protected branch, never push, never merge.
- Stack: `${project.stack}`. Package manager: `${tooling.packageManager}`, and no other.
- Tests: `${tooling.commands.test}`. Type check: `${tooling.commands.typeCheck}`. Never substitute a different tool.
- Line endings: LF only. Before handoff: `${tooling.commands.format}` on every file you edited.
- The project's non-negotiables: `${chain.hardRules}` and `${chain.invariants}`, plus whatever in
  `${rulesDir}/` matches the paths you own. These are the project's, declared in its config — this
  prompt does not carry a list of its own.

## Your task
{{the task block from the plan, verbatim: title, Owns, Needs, CHECK, EXPECT, Steps}}

## What you MUST do
1. Read every file in `Owns` before editing it.
2. Follow the Steps in order; do not skip the TDD ones (failing test → RED → implement → GREEN).
3. Run your task's `CHECK` and report its output verbatim — that output becomes the plan's EVIDENCE.
4. Run `${tooling.commands.format}` on every file you edited. Leave everything unstaged.
5. Return the structured report below.

## What you MUST NOT do
- Read the plan file or another task's block. Your work is self-contained.
- Write any path outside `Owns` — if you need one, STOP and return BLOCKED.
- Run the whole project's type-check or lint. That is the phase gate's job, not yours.
- Stage, commit, push, open a PR, merge, use `--no-verify`, or `git commit --amend`.

## Return contract (< 2000 tokens)
### Status        PASS | FAIL | BLOCKED
### Changed paths - <path> …            (must be a subset of Owns)
### CHECK output  <the deciding lines, verbatim — this is the evidence>
### Git state     base HEAD <short SHA> · suggested subject <conventional-commit subject> · unstaged YES/NO
### Summary       2-5 sentences: what you did, and why EXPECT now matches.
### Next          (empty unless BLOCKED — then what is blocking)
```

### Spec reviewer (read-only — GATE A)

```
You are a spec-compliance reviewer for `${project.name}`. Verify the diff fulfills the task block —
nothing else. You are NOT reviewing code quality, style, naming, comments or test design.

## Task block           {{paste the task block, including CHECK and EXPECT}}
## Implementer's diff   {{paste the full diff}}
## Claimed evidence     {{paste the implementer's CHECK output + Git state + Summary}}

## What to check
1. `EXPECT` genuinely matches the reported `CHECK` output — and that output could not appear on failure.
2. Changed paths are a subset of `Owns`. A surprise file is a FAIL, not a nit.
3. No scope creep: no "while I was here" refactor, no extra feature, no unscoped fix.
4. No silent omission — every sub-item of the task appears in the diff.
5. The evidence proves the criterion. A passing type-check alone proves nothing about behaviour.

## Return contract (< 1000 tokens)
### Verdict            PASS | FAIL | BLOCKED
### Criterion          <restate EXPECT> · Met? YES/NO/PARTIAL · Evidence: <diff lines / output>
### Ownership check    PASS / FAIL — <name any path outside Owns>
### Missing items      - <what the task asked for that the diff does not deliver>
### Recommendation     PASS → "Proceed to the quality reviewer." · FAIL → "Re-dispatch with these gaps." · BLOCKED → describe it.
```

### Code-quality reviewer (read-only — GATE B)

```
You are a code-quality reviewer for `${project.name}`. The diff already passed spec compliance — do
NOT re-check the task. Catch maintainability, project conventions, security and testability.

## The project's non-negotiables (each violation = FAIL)
{{paste ${chain.hardRules} and ${chain.invariants} from the project config, plus the rules in
${rulesDir}/ that match the touched paths. If the project declared none, say so and review on the
general criteria below only — do not invent conventions it never adopted.}}

## Implementer's diff   {{paste the full diff}}

## Also check
- Anti-patterns from `Skill("debugger")` → `../../debugger/references/anti-patterns.md`, where they
  match the touched files.
- Test design: tests exist and exercise the criterion rather than mocking it away.
- Error handling at boundaries · self-descriptive naming · no premature abstraction · comments only
  for a non-obvious WHY · no backwards-compatibility shim nobody asked for.
- Security boundaries: injection, auth scope, secrets, data that crosses a tenant.

## Return contract (< 1500 tokens)
### Verdict             PASS | FAIL | BLOCKED
### Rule check          - <rule>: PASS/FAIL — <evidence>   (only rules the diff touches)
### Anti-pattern check  PASS / FAIL — <name it>
### Test design check   PASS / FAIL — <name the gap>
### Nits (FYI only)     - <nit>    (never triggers a re-dispatch on its own)
### Recommendation      PASS → "Close the task." · FAIL → "Re-dispatch with these violations." · BLOCKED → describe it.
```
