---
description: "Diagnose and fix a defect — error, crash, stack trace, failing test, 500, hydration mismatch, CI gone red, or behaviour that changed after a deploy. Use when the user reports something broken, pastes an error, says a test is failing, says it worked yesterday, or asks why staging differs from local. Modes (positional) — default: triage and fix · audit: 9-dimension full-stack audit · frontend: React/UI plus browser E2E · backend: API and services · auth-db: auth, permissions, RLS · recover: after two or more failed attempts, when the user says we tried three times and it is still broken, that we are going in circles, or asks to back out and start over. Do not use to add behaviour that never worked (/implement), to judge code that already works (/pr-review), or to prove gates pass (/verify)."
workflow_type: routing
---

# /debug — Intelligent Debugging

**ARGUMENTS**: $ARGUMENTS

> **Read before step 0 — never reconstruct these from memory:** `${CLAUDE_PLUGIN_ROOT}/references/shared/000-config-loader.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/005-method-bootstrap.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/010-quality-gates.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/015-verification-gate.md`
> Read `${CLAUDE_PLUGIN_ROOT}/references/shared/020-complexity-routing.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/030-agent-assignment-matrix.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/040-wisc-context-load.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/070-parallel-agent-spawn.md`
> Read `${CLAUDE_PLUGIN_ROOT}/references/shared/100-autoresearch-loop.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/120-skill-invocation-order.md`

> First positional arg = mode. Examples:
> ```
> /debug                    # default — triage + investigate + fix
> /debug audit              # surface-gated audit (one Evaluator, up to two specialists)
> /debug frontend           # static + agent-browser E2E
> /debug backend            # API/service/handler/middleware
> /debug auth-db            # auth, permissions, tenant isolation, RLS
> /debug recover            # failure recovery (after 2+ failed attempts)
> ```
> Anything after the mode token is forwarded as scope (e.g., `/debug audit scope=payments`).

---

## What this file is, and is not

The discipline — the Iron Law, the stopping triggers, the escalation ladder, the pack selector and
the root-cause catalogue — is in `Skill("debugger")`, loaded in § 0.1 and **not restated here**.
Read `§ Iron Law` and `§ Stopping & escalation` there before proposing any fix. Its References
table is an index to consult, not a list to open: pick the row the Step calls for.

**This file owns only mode dispatch and the per-mode orchestration** (`audit`, `frontend`,
`backend`, `auth-db`, `recover`). The skill's numbering is **Steps 0-6** and it is the only
numbering — an artefact of this harness that says "Phase 4" is citing a scheme that no longer
exists. Browser work is `Skill("webapp-testing")`, loaded only when the reproduction needs one.

---

## 0. Mode dispatch

Parse first positional token from `$ARGUMENTS`:

| Token | Section | Sub-agents |
|---|---|---|
| (none) / `debug` / `auto` | § 1 default flow | by complexity (§ 1.3) |
| `audit` / `full` | § 2 audit | Evaluator + conditional security/UX (max 3) |
| `frontend` / `ui` / `react` | § 3 frontend | frontend-specialist + explorer (max 2) |
| `backend` / `api` | § 4 backend | templates B + C (+ D on a mutation) |
| `auth-db` / `auth` / `db` / `permissions` | § 5 auth-db | templates B + C + D |
| `recover` | § 6 recovery | evaluator Mode 3 · Mode 5 on a hypothesis the thread cannot leave |

A performance or resource-use complaint with no defect is not a mode here — run `/perf` and use its
resource audit. `audit` and `frontend` are not substitutes for the standard resource diagnostic.

Modes share the **§ 0.1 Setup** preamble.

### 0.1 Setup (every mode)

Load the debugger method and project knowledge layer (per
`${CLAUDE_PLUGIN_ROOT}/references/shared/005-method-bootstrap.md`):

```typescript
Skill("debugger"); // Steps 0-6, anti-pattern catalogue, packs, TDD and verification gates
```

Inside a plugin the skill is namespaced, so a same-named personal skill cannot shadow it.

