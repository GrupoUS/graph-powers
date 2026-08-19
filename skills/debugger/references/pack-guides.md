# Pack Execution Guides

Detailed execution flows, key rules, and common patterns for each debug pack, plus the **Step 2 parallel-research templates** the packs dispatch.

> **Step mapping:** each pack's numbered flow below maps onto the SKILL.md Step 0–6 chain — `Pre-flight (Step 0)` → `Diagnose: loop → reproduce & minimise → hypothesise (Steps 1–3, see references/diagnose.md)` → `Parallel sub-agents (Step 2, templates below)` → `Instrument (Step 4)` → `Fix + regression test (Step 5, mandatory Skill("superpowers:systematic-debugging") → Skill("superpowers:test-driven-development"))` → `Verify & cleanup + browser/DB evidence (Step 6)`. Always finish Step 1 (a runnable reproducer) before launching sub-agents.

---

## 8a. `frontend-debug`

**Scope:** React/UI regressions, hydration errors, interaction failures, visual glitches.

**Execution flow:**
1. Pre-flight (Step 0) + agent-browser check
2. Build reproducer (Step 1) → launch 3 sub-agents: Evidence Collector + Code Archaeologist + Regression Hunter
3. While agents work, run quality gates as baseline
4. Consolidate findings → select hypothesis (Step 3)
5. Apply minimal fix (Step 5)
6. Verification gates (Step 6)
7. Browser evidence: screenshot + console + network + responsive viewports
8. Report

**Key rules:**
- NEVER fix without capturing the initial screenshot first
- NEVER interact with the page without calling `agent-browser snapshot` first (refs invalidate after DOM changes)
- Choose browser mode: headless for public pages, CDP for authenticated pages (see `Skill("webapp-testing")` → `../../webapp-testing/references/browser-setup.md`)
- Default target: `${project.stagingUrl}` from `.graph-powers/config.json` (override with `url=` argument)
- In CDP mode, do NOT call `agent-browser close` — it kills the user's Chrome session

**Common frontend patterns:**
- `Select controlled/uncontrolled` → `value={undefined}` transitioning to string
- Hydration mismatch → dynamic values computed differently on server vs client
- Infinite re-render → `useEffect` dep array includes an unstable reference (new object/array each render)
- Loading skeleton stuck → query never resolves, check `staleTime` and `enabled` condition

---

## 8b. `backend-debug`

**Scope:** Hono/tRPC procedure failures, service errors, mutation side effects.

**Execution flow:**
1. Pre-flight (Step 0)
2. Build reproducer (Step 1) → launch 2 sub-agents: Code Archaeologist + Regression Hunter
3. If mutation involved, also launch DB State Inspector
4. Consolidate → hypothesis (Step 3)
5. Minimal fix (Step 5)
6. Verification gates (Step 6)
7. Database validation (psql)
8. Report

**Key rules:**
- Always verify procedure boundary: the generic authenticated procedure vs the admin one vs the tenant-scoped one
- Check the Zod input schema matches what the frontend sends
- Verify `Promise.all` vs sequential for batch operations
- `db.transaction()` is the correct atomicity primitive whenever the driver supports it. A "never use transactions" rule in a project's docs usually applies to a serverless **HTTP** driver only — read the import in the connection module before citing it, and never de-atomize call sites to satisfy a rule you have not verified still applies.
- Always guard `.returning()[0]` against empty arrays

**Common backend patterns:**
- `No transactions support in <driver>` → the connection module is on the HTTP-only driver; fix the driver import, do not de-atomize the callers
- `Cannot read properties of undefined` after insert → unguarded `.returning()[0]`
- HTTP 500 on mutation → same as above, or unhandled async rejection
- `TRPCError UNAUTHORIZED` → procedure context not forwarding userId

---

## 8c. `auth-db-debug`

**Scope:** Authentication, role/permission mismatches, tenant isolation failures.

**Execution flow:**
1. Pre-flight (Step 0)
2. Build reproducer (Step 1) → launch 2 sub-agents: Code Archaeologist + Regression Hunter
3. Launch DB State Inspector to verify user/tenant/role state
4. Consolidate → hypothesis (Step 3)
5. Minimal fix (Step 5)
6. Verification gates (Step 6)
7. Database validation: verify role assignments, tenant boundaries, FK integrity
8. Report

**Key rules:**
- Verify the tenant-resolution chain the context builder uses: team membership → owner lookup → admin fallback
- Every UPDATE must include the tenant predicate (`eq(table.tenantId, ctx.tenant.id)`) — TOCTOU ownership check
- Verify the auth provider's webhook signing secret matches between environments
- Check the auth middleware matcher covers the affected route

**Common auth patterns:**
- `auth()` returns null → middleware matcher missing the route
- Tenant record not found → a corrupted auto-created row; repair the broken link rather than deleting the row
- Cross-tenant data leak → missing tenant filter in the WHERE clause
- Webhook 400 → env mismatch between local `.env` and production/staging

