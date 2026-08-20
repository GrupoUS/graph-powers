# Steps 4–6 — Fix: Instrument → Fix + regression test → Verify & cleanup

> Back half of the **diagnose-first** chain (mattpocock `diagnosing-bugs` §4–§6). Front half (build loop → reproduce & minimise → hypothesise, Steps 1–3) is `references/diagnose.md`. Steps 4–5 run **inside** the Superpowers chain — `Skill("superpowers:systematic-debugging")` opens it and mandates `Skill("superpowers:test-driven-development")`. Both Iron Laws apply: *NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST* and *NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST.* The sections below are worked worked examples; the discipline lives in the Superpowers skills.

---

## Step 4 — Instrument (P4)

Map each probe to a **specific prediction** from a Step 3 hypothesis (which value should appear here? what disproves the hypothesis if it doesn't?). Change **one variable per probe**.

- Prefer a real debugger or REPL inspection over logs. If logs are required, tag every line with the Step 3 prefix so cleanup is one grep:
  ```ts
  console.error("DEBUG_BUG_<ID>", { stage: "tRPC ctx", input, userId: ctx.userId });
  ```
- **Never log everything** — probe only at the boundaries that distinguish competing hypotheses.
- **Performance regressions:** measure and bisect, do not log. Logs are usually wrong about where time goes — measure first, fix second.

---

## Step 5 — Fix + regression test (P5)

### 1. Create the failing test on the real seam (RED)
The test must exercise the **actual production code path** that fails — not a happy-path stub, not a private helper called with synthetic args. If no correct seam exists, refactor to expose one *before* writing the test (still inside `Skill("superpowers:test-driven-development")` RED).
```typescript
it("should reject an empty tenantId", () => {
  expect(() => service.create({ tenantId: "" })).toThrow();
});
```
Watch it fail RED. Confirm the failure mode matches the Step 1 reproducer.

### 2. Implement single fix (GREEN)
- ONE change at a time. No "while I'm here" improvements. Smallest change that turns the test green.
- `Read` before edit; re-run type-check after each edit — revert if new failures appear.

### 3. Verify gates
```bash
${tooling.commands.typeCheck} && ${tooling.commands.lint} && ${tooling.commands.test}
```

### Root cause tracing — 5-step backward trace
Trace backward through the call chain to the original trigger, then fix at source.
```
1. Observe Symptom        → "column tenant_id does not exist"
2. Find Immediate Cause   → db.select().where(eq(metrics.tenant_id, id))
3. Ask: What Called This? → metricsRouter.listForTenant(id)
4. Keep Tracing Up        → id = undefined — context not yet loaded
5. Find Original Trigger  → Query fires before auth resolves
```
```typescript
// Fix at source, not at the symptom:
const { data } = trpc.metrics.listForTenant.useQuery(
  { tenantId },
  { enabled: !!tenantId } // ← gate the query until the id exists
);
```

### Git bisect for regressions
```bash
git bisect start
git bisect bad                    # Current is broken
git bisect good HEAD~20           # This was working
# Git guides you to the exact commit
git bisect reset
```

### Test-pollution bisection
When something shows up during a test run but you do not know which test creates the polluted state (file, env var, database row, lockfile):
```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/debugger/scripts/find_polluter.py '.git' '${paths.backendRoot}/**/*.test.ts'
python -X utf8 ${CLAUDE_PLUGIN_ROOT}/skills/debugger/scripts/find_polluter.py "<scratch>/lockfile" "${paths.frontendRoot}/**/*.test.tsx"
# <scratch> is any writable directory — `python -X utf8 -c "import tempfile;print(tempfile.gettempdir())"`.
# Double quotes, not single: cmd.exe does not treat `'` as a quote character.
```
The script runs the tests one at a time, stops at the first that materialises the watched path, and reports the culprit file. **When to reach for it:** an intermittent test run plus a suspicion of cross-test pollution (shared state, missing `afterEach` cleanup, a leftover fixture).

### Defense-in-Depth — fix the system, not just the bug
After fixing, add validation at EVERY layer the data passes through, so the bug becomes **structurally impossible**, not just improbable.

| Layer | Purpose | Example |
|-------|---------|---------|
| **1. Entry point** | Reject invalid input at the API boundary | Zod schema on the tRPC procedure |
| **2. Business logic** | Ensure the data makes sense | Duplicate check before create (`CONFLICT`) |
| **3. Environment guard** | Prevent dangerous operations | Refuse prod DB ops when `NODE_ENV === "test"` |
| **4. Debug instrumentation** | Capture context for forensics | Stack trace + timestamp on the failure path |

```typescript
// Layer 2: Business logic
const existing = await ctx.db.select().from(accounts).where(and(
  eq(accounts.userId, ctx.userId),
  eq(accounts.fullName, input.name),
));
if (existing.length > 0) throw new TRPCError({ code: "CONFLICT", message: "Name already exists" });

// Layer 3: Environment guard
if (process.env.NODE_ENV === "test") {
  const dbUrl = process.env.DATABASE_URL ?? "";
  if (!dbUrl.includes("localhost") && !dbUrl.includes("_test"))
    throw new Error("Refusing operation on non-test database");
}
```
**Validate each layer catches what the others miss:** bypass Layer 1 with direct input → Layer 2 must catch; mock Layer 2 → Layer 3 must refuse in the wrong context; escape Layer 3 → Layer 4 must log enough for forensics. Single-point validation **guarantees** the bug returns via another path (future refactor, new mock, edge case from another code path).

### Writing the regression test — condition-based waiting
Replace arbitrary timeouts with condition polling (flaky async tests are themselves a bug).
```typescript
// ❌ Guessing at timing
await new Promise((r) => setTimeout(r, 50));
// ✅ Waiting for the condition
await waitFor(() => getResult() !== undefined);
```
```typescript
async function waitFor<T>(condition: () => T | undefined | null | false, description: string, timeoutMs = 5000): Promise<T> {
  const start = Date.now();
  while (true) {
    const result = condition();
    if (result) return result;
    if (Date.now() - start > timeoutMs) throw new Error(`Timeout waiting for ${description}`);
    await new Promise((r) => setTimeout(r, 10));
  }
}
```
| Scenario | Pattern |
|----------|---------|
| Wait for event | `waitFor(() => events.find(e => e.type === 'DONE'))` |
| Wait for state | `waitFor(() => machine.state === 'ready')` |
| Wait for count | `waitFor(() => items.length >= 5)` |
| Wait for DOM | `waitFor(() => document.querySelector('.loaded'))` |

**When an arbitrary timeout IS correct:** wait for the triggering condition first, *then* the timed behavior — and document the math (`setTimeout(r, 200) // 2 ticks at 100ms`).

**Testing pyramid** — put the regression test at the cheapest layer that exercises the real seam: Unit (Vitest, ~70%, pure logic) → Integration (Vitest + tRPC, ~20%, routes/DB/auth) → E2E (`agent-browser` CLI, ~10%, critical journeys). Naming: `describe('[Component]')` › `it('[should] [behavior] [when condition]')`. Run via the project's declared test command (`${tooling.commands.test}`), never the runtime's bare test subcommand — Bun's native runner, for one, does not implement vitest's `vi.mocked`/`vi.hoisted`.

### 3-fix escalation rule
- **< 3 fixes failed** → return to Step 1 (rebuild the reproducer if the loop drifted).
- **≥ 3 fixes failed** → **STOP.** It's wrong architecture, not a wrong hypothesis. Escalate to `graph-powers:evaluator` Mode 3 before any further attempt.

---

## Step 6 — Verify & cleanup (P6)

> Invoke `Skill("superpowers:verification-before-completion")` before any "fixed" claim. No completion claim before the gate command output (stdout + exit code) is read.

### Fix Verification Criteria — a fix is verified when ALL are true
1. **Reproducible:** bug reproduces on demand via the Step 1 feedback loop (failing test / `curl` / `agent-browser`) — manual steps do NOT count.
2. **Test-proven on the real seam:** regression test fails without the fix, passes with it, and exercises the **real production code path** (not a happy-path stub, not a private helper with synthetic args).
3. **Isolated:** the fix changes only what's necessary.
4. **Gate-passing:** `${tooling.commands.typeCheck}`, `${tooling.commands.lint}`, `${tooling.commands.test}` all pass (release: `${tooling.commands.build}`).
5. **Non-regressive:** no previously passing test now fails.
6. **Instrumentation removed:** `grep -rn "DEBUG_BUG_<ID>" ${paths.backendRoot} ${paths.frontendRoot}` returns 0 — every Step 4 tagged log deleted before commit.
7. **Hypothesis confirmed:** commit body names which of the ≥3 Step 3 hypotheses survived, and (briefly) why the rejected ones were disproved.

### Regression prevention — scale to bug severity
| Bug level | Required |
|-----------|----------|
| L1–L4 | Fix + test (standard flow) |
| L5 | Fix + test + regression-risk note |
| L6+ | Fix + test + postmortem + prevention |

| Risk | Definition | Action |
|------|-----------|--------|
| **High** | Same bug class likely elsewhere | Scan codebase, fix ALL instances |
| **Medium** | Could recur if related code changes | Add guard, document |
| **Low** | Isolated incident | Standard fix |

### Cleanup checklist (mandatory exit gate — none optional)
- [ ] Original Step 1 reproducer **no longer fires** (re-run 3×, all green)
- [ ] Regression test passes in CI and exercises the **real production seam**
- [ ] `grep -rn "DEBUG_BUG_<ID>" ${paths.backendRoot} ${paths.frontendRoot}` returns **0**
- [ ] No `console.log` or `graph-powers:debugger` left in the touched production paths. Get the changed files from `git diff --name-only HEAD~1 HEAD`, then search them with the **Grep tool** — `$(...)` and a `grep` binary are POSIX-only, and this check silently passes when either is missing
- [ ] No `as any`, no stub credentials, no test scaffolding left over

### Post-mortem (mandatory L6+, recommended for all)
Write to `debug-reports/YYYY-MM-DD-<slug>.md`:
```markdown
# <Bug title>
**Severity:** P1/P2/P3/P4 · **Time to resolve:** Xh

## Timeline
1. Reported: [when, how]  2. Root cause identified: [when, technique]  3. Fixed: [when]  4. Verified: [when, how]

## Root cause
<5-Whys terminal answer — the original trigger, not the symptom>

## Hypotheses
**Confirmed:** <which of the ≥3 Step 3 hypotheses survived>
**Disproved:** <one line each, with the probe that disproved it>

## Why it escaped
- [ ] Missing test coverage  - [ ] Insufficient defense-in-depth  - [ ] Edge case not considered  - [ ] Env difference (dev vs prod)

## Prevention measures
1. <test added>  2. <guard added>  3. <pattern fix — if High risk, list other instances fixed>

## Architectural follow-up
<what system-level change would prevent this bug CLASS? open a tracking issue if non-trivial>
```
The architectural follow-up is the most valuable line — symptomatic fixes prevent the same bug; architectural fixes prevent the bug class.

---

## Templates

### 5 Whys
```markdown
**Problem**: [error]
1. Why? → [first cause]   2. Why? → [deeper]   3. Why? → [underlying]   4. Why? → [systemic]   5. Why? → [root]
**Root Cause**: [final]   **Fix**: [solution]
```

### Commit message
```
fix(scope): brief description

Root cause: [5 Whys result]
Confirmed hypothesis: [which of the ≥3 Step 3 hypotheses survived]
Fix: [what changed]

Tested: ${tooling.commands.typeCheck} ✅, ${tooling.commands.test} ✅
```

---

## Security checklist (audit / `systematic-audit` support — OWASP 2025 + the project's privacy regime)

| Check | Pattern |
|-------|---------|
| Auth verified on every route | `if (!ctx.user) throw new TRPCError({ code: "UNAUTHORIZED" })` |
| Ownership verified | resource `tenantId` matches `ctx.tenant.id` before read/write |
| Parameterized queries | `db.select().from(users).where(eq(users.id, userId))` — NEVER string-concat SQL |
| No exposed secrets | `grep -rn "sk_live\|password\|api_key" ${paths.backendRoot} ${paths.frontendRoot}` → 0 |
| Input validated | all inputs through Zod; file uploads type + size checked |
| PII / privacy | HTTPS enforced; no sensitive data in logs; failed auth attempts logged |
| Dependency audit | the package manager's audit command (`${tooling.packageManager} audit`) |