Read `.graph-powers/config.json` (paths, tooling, gates, `${rulesDir}`). The bug catalogue at
`${CLAUDE_PLUGIN_ROOT}/skills/debugger/references/anti-patterns.md` arrives with the skill — **this
is the only place this command names it.** Every later section that needs a known-pattern lookup
uses what was loaded here.

Resolve baseline gates from `${CLAUDE_PLUGIN_ROOT}/references/shared/010-quality-gates.md` using literal `tooling.commands`. When the change set is JS/TS, apply `${CLAUDE_PLUGIN_ROOT}/references/shared/130-typescript7-oxc-gates.md` first. Fix loops use focused changed tests and the low-resource runners; run a full gate once after the fix converges.

Context load via `${CLAUDE_PLUGIN_ROOT}/references/shared/040-wisc-context-load.md` (WISC):
- Bug in frontend area → `/prime frontend`
- Bug in backend area → `/prime backend`
- Multi-layer → `/prime fullstack`

---

## 1. Default mode — Triage + investigate + fix

### 1.1 Quick triage (classify before investigating)

Detect error category in <10s:

| Signature | Category | Quick action |
|---|---|---|
| Generic server / `INTERNAL_SERVER_ERROR` | Backend handler | Read cited route/router |
| `TypeError: Cannot read properties of undefined` | Unguarded access | Find unguarded `[0]` / `.x` |
| Type-checker error (`TS2769`, `TS2345`, etc.) | Type mismatch | Compare schema vs DB column type |
| `415 Unsupported Media Type` | Content-Type / framework | Verify request headers |
| `CORS error` / preflight | Middleware ordering | CORS before auth |
| `ERR_MODULE_NOT_FOUND` | Import/export | Check the barrel file |
| `connection timeout` / `ECONNREFUSED` | Infra/DB | Check connection string + pool |

Symptom-to-cause lookups this table does not carry — hydration mismatch, stale cache after a
mutation, `FORBIDDEN`/`401`, cross-tenant leak, the transaction-driver trap — are in
`Skill("debugger") § Common Root Causes` and its bug catalogue, both already loaded.

**Known-pattern shortcut.** Also check `${rulesDir}/stability.md`, the domain rules the routing
matrix auto-loaded, and recent breaking changes in dependencies. A match → apply the documented fix
directly (L1-L2), no agents.

### 1.2 Complexity classification

Per `${CLAUDE_PLUGIN_ROOT}/references/shared/020-complexity-routing.md`.

### 1.3 Investigation by complexity

**L1-L2 — Direct fix.** Read file → identify root cause → apply minimal fix → run gates.

**L3 — Single agent.** Spawn 1 `graph-powers:explorer` (foreground): investigate root cause, return a findings
table with file:line. Read-only **by frontmatter, not by instruction** — a prompt saying "do not
fix" is a request, not a permission, and the bug catalogue records the review agent that reverted
80 lines of the diff it was reviewing. Fixing is a separate dispatch, after the root cause is named.

**L4-L5 — Parallel agents.** Follow
`${CLAUDE_PLUGIN_ROOT}/references/shared/070-parallel-agent-spawn.md`, then dispatch templates
**B (Code Archaeologist)** and **C (Regression Hunter)** in one message from
`${CLAUDE_PLUGIN_ROOT}/skills/debugger/references/pack-guides.md`. Use them verbatim — they carry
the shared return contract and the read-only-by-frontmatter rule that a prose "do not fix" does not.

If agents return contradictory findings or no definitive file:line → escalate to `codex:codex-rescue` (foreground, diagnosis-only):

```
"Diagnose root cause only — do not apply any fixes.
 Context: [paste agent findings table]
 Error: [paste exact error]
 Focus: [file:line range]"
```

**L6+ — Full investigation.** Above, plus template **D (DB State Inspector)** from the same file.

### 1.4 While agents run

- Read files cited in the error stack — answers are usually there
- Grep for suspicious patterns in affected scope
- Compare with similar working implementations
- Form your own hypothesis

### 1.5 Consolidate hypotheses