---

## 8d. `systematic-audit`

**Scope:** Full cross-layer stability sweep. Post-release hardening or periodic health check.

**Execution flow:**
1. Pre-flight (Step 0) + agent-browser check
2. Launch 4 sub-agents:
   - Evidence Collector (browser baseline of critical flows)
   - Code Archaeologist (scan for unstable patterns across the codebase)
   - Regression Hunter (cross-reference MEMORY.md for known issues)
   - DB State Inspector (FK integrity, orphaned rows, missing indexes)
3. **Inventory first, NO fixes** — classify all findings as P0/P1/P2/P3
4. Present the findings table to the user for prioritization
5. Fix P0 issues one at a time, verifying after each; then P1, then P2
6. Final gates: `${tooling.commands.typeCheck} && ${tooling.commands.lint} && ${tooling.commands.test} && ${tooling.commands.build}`
7. Browser evidence of critical flows post-fix
8. Full report with remaining P3 items logged

**Key rules:**
- NEVER fix during the inventory phase
- One fix at a time, validate after each
- Track progress with TaskCreate/TaskUpdate
- Cross-reference `${rulesDir}/stability.md` (Stability Audit Checklist A–L) + `references/methodology.md § Security checklist`

---

## Parallel-research templates (Step 2)

Dispatched after Step 1 produces a runnable reproducer + ≥3 falsifiable hypotheses. Invoke `Skill("superpowers:dispatching-parallel-agents")` first to enforce distinct scope + a shared return contract, then launch.

**Shared dispatch contract (applies to every template below):** `run_in_background: true`; read-only (Code Archaeologist + Regression Hunter use `subagent_type: "explorer"`; Evidence Collector + DB State Inspector use `subagent_type: "debugger"` but capture-only — **fix nothing**); return < 2000 tokens; findings as a `| # | Finding | Confidence (1-5) | Source | Impact |` table where applicable; pass the bug symptom + failing URL/procedure + affected files in the prompt.

**Which agents per pack:** all packs → B + C. `frontend-debug` / `systematic-audit` → add A. `backend-debug` / `auth-db-debug` → add D.

### A — Evidence Collector (browser state; `frontend-debug` + `systematic-audit`)
Browser mode: **public page → headless**; **authenticated page → `--cdp 9222` attach** (keeps the user's Chrome session — do NOT `close`).
```
MODE A (headless): bunx agent-browser open "[URL]" → snapshot -i -c → screenshot e2e-screenshots/debug/00-initial.png
                   → eval "document.querySelector('#react-error-overlay')?.textContent || 'no overlay'" → get title/url → close
MODE B (CDP):      bunx agent-browser --cdp 9222 open "[URL]" → snapshot -i -c → screenshot → eval(overlay) → console → errors  (NO close)
RETURN: browser mode used · screenshot path · React error-overlay text if present · page URL + title. Fix nothing.
```

### B — Code Archaeologist (all packs)
```
1. Search the codebase for the failing component / route / procedure; pin the EXACT file:line where the error originates.
2. git log --oneline -10 -- <affected-files> for the last commits.
3. Map the dependency chain: API handlers → data-layer queries → auth middleware → input validators.
4. Flag recent changes that could have caused the regression.
5. `systematic-audit` pack only — structural sweep per references/structural-quality.md: files > 1000 lines,
   ad-hoc branching hotspots (one-off booleans / scattered special cases in shared flows), near-duplicate
   helpers vs Canonical Homes. Inventory only — fix nothing; classify findings like any other (P0-P3).
RETURN: findings table · affected file:line ranges · last 3 commits touching them · dependency chain · knowledge gaps.
```

### C — Regression Hunter (all packs)
```
1. Scan references/anti-patterns.md (Negative Constraints index + bug catalog) and the Common Root Causes Catalog in SKILL.md.
2. Search MEMORY.md for matching patterns (project auto-memory).
3. Check ${rulesDir}/stability.md (Stability Audit Checklist A–L) for relevant rules.
MATCH found  → return pattern name, root cause, recommended fix, file guidance.
NO MATCH     → generate top-3 hypotheses ranked by probability, each with evidence for/against + an investigation step.
RETURN: MATCHED / NO_MATCH; matched → pattern + fix guidance; not matched → ranked hypotheses with investigation plan.
```

### D — DB State Inspector (`backend-debug` + `auth-db-debug`; replaces A)
```
1. Read the schema definitions under ${paths.schemaRoot} to understand the table structure.
2. Construct targeted SELECT queries to verify data state.
3. Check for orphaned rows, missing FK references, tenant_id gaps; verify enum values match the schema; confirm indexes exist for all FK columns.
IMPORTANT: do NOT run psql directly — return the queries you would run; the lead agent executes them after review.
RETURN: table structure summary · diagnostic queries (ready to run) · suspected data inconsistencies.
```
