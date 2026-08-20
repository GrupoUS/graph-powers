---
description: "Diagnose and fix a defect — error, crash, stack trace, failing test, 500, hydration mismatch, CI gone red, or behaviour that changed after a deploy. Use when the user reports something broken, pastes an error, says a test is failing, says it worked yesterday, or asks why staging differs from local. Modes (positional) — default: triage and fix · audit: 9-dimension full-stack audit · frontend: React/UI plus browser E2E · backend: API and services · auth-db: auth, permissions, RLS · recover: after 2+ failed attempts. Do not use to add behaviour that never worked (/implement), to judge code that already works (/pr-review), or to prove gates pass (/verify)."
workflow_type: routing
---

# /debug — Intelligent Debugging

**ARGUMENTS**: $ARGUMENTS

> **Read before step 0 — never reconstruct these from memory:** `${CLAUDE_PLUGIN_ROOT}/references/shared/000-config-loader.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/005-superpowers-bootstrap.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/010-quality-gates.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/015-verification-gate.md`
> Read `${CLAUDE_PLUGIN_ROOT}/references/shared/020-complexity-routing.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/030-agent-assignment-matrix.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/040-wisc-context-load.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/070-parallel-agent-spawn.md`
> Read `${CLAUDE_PLUGIN_ROOT}/references/shared/100-autoresearch-loop.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/120-skill-invocation-order.md`

> First positional arg = mode. Examples:
> ```
> /debug                    # default — triage + investigate + fix
> /debug audit              # full-stack audit (9 dimensions, 4 parallel agents)
> /debug frontend           # static + agent-browser E2E
> /debug backend            # API/service/handler/middleware
> /debug auth-db            # auth, permissions, tenant isolation, RLS
> /debug recover            # failure recovery (after 2+ failed attempts)
> ```
> Anything after the mode token is forwarded as scope (e.g., `/debug audit scope=payments`).

---

## Stopping Conditions (apply to ALL modes)

- STOP proposing fixes before root cause investigation
- STOP after 3 failed fix attempts → switch to `/debug recover`
- ASK if error affects production data or requires schema migration
- ASK if fix scope expands beyond originally reported error

---

## Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST.
```

If investigation isn't complete, you cannot propose corrections.

### Debugger skill loading (mandatory)

This plugin ships `${CLAUDE_PLUGIN_ROOT}/skills/debugger/SKILL.md` alongside this command; inside a plugin it is namespaced, so a same-named personal skill cannot shadow it and `Skill("debugger")` resolves here. Load the skill body for pack selection, **Phases 0-7** (pre-flight → diagnose and reproduce → parallel research → hypothesis selection → instrument and fix through the superpowers chain → verification gate → evidence confirmation → cleanup and post-mortem), and its NEVER constraints. Its References section is an **index to consult**, not a list to open: pick the row the phase calls for. Browser verification lives in `Skill("webapp-testing")`, loaded only when the reproduction needs a browser. Use **this file** for mode-specific orchestration (`audit`, `frontend`, `recover`, …). Do not paste long catalogues here — defer to the skill's References table.

---

## 0. Mode dispatch

Parse first positional token from `$ARGUMENTS`:

| Token | Section to execute |
|---|---|
| (none) / `debug` / `auto` | § 1 (default flow) |
| `audit` / `full` | § 2 (audit mode) |
| `frontend` / `ui` / `react` | § 3 (frontend mode) |
| `backend` / `api` | § 4 (backend mode) |
| `auth-db` / `auth` / `db` / `permissions` | § 5 (auth-db mode) |
| `recover` | § 6 (recovery mode) |

Modes share the **§ 0.1 Setup** preamble.

### 0.1 Setup (every mode)

Load the superpowers method layer **before** the the project debugger knowledge layer (per `${CLAUDE_PLUGIN_ROOT}/references/shared/005-superpowers-bootstrap.md` + § 12):

```typescript
Skill("superpowers:using-superpowers");        // meta — announce-before-action
Skill("superpowers:systematic-debugging");     // 4-phase root-cause discipline (observe → hypothesize → test → conclude)
Skill("debugger");                     // the project anti-pattern catalog, packs, references, superpowers debug chain
```

Chain rationale: `systematic-debugging` sets the investigation method (no fix without root cause); `graph-powers:debugger` provides project-specific bug patterns + Negative Constraints + the wired superpowers debug chain (its phases invoke TDD / dispatching-parallel-agents / verification-before-completion). Both load — they do not conflict. (`graph-powers:debugger`, not `graph-powers:debugger`: precedence personal > project shadows a same-named project skill — see § 0.42 header.)

Read `.graph-powers/config.json` (paths, tooling, gates, `${rulesDir}`). For project-specific anti-patterns, load via `Skill("debugger")` → `${CLAUDE_PLUGIN_ROOT}/skills/debugger/references/anti-patterns.md` (already loaded by debugger skill above).

Run baseline quality gates from `${CLAUDE_PLUGIN_ROOT}/references/shared/010-quality-gates.md` using `${tooling.typeChecker}` / `${tooling.linter}` / `${tooling.testRunner}`.

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
| `hydration mismatch` | SSR/CSR divergence | Check effects vs render |
| Cache stale / stale-while-revalidate | Client query config | staleTime = refetchInterval |
| `ERR_MODULE_NOT_FOUND` | Import/export | Check barrel `index.ts` |
| `FORBIDDEN` / `401` / `403` | Auth/role | Check procedure level / RLS |
| `connection timeout` / `ECONNREFUSED` | Infra/DB | Check connection string + pool |

**Known-pattern shortcut.** Before investigating, check:
- `${rulesDir}/stability.md` (Checklist A-L)
- Tier 2 domain rules (auto-loaded via routing matrix)
- `Skill("debugger")` → `${CLAUDE_PLUGIN_ROOT}/skills/debugger/references/anti-patterns.md` (project anti-patterns)
- Recent breaking changes in dependencies (`mcp__tavily__tavily_search` if needed)

If error matches a known pattern → apply documented fix directly (L1-L2), no agents.

### 1.2 Complexity classification

Per `${CLAUDE_PLUGIN_ROOT}/references/shared/020-complexity-routing.md`.

### 1.3 Investigation by complexity

**L1-L2 — Direct fix.** Read file → identify root cause → apply minimal fix → run gates.

**L3 — Single agent.** Spawn 1 `graph-powers:explorer` (foreground): investigate root cause, return a findings
table with file:line. Read-only by frontmatter, not by instruction — `anti-patterns.md § Agent
misuse` is explicit that a review task never goes to a write-capable subagent, and a prompt
saying "do not fix" is a request, not a permission. Fixing is a separate dispatch, after the
root cause is named.

**L4-L5 — Parallel agents.** Before spawning, invoke `Skill("superpowers:dispatching-parallel-agents")` to enforce distinct scope + shared return contract. Spawn in same message:

```
code-archaeologist (graph-powers:explorer, background):
  - Find exact file:line where flow breaks
  - git log --oneline -10 -- <affected-files> for recent regressions
  - Map dependency chain
  - Return findings table (# | Finding | Confidence 1-5 | Source | Impact). DO NOT FIX.

regression-hunter (graph-powers:explorer, background):
  - Read ${CLAUDE_PLUGIN_ROOT}/skills/debugger/references/methodology.md (or pack-guides.md)
  - Cross-check stability rules + Skill("debugger") ${CLAUDE_PLUGIN_ROOT}/skills/debugger/references/anti-patterns.md
  - If MATCH: return pattern + root cause + fix guidance
  - If NO MATCH: top-3 hypotheses with evidence for/against. DO NOT FIX.
```

If agents return contradictory findings or no definitive file:line → escalate to `codex:codex-rescue` (foreground, diagnosis-only):

```
"Diagnose root cause only — do not apply any fixes.
 Context: [paste agent findings table]
 Error: [paste exact error]
 Focus: [file:line range]"
```

**L6+ — Full investigation.** Above + `db-state-inspector` (graph-powers:debugger, background): schema check, FK indexes, type exports, RLS/tenant boundaries, auth procedure levels.

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

**Hard gate (L3+):** Before writing any patch, invoke `Skill("superpowers:test-driven-development")`. The skill requires a **failing reproduction test** that demonstrates the bug. No patch lands without a red test first. L1-L2 trivial fixes (single-line typo, exact-pattern from `${CLAUDE_PLUGIN_ROOT}/skills/debugger/references/anti-patterns.md`) are exempt — note the exemption explicitly.

- Fix the SOURCE, not the symptom
- NEVER "while I'm here…" — scope creep kills debugging
- Run quality gates AFTER EACH fix
- After gates pass, invoke `Skill("superpowers:verification-before-completion")` to capture stdout + exit code as evidence before closing the fix.

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

Run § 0.1, then — **only in `audit` mode** — load `${CLAUDE_PLUGIN_ROOT}/references/audit-agent-prompts.md` for the 4 agent prompts and consolidation report template. No other mode opens it.

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

### 2.4 Spawn 4 parallel agents

Use prompts verbatim from `${CLAUDE_PLUGIN_ROOT}/references/audit-agent-prompts.md`:

- **Agent 1** — `graph-powers:evaluator` (Mode 3) — Architecture & Structure (D1-D2)
- **Agent 2** — `graph-powers:debugger` — Code Quality (D3 + D8 dependencies + D9 tech-debt)
- **Agent 3** — `graph-powers:debugger` — Documentation + Missing Flows (D4-D5)
- **Agent 4** — `graph-powers:frontend-specialist` — UX + Tests/CI (D6-D7)

All `run_in_background: true`, same message. Resolve `${paths.*}` placeholders from config before spawning.

### 2.5 While agents run

Run quality gates from § 2.2 and collect repo metrics.

### 2.6 Consolidate report

Produce `docs/AUDIT-REPORT-{YYYY-MM-DD}.md` per template in `${CLAUDE_PLUGIN_ROOT}/references/audit-agent-prompts.md` § Consolidation report template.

### 2.7 Codex adversarial cross-check (P0/P1)

When report surfaces P0/P1 → optionally run `codex:codex-rescue` with adversarial-review on those file:line targets. Show findings → STOP → ask user.

### 2.8 PR variant — `/debug audit pr`

Before § 2.4, run `codex adversarial-review --scope branch` for an independent baseline diff review. Then narrow the 4 agents to D3 + D8 + D9 + security on changed files only. Output: per-file inline feedback (no exec summary).

---

## 3. Frontend mode — `/debug frontend` (static + agent-browser E2E)

**Iron Laws (frontend):**
```
NO FIXES WITHOUT STATIC DIAGNOSIS + VISUAL EVIDENCE FIRST.
NO INTERACTION WITHOUT A SNAPSHOT BEFORE IT.
NO FIX WITHOUT A SNAPSHOT/SCREENSHOT AS EVIDENCE.
NO FIX WITHOUT A PASSING UNIT REPRODUCTION TEST.
```

### 3.1 Setup

Run § 0.1. Run `/prime frontend`.

### 3.2 Quality gates baseline

Run unit-test suite first (cheap, catches logic errors): `${tooling.testRunner}` against frontend project. Then `${tooling.typeChecker}` and `${tooling.linter}`. Only proceed to browser if unit tests pass.

### 3.3 Static diagnosis (parallel)

```
Agent 1 (graph-powers:frontend-specialist, background):
  - Component tree, hooks, rerender triggers
  - Token/layout issues, controlled-vs-uncontrolled state
  - Flickering, unstable rerenders, key warnings
  - Scope: $ARGUMENTS (after mode token)
  - Return: file:line + root cause hypothesis. DO NOT FIX.

Agent 2 (graph-powers:debugger, background):
  - Frontend ↔ backend integration paths used by the failing flow
  - Silent failures, latency issues, suspense interactions
  - Mutations wrapped in try-catch (stability rule J)
  - Post-mutation cache invalidation
  - Return: handler/procedure with potential issues + hypothesis. DO NOT FIX.
```

### 3.4 Route + coverage discovery (parallel)

```
Agent 1 (graph-powers:explorer, background):
  - Map all routes recursively under ${paths.frontendRoot}
  - List: path, component, functionality
  - Identify critical user flows (auth, CRUD, integrations, settings)
  - List expected interactions per flow
  - Return: route table + prioritized journeys

Agent 2 (graph-powers:explorer, background):
  - Map existing E2E coverage (look for e2e/, tests/e2e/, playwright/, agent-browser/ — accept any historical layout)
  - For each test: routes covered, assertions, interactions tested
  - Cross-reference; identify routes WITHOUT coverage
  - Return: coverage table (route | tested? | file | quality) + gaps list
```

### 3.5 Browser session

Browser stack: `vercel-labs/agent-browser` CLI invoked via Bash. Full reference: `${CLAUDE_PLUGIN_ROOT}/skills/webapp-testing/references/browser-setup.md`.

Pre-flight (mandatory): `bunx agent-browser --version`. If it fails → STOP, do not silently fall back.

Resolve target URL: `${project.stagingUrl}` from config (override via `/debug frontend url=http://...`).

```bash
bunx agent-browser open "<the URL, substituted before you run this — resolve it from ${project.stagingUrl}; a shell variable is not set anywhere and expands to nothing>"
bunx agent-browser snapshot -i -c              # accessibility baseline, interactive + compact
bunx agent-browser console                     # any error-level messages collected since open
```

### 3.6 Journey loop (per critical flow)

```bash
# 1. Navigate (or just continue in the existing session)
bunx agent-browser open "<the URL, substituted before you run this>"

# 2. Snapshot (ALWAYS before any ref-based interaction — refs go stale on DOM mutation)
bunx agent-browser snapshot -i -c

# 3. Interact using refs from snapshot
bunx agent-browser click @e3
bunx agent-browser fill  @e4 "value"
bunx agent-browser select @e5 "option"

# 4. Wait
bunx agent-browser wait --text "Success"
bunx agent-browser wait --url "**/dashboard"
bunx agent-browser wait --load networkidle

# 5. Capture
bunx agent-browser snapshot -i -c
bunx agent-browser screenshot ".graph-powers/logs/<flow>-step.png"   # only for visual regression
bunx agent-browser screenshot ".graph-powers/logs/<flow>-step.png" --annotate  # numbered labels

# 6. Verify
bunx agent-browser console                     # error-level → FAIL
bunx agent-browser errors                      # uncaught page errors → FAIL
bunx agent-browser network requests --filter "api-staging"  # 4xx/5xx → FAIL

# 7. If issue:
#   a) Document: snapshot + console + errors + network output
#   b) Write unit reproduction test → must FAIL (confirms repro)
#   c) Fix in source
#   d) Re-run unit test → must PASS
#   e) Re-test E2E: navigate → snapshot → interact → snapshot
#   f) Run gates (type-check + lint)
```

### 3.7 Viewports

```bash
bunx agent-browser set viewport 1280 720       # desktop
bunx agent-browser set viewport 375 667        # mobile
bunx agent-browser set viewport 768 1024       # tablet (optional)
# Or full device emulation:
bunx agent-browser set device "iPhone 15 Pro"
```

There is no bare `resize` subcommand — always `set viewport`.

### 3.8 Per-step verification

- [ ] Element exists/visible (snapshot)
- [ ] Interaction produces expected state (snapshot)
- [ ] No JS errors (`bunx agent-browser console`)
- [ ] No uncaught page errors (`bunx agent-browser errors`)
- [ ] No failed app requests (`bunx agent-browser network requests`)
- [ ] Loading states appear/disappear
- [ ] Visual feedback after actions (toast/alert)
- [ ] Navigation returns to correct state

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

```bash
bunx agent-browser close --all   # headless sessions ONLY; over `--cdp` this kills the person's signed-in browser
```

Run final quality gates per `${CLAUDE_PLUGIN_ROOT}/references/shared/010-quality-gates.md`.

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

Loaded rules: whatever in `${rulesDir}/` matches the data and auth paths this bug touches, plus `${rulesDir}/stability.md`. List the directory; do not assume a filename. Plus, **when the bug touches row-level security**, `Skill("debugger")` → `${CLAUDE_PLUGIN_ROOT}/skills/debugger/references/anti-patterns.md` (RLS specifics).

---

## 6. Recover mode — `/debug recover` (failure recovery)

> Trigger: 2+ failed fix attempts on same hypothesis · quality gate fails 2× · user signals "this isn't working" · confidence < 3 after multi-file investigation.

If the recovery was triggered by code-review feedback (codex review P0/P1, evaluator REVISION_REQUIRED, user pointing to a specific reviewer note), invoke `Skill("superpowers:receiving-code-review")` **before** reading the recovery protocol. The skill enforces technical evaluation of feedback (implement / clarify / pushback) instead of blind agreement.

**Only in `recover` mode**, load `${CLAUDE_PLUGIN_ROOT}/references/recovery-protocol.md` and execute its five steps verbatim.
They are written there and nowhere else — this command used to restate them from memory, and the
restatement had drifted into five different steps under the same numbers, so an agent obeying the
command never ran the protocol and an agent reading the file contradicted the command.

Anti-patterns: looping past 2 attempts · skipping the write-up in Step 1 · reverting without showing
the diff · escalating with a question too vague to answer.

---

## 7. Agent / mode matrix

| Bug type | Mode | Sub-agents | Skill |
|---|---|---|---|
| API / handler error | `backend` | code-archaeologist + regression-hunter | `graph-powers:debugger` |
| UI / component / hydration | `frontend` | (per § 3) + frontend-specialist + debugger | `graph-powers:debugger` |
| Auth / permissions / RLS | `auth-db` | code-archaeologist + regression-hunter + db-state-inspector | `graph-powers:debugger` |
| Database / schema / migration | `auth-db` | code-archaeologist + db-state-inspector | `graph-powers:debugger` |
| Performance | (run `/perf` instead) | — | `performance-optimization` |
| Full audit | `audit` | 4 parallel (evaluator/debugger/debugger/frontend-specialist) | all |
| Failure recovery | `recover` | evaluator (Mode 3) | — |

---

## 8. Escalation hierarchy

Before stopping, escalate in this order:
1. 2+ failed fixes in same area → `codex:codex-rescue` for full fix
2. Contradictory agent findings → `codex:codex-rescue` diagnosis mode
3. Architecture-level blocker → `graph-powers:evaluator` (Mode 3)
4. All escalations exhausted → `/debug recover` → user decides

**Hard STOP signs:**
- Proposing a fix before finding root cause
- Multiple simultaneous changes in same flow
- "Just try this and see"
- Skipping quality gate verification
- Ignoring evidence contradicting your hypothesis

---

## 9. Auto mode

If `auto` token in `$ARGUMENTS`: complete default flow (§ 1), then run AutoResearch Loop per `${CLAUDE_PLUGIN_ROOT}/references/shared/100-autoresearch-loop.md` on skills used in this session.