```markdown
## Main Hypothesis
[Root cause with file:line]

## Evidence
- Agent 1: [finding]
- Agent 2: [finding]
- Own investigation: [finding]

## Alternative Hypotheses
1. [alternative]
2. [alternative]
```

### 1.6 Implement fix

**Hard gate:** when Step 5 writes a patch, apply
`${CLAUDE_PLUGIN_ROOT}/skills/planning/references/execution/tdd-policy.md`: a failing reproduction
test on the real seam, watched fail, before the fix. Debugging a behaviour regression is
`TDD: required`; any exception has to use one of the policy's explicit recorded statuses.

- Fix the SOURCE, not the symptom
- NEVER "while I'm here…" — scope creep kills debugging
- Run quality gates AFTER EACH fix
- After gates pass, apply `${CLAUDE_PLUGIN_ROOT}/references/shared/015-verification-gate.md` to capture stdout + exit code as evidence before closing the fix.

**Sequential mode (default — same file/flow):** ONE fix at a time.

```
Edit → Quality Gates → Pass? → Next fix
                       → Fail? → Analyze new error → Back to triage
```

**Parallel mode (independent issues, distinct areas):** spawn one `graph-powers:debugger` agent per area in same message. Each: read target → minimal fix → run gates → report file:line + gate output.

| Criterion | Parallel OK | Sequential required |
|---|---|---|
| Different files, no cross-imports | ✅ | — |
| Same router/component | — | ✅ |
| Frontend + backend of SAME flow | — | ✅ (backend first) |
| Schema change + code that uses schema | — | ✅ (schema first) |

After parallel fixes: full gate suite. If gates fail → resolve sequentially.

**If 2+ fixes failed in same area:** escalate to `codex:codex-rescue` for full fix. Then if still failing → switch to `/debug recover`.

### 1.7 Cleanup

After validated fixes:

| Check | Threshold | Action if failed |
|---|---|---|
| Cyclomatic complexity | No function > 10 branches | Extract sub-functions |
| Security | No new injection / auth gaps / PII exposure | Fix before closing |
| New dependencies | None added without deliberate choice | Audit or remove |
| Dead code | No commented-out blocks introduced | Remove |
| Root cause test | Fix has a regression test | Add test |

Auth/payments/PII fixes (L4+) → run `codex:codex-rescue` adversarial review:

```
"Run codex adversarial-review --scope working-tree.
 Focus: [security / auth / data integrity].
 Report findings only — do not apply fixes."
```

Present per `codex:codex-result-handling`: show issues → STOP → ask user which to fix.

After close: optionally `/evolve` to persist learnings.

---

## 2. Audit mode — `/debug audit` (full-stack 9 dimensions)

> Comprehensive audit. For targeted bug fixing use default mode.
> **PR/diff variant:** `/debug audit pr` — runs `codex adversarial-review --scope branch` first, then covers code-quality + dependencies + tech-debt + security on changed files only.

### 2.1 Setup

Run § 0.1, then — **only in `audit` mode** — load `${CLAUDE_PLUGIN_ROOT}/references/audit-agent-prompts.md` for the bounded audit batch and consolidation report template. No other mode opens it.

### 2.2 Quality gates baseline

Per `${CLAUDE_PLUGIN_ROOT}/references/shared/010-quality-gates.md` using config tooling. Also collect metrics:

Count source and test files with the **Glob tool**, not `find`: on Windows `find` resolves to
`C:\Windows\System32\find.exe`, which is a different program, and `wc` does not exist at all.

- Glob `**/*.{ts,tsx,astro,py,go}` under `${paths.backendRoot}` and `${paths.frontendRoot}` — count the results.
- Glob `**/*.{test,spec}.*` under the same roots — count those too.

```bash
git log --oneline -20
```

### 2.3 Severity classification

Per `${CLAUDE_PLUGIN_ROOT}/references/audit-agent-prompts.md` § Severity classification (P0-P3 + auto-flag thresholds: coverage < 80% on critical paths; cyclomatic > 10; CVE ≥ 7.0).

### 2.4 Dispatch the bounded audit batch

