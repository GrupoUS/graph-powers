---
description: "Diagnose and fix a defect — error, crash, failing test, 500, hydration mismatch, CI failure or regression. Modes: default triage/fix; audit; frontend; backend; auth-db; recover. Do not use for new behavior (/implement), review (/pr-review), or gate proof (/verify)."
workflow_type: routing
---

> Hermes: first load `skill_view("graph-powers:graph-engineering")` for native calls and host-policy limits. `content/` paths are `file_path` values relative to the common registered-document parent. Source tools/model frontmatter is not host enforcement.

# /debug

**ARGUMENTS:** the user-provided arguments. First token is the mode; remaining text is scope.

| Token | Route |
|---|---|
| none / `debug` / `auto` | § 1 default |
| `audit` / `full` | § 2 bounded nine-dimension audit |
| `frontend` / `ui` / `react` | § 3 frontend diagnosis and E2E |
| `backend` / `api` | § 4 default with service/API focus |
| `auth-db` / `auth` / `db` / `permissions` | § 5 default with auth/data focus |
| `recover` | § 6 recovery |

Resource-only symptoms route to `/perf resources`; these modes diagnose a defect.

## 0. Setup

Read `.graph-powers/config.json`. Load `skill_view("graph-powers:debugger")` for Steps 0–6, root-cause catalogue, TDD and escalation; load matching `${rulesDir}` files.

Read `content/references/shared/010-quality-gates.md` to resolve declared gates.

Only for JS/TS or Oxfmt-supported diagnostic scope, before any edit, read and apply `content/references/shared/130-typescript7-oxc-gates.md`.

Use `/prime` only for the affected frontend, backend, or fullstack context.

## 1. Default: triage, prove, fix

Classify the symptom, inspect its cited path and comparable working code, then state root cause with file:line and alternatives. A known documented pattern may take a direct L1-L2 fix.

### 1.3 Investigation route

- L1-L2: reproduce, make the smallest source fix, and run the focused reproduction plus declared changed-boundary gate.
- Only for L3, read `content/references/shared/030-agent-assignment-matrix.md`; dispatch `graph-powers:explorer (background):` investigate only and return file:line evidence.
- Only for L4-L5, read `content/references/shared/070-parallel-agent-spawn.md`; dispatch debugger pack B (archaeologist) and C (regression hunter) together. Add pack D (DB state) for L6+ or data state.

Templates A/B/C/D are defined only in `content/skills/debugger/references/pack-guides.md`; load the selected template rather than reconstructing a pack.

Consolidate evidence before writing. A behavior regression needs the TDD status required by `skill_view("graph-powers:debugger")`; fix the cause, not its symptom. After a focused gate passes, run each broader applicable gate once. Reuse green evidence only while its files, configuration and relevant environment remain valid; otherwise rerun the affected gate. Two failed fixes in one area or contradictory evidence escalate to `codex:codex-rescue`; repeated failure routes to § 6. For auth, payments, PII or destructive-data changes, obtain the required adversarial review and user decision before further fixes.

## 2. `audit`

Only in `audit`, load `content/references/audit-agent-prompts.md`. Run declared baseline gates and a bounded batch: evaluator always; security only for auth/API/data/payment/secrets/schema; UX only for frontend. `audit pr` narrows that same batch to changed files and reports inline findings. Use the reference severity and report template; P0/P1 gets the optional Codex cross-check, then stop for the user.

## 3. `frontend`

Run § 0 and `/prime frontend`; dispatch `graph-powers:frontend-specialist` and `graph-powers:explorer` once for component/state and route/coverage evidence. Load `skill_view("graph-powers:webapp-testing")` only when a browser reproduction is needed. Capture evidence, make the unit reproduction fail, fix, prove it green, re-drive the journey, and run applicable gates once. Report journeys, viewport coverage, evidence, fixed and pending issues.

## 4. `backend`

Use § 1 with routes, handlers, middleware, validators, services, data access and provider idempotency/timeouts in scope. Dispatch packs B+C; load only matching rules and any existing routing supplement.

## 5. `auth-db`

Use § 1 with auth/session/roles, tenant filters, RLS, FK/type integrity, TOCTOU and webhook verification in scope. Dispatch packs B+C+D and load only matching auth/data rules.

## 6. `recover`

When two attempts, two gate failures, low confidence after a multi-file investigation, or explicit user signal trigger recovery, load `content/references/recovery-protocol.md` only in `recover` mode and execute Steps 0–5 verbatim. If review feedback started recovery, first read `content/commands/pr-review.md` § 4.1.

## 7. Stop

Return cause, changed paths, reproduction/gate evidence, remaining risk, and exactly the next needed decision. Never commit or expand the task.

## 8. Auto mode

If auto token in the user-provided arguments: complete default flow (§ 1), then read `content/references/shared/100-autoresearch-loop.md` only if its trigger is evidenced; otherwise stop with the validated fix.