Use the prompts verbatim from `${CLAUDE_PLUGIN_ROOT}/references/audit-agent-prompts.md`. Dispatch
one base Evaluator and add only the specialists justified by the audited surfaces:

- **Base** — `graph-powers:evaluator` — D1-D5 and D7-D9, always.
- **Security** — `graph-powers:security-reviewer` — only when auth, API, personal data, payment,
  secrets or schema surfaces exist.
- **UX** — `graph-powers:ui-ux-designer` — D6, only when a frontend surface exists.

At most three agents, all `run_in_background: true` in the same message. Resolve `${paths.*}`
placeholders from config before spawning. Project lenses are folded into the compatible role, not
dispatched one by one.

### 2.5 While agents run

Run quality gates from § 2.2 and collect repo metrics.

### 2.6 Consolidate report

Produce `docs/AUDIT-REPORT-{YYYY-MM-DD}.md` per template in `${CLAUDE_PLUGIN_ROOT}/references/audit-agent-prompts.md` § Consolidation report template.

### 2.7 Codex adversarial cross-check (P0/P1)

When report surfaces P0/P1 → optionally run `codex:codex-rescue` with adversarial-review on those file:line targets. Show findings → STOP → ask user.

### 2.8 PR variant — `/debug audit pr`

Do not nest another adversarial command before § 2.4. Narrow the same bounded batch to changed files:
the Evaluator covers D3/D8/D9, the security specialist fires only on a sensitive surface, and UX only
on a changed frontend surface. Output per-file inline feedback with no executive summary.

---

## 3. Frontend mode — `/debug frontend` (static + agent-browser E2E)

Pack rules for `frontend-debug` — screenshot before the fix, snapshot before every ref action —
are in `${CLAUDE_PLUGIN_ROOT}/skills/debugger/references/pack-guides.md § Per-pack delta`.

### 3.1 Setup

Run § 0.1. Run `/prime frontend`.

### 3.2 Quality gates baseline

Run the smallest relevant unit-test filter first. For a Bun edit loop, use
`Skill("debugger") § JS/TS gate resolver` and its changed-only command, not the full suite. Then
run resolved type-check and lint once; only then reach for a browser.

### 3.3 Static diagnosis (parallel)

```
Agent 1 (graph-powers:frontend-specialist, background):
  - Component tree, hooks, rerender triggers
  - Token/layout issues, controlled-vs-uncontrolled state
  - Flickering, unstable rerenders, key warnings
  - Scope: $ARGUMENTS (after mode token)
  - Return: file:line + root cause hypothesis. DO NOT FIX.

Agent 2 (graph-powers:explorer, background):
  - Frontend ↔ backend integration paths used by the failing flow
  - Silent failures, latency issues, suspense interactions
  - Mutation error handling and post-mutation cache invalidation
  - Map routes involved in the scope and their existing E2E coverage
  - Return: handler/procedure + root-cause hypothesis + route/coverage gaps. DO NOT FIX.
```

### 3.4 Route + coverage consolidation

Reuse the single Explorer report from § 3.3; do not open a second discovery batch. The parent fills
mechanical omissions with Glob/Read under `${paths.frontendRoot}` and the existing E2E directories,
then produces `route | component | critical journey | tested? | test file | gap`. Missing evidence
is reported as unknown, never paid for with three near-identical scouts.

### 3.5 Browser journeys

`Skill("webapp-testing")` owns the browser entirely: pre-flight, named session, the core loop, the
`--cdp` path for authenticated routes, the verdict rules and cleanup. Load it and follow it — the
commands are not repeated here, and the CLI's own reference is one `skills get core` away.

Target: `${project.stagingUrl}` from config, overridable with `/debug frontend url=http://...`.

Per critical flow, and this is the part that belongs to `/debug` rather than to the skill:

1. Drive the journey and capture evidence at each step.
2. On an issue — document the snapshot, console, errors and network output **first**.
3. Write a unit reproduction test and watch it **fail**. That is the repro, not the screenshot.
4. Fix at the source, re-run the unit test to green, then re-drive the journey.
5. Run the gates before moving to the next flow.

Viewports worth one pass each: desktop `1280 720`, mobile `375 667`, tablet `768 1024` when the
layout has a breakpoint there.

**Per-step checklist:** element present · interaction produced the expected state · no error-level
console message · no uncaught page error · no failed application request · loading states appear
and clear · visible feedback after the action · navigation lands on the right state.

### 3.9 Report

```markdown
## E2E Test Report
Date: {date} | Target: {url} | Viewports: Desktop, Mobile

### Summary
| Metric | Value |
|---|---|
| Journeys tested | X |
| Snapshots captured | X |
| Issues found | X |
| Issues fixed | X |
| Issues pending | X |

### Journeys
| # | Journey | Status | Steps | Issues |

### Issues
| # | Severity | Journey | Step | Description | Evidence | Status |

### Coverage
| Area | Routes | Tested | % |
```

### 3.10 Cleanup

Close headless sessions; over `--cdp`, cleanup is doing nothing (`Skill("webapp-testing")`). Then
the final gates per `${CLAUDE_PLUGIN_ROOT}/references/shared/010-quality-gates.md`.

---

## 4. Backend mode — `/debug backend`

Run § 0.1, then default flow (§ 1) with focus on:
- API routes / handlers / middleware
- Service layer, validators (Zod or equivalent)
- Database access patterns
- External provider calls (timeouts, idempotency)

Spawn `code-archaeologist` + `regression-hunter` (background).

Loaded rules: whatever in `${rulesDir}/` matches the touched paths, plus `${rulesDir}/routing-supplements.md` if the project has one. List the directory; do not assume a filename.

---

## 5. Auth-DB mode — `/debug auth-db`

Run § 0.1, then default flow (§ 1) with focus on:
- Auth middleware, session, role/procedure levels
- Tenant isolation in WHERE clauses
- RLS policies, FK integrity, type/enum mismatches
- TOCTOU patterns, owner filter, webhook secret mismatch

Spawn `code-archaeologist` + `regression-hunter` + `db-state-inspector` (background).

Loaded rules: whatever in `${rulesDir}/` matches the data and auth paths this bug touches, plus `${rulesDir}/stability.md`. List the directory; do not assume a filename. Row-level security specifics are in the bug catalogue the skill already loaded.

---

## 6. Recover mode — `/debug recover` (failure recovery)

> Trigger: 2+ failed fix attempts on same hypothesis · quality gate fails 2× · user signals "this isn't working" · confidence < 3 after multi-file investigation.

If recovery was triggered by code-review feedback, read and apply `${CLAUDE_PLUGIN_ROOT}/commands/pr-review.md § 4.1` before the recovery protocol. That section is the canonical technical evaluation of feedback (implement / clarify / pushback), not a second skill or a locally restated checklist.

**Only in `recover` mode**, load `${CLAUDE_PLUGIN_ROOT}/references/recovery-protocol.md` and execute
it verbatim, Step 0 through Step 5. It is written there and nowhere else: this command once restated
the steps from memory, the restatement drifted into different steps under the same numbers, and an
agent obeying the command never ran the protocol. There is no second entry point either — a
standalone `/recover` command existed for exactly that reason and was removed.

---

## 7. Escalation hierarchy

The triggers that send you back to Step 1, and the ≥3-attempt architecture rule, are in
`Skill("debugger") § Stopping & escalation`. What this command adds is the order of outside help:

1. Two failed fixes in the same area → `codex:codex-rescue` for a full fix.
2. Contradictory agent findings → `codex:codex-rescue`, diagnosis mode.
3. Architecture-level blocker → `graph-powers:evaluator` Mode 3.
4. The same hypothesis back after every decomposition, no architecture signal →
   `graph-powers:evaluator` Mode 5, the blind second opinion, called from recovery Step 4.
5. Exhausted → `/debug recover`, then the user decides.

---

## 8. Auto mode

If `auto` token in `$ARGUMENTS`: complete default flow (§ 1), then run AutoResearch Loop per `${CLAUDE_PLUGIN_ROOT}/references/shared/100-autoresearch-loop.md` on skills used in this session.
