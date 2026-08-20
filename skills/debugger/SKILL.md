---
name: debugger
description: "Root-cause discipline for a defect already under investigation: reproduce, isolate, prove the cause, then fix. Wraps superpowers systematic-debugging, test-driven-development and verification-before-completion, adding this harness's anti-pattern catalogue and evidence gates. Loaded by /debug. Not for choosing what to build."

---

# Debugger (the project)

Production-grade debugging — root-cause rigor, parallel sub-agent research, agent-browser evidence, DB validation. **Diagnose first: find the bug before fixing it.** The superpowers debug skills are the engine of each Step (§ Engine); the project layers packs, the anti-pattern catalog, and stack-specific evidence gates around them. Inside this plugin the skill is namespaced as `graph-powers:debugger`, so a same-named personal skill cannot shadow it; `/debug` and `Skill("debugger")` both resolve here. The **agent** `subagent_type: "graph-powers:debugger"` is a separate namespace and a different artefact.

## Iron Law (diagnose-first)

1. **No hypothesis without a reproducer.** Step 3 can't start until Step 1 produced a deterministic, agent-runnable feedback loop. *No loop → no hypothesis.*
2. **No fix without confirmed root cause.** Understand *why* before changing code — otherwise fixes rerun blind.
3. **No production code without a RED test on the real seam** (`Skill("superpowers:test-driven-development")`). Fixes without RED are hopes, not fixes.
4. **No "fixed" without fresh evidence** — gate suite exit-0 **plus** screenshot or DB check.
5. **No scope expansion mid-incident** — log follow-ups; fix only what reproduces.

**Guardrails (NEVER):** cite a `file:line` without `Read` (lines drift) · click/fill before `agent-browser snapshot -i -c` (`@eN` refs stale) · `as any` to patch a type (hides the contract bug) · ship `console.log`/`graph-powers:debugger` (Step 6 grep must be 0).

> **Never de-atomize a transaction you have not proven is unsupported.** Serverless Postgres vendors
> ship two drivers: an HTTP one that rejects `db.transaction()` and a pool/WebSocket one that
> supports it. A "never use transactions here" rule written for the first outlives the migration to
> the second, and an agent obeying the stale rule rewrites working atomic writes into independent
> statements — producing exactly the half-applied state the rule existed to prevent. **Read the
> driver import in the connection module first**, and never swap `db.transaction()` for a batch of
> independent writes to silence an error you have not reproduced.

## Engine

The superpowers debug chain is the motor of each Step; this skill wraps it. **Every artefact in this
harness cites the pairing from here — do not restate it elsewhere.**

| Engine skill | Invoked at | the project wrap |
|---|---|---|
| `superpowers:dispatching-parallel-agents` | Step 2 (before fan-out) | distinct scope + shared return contract for the pack's sub-agents |
| `superpowers:systematic-debugging` | Step 5 (opens the fix) | Iron Law #2, packs, anti-pattern catalog |
| `superpowers:test-driven-development` | Step 5 (RED→GREEN gate) | Iron Law #3 real-seam RED before any prod edit |
| `superpowers:verification-before-completion` | Step 6 (before any "fixed" claim) | gate suite exit-0 + agent-browser/DB evidence |
| `superpowers:receiving-code-review` | Escalation / `/debug recover` | technical evaluation of reviewer feedback, not blind agreement |

---

## Step 0 — Classify & route
- Pick the pack via **Pack selector** (default / frontend / backend / auth-db / audit).
- Resolve tooling from `.graph-powers/config.json` (`tooling.packageManager/typeChecker/linter/testRunner`); the project scripts are the source of truth.
- Pre-load `references/anti-patterns.md` (Negative Constraints index + bug catalog) as first-line triage.
- Baseline gates: `${tooling.commands.typeCheck} && ${tooling.commands.lint} && ${tooling.commands.test}`. Frontend/audit packs: `bunx agent-browser --version`, then `Skill("webapp-testing")` for session, mode and verdict rules.
- **Exit:** pack chosen + baseline result known (so later breakage is attributable).

## Step 1 — Build feedback loop (P1) → `references/diagnose.md`
- Pick the highest-rank rung that fits: vitest → curl HTTP fixture → Python CLI fixture → `agent-browser` → replay harness → fuzz/differential → log parse → metrics → manual (last resort).
- Make it **red-capable · deterministic · fast (<30s) · agent-runnable**; save to `.graph-powers/logs/<id>-repro.*`.
- **GATE:** if you're reading code to build a theory before this command exists — stop. **No loop → no hypothesis.**

## Step 2 — Reproduce & minimise (P2) → `references/diagnose.md` + `references/pack-guides.md`
- Run the loop 3× → identical failure OR variance captured as a parameter; confirm it matches the user's symptom (not a nearby failure).
- **Minimise:** strip inputs/callers/config one at a time until every element is load-bearing.
- Dispatch Step-2 parallel research (`Skill("superpowers:dispatching-parallel-agents")` first): Code Archaeologist + Regression Hunter (all packs); + Evidence Collector (frontend/audit) or DB State Inspector (backend/auth). Templates: `references/pack-guides.md § Parallel-research templates`.

## Step 3 — Hypothesise (P3) → `references/diagnose.md`
- Write **≥3 ranked, falsifiable** hypotheses in *"if X is the cause, then Y eliminates the bug"* form; each names a disproving probe. A hypothesis you can't disprove is a guess.
- Checkpoint the ranking with the user; choose the `DEBUG_BUG_<ID>` tag prefix for Step 4 instrumentation.
- **GATE:** merge with Step 2 research (2+ independent sources → HIGH confidence). Record hypothesis + evidence + counter-evidence + fix target `file:line`.

## Step 4 — Instrument (P4) → `references/methodology.md`
- Probe each prediction; **one variable per probe**; debugger/REPL over logs. Tag every log `console.error("DEBUG_BUG_<ID>", …)`. Perf bugs → measure/bisect, never log.
- Library behavior in doubt → Context7 live docs (ORM `.returning()`/batch semantics, the auth SDK's middleware matcher, the query client's invalidation/`staleTime`).
- **Exit:** root cause confirmed; rejected hypotheses disproved by evidence (not just the winner proven).

## Step 5 — Fix + regression test (P5) → `references/methodology.md`
- Invoke `Skill("superpowers:systematic-debugging")` → it mandates `Skill("superpowers:test-driven-development")`: RED on the **real production seam** → watch fail → **single** fix GREEN → watch pass → gates. `Read` before edit; re-run type-check after each edit, revert on new failures.
- Add defense-in-depth at the right layer; re-run the Step 1 loop to confirm it's now green.
- **Fix-shape check** (`references/structural-quality.md`): a fix that adds an ad-hoc conditional / one-off boolean to an unrelated flow is a symptom patch — prefer the fix at the model/boundary that **deletes** the special case.

## Step 6 — Verify & cleanup (P6) → `references/methodology.md`
- Invoke `Skill("superpowers:verification-before-completion")`: full gate suite exits 0 (read stdout + exit code before any "fixed" claim). Capture evidence — frontend: agent-browser snapshot/console/errors/network; backend/auth: psql or validated queries.
- Fix Verification Criteria #1–7; `grep -rn "DEBUG_BUG_<ID>" ${paths.backendRoot} ${paths.frontendRoot}` → **0**; commit body names the confirmed hypothesis + root cause; postmortem to `debug-reports/` for L6+.

---

## Stopping & escalation

| Trigger | Action |
|---|---|
| Self-talk: "just try this quick" / "it's obvious, no repro" / "two fixes at once" / "worked on my guess" / "no test, saw it run" / "patch it there" / "skip the repro" | **STOP — return to Step 1.** Each is a disguised guess / skipped gate. |
| User: "stop guessing" / "is that not happening?" / "ultrathink this" / "we're stuck" / "will it show us…?" / "did you reproduce it?" | Return to Step 1 — missing evidence or instrumentation. |
| 1–2 failed fix attempts | Return to Step 1 with a new hypothesis (rebuild the reproducer if the loop drifted). |
| ≥3 failed attempts (each reveals new shared state/coupling · fixes demand massive refactor · each fix spawns a new symptom elsewhere) | **STOP — wrong architecture, not wrong hypothesis.** Escalate to `graph-powers:evaluator` Mode 3 before any further attempt; hunt the code-judo restructure that deletes the bug class (`references/structural-quality.md`). |
| Review feedback (codex P0/P1, evaluator REVISION_REQUIRED, user points at a reviewer note) | `Skill("superpowers:receiving-code-review")` **before** acting — evaluate each item technically, never blind agreement. |
| Wrong skill: perf/SEO/bundle/Lighthouse · feature design with no bug · pure dep upgrade with no failure signal | Redirect → `performance-optimization` · `Skill("planning")` (`/plan`) · repo upgrade docs. |

## Pack selector

| Pack | `/debug` mode | Scope | Browser ev. | DB val. | Sub-agents |
|------|---|-------|:---:|:---:|:---:|
| `frontend-debug` | `frontend`/`ui`/`react` | React/UI regressions, hydration, interaction | **YES** | — | 3 parallel |
| `backend-debug` | `backend`/`api` | Hono/tRPC/service failures | — | **YES** | 2 parallel |
| `auth-db-debug` | `auth-db`/`auth`/`db`/`permissions` | auth provider role, tenant, sync drift | — | **YES** | 2 parallel |
| `systematic-audit` | `audit`/`full` | Full cross-layer stability sweep | **YES** | **YES** | 4 parallel |
| *(none)* | `recover` | evaluator-led recovery (no pack) | — | — | — |

**Selection:** explicit pack name → use it; visual/UI/React → `frontend-debug`; 500/procedure/mutation → `backend-debug`; auth/role/tenant → `auth-db-debug`; "audit" or unclear → `systematic-audit`; ambiguous → **one** multiple-choice clarifying question. Per-pack flows: `references/pack-guides.md`.

## Common Root Causes Catalog

Quick lookup; full Negative Constraints index + bug catalog → `references/anti-patterns.md`.

| Symptom | Root cause | Fix |
|---------|------------|-----|
| `Select is changing from uncontrolled to controlled` | `value={undefined}` → string | `value={val ?? ""}` |
| `No transactions support in <driver>` | The connection module was switched to the vendor's HTTP-only driver | Restore the pool/WebSocket driver import; do NOT de-atomize the call sites |
| `Cannot read properties of undefined` after insert | Unguarded `.returning()` | destructure then `if (!row) throw …` |
| Auth session null in the API context / UNAUTHORIZED | Middleware matcher / context chain | extend the matcher · check the tenant-resolution step |
| Cache stale after mutation | Partial invalidation | invalidate list + detail queries |
| SSE leak | Listener inside loop | single listener + `finally` cleanup |
| Cross-tenant data leak | Missing tenant filter | add `eq(table.tenantId, ctx.tenant.id)` |

## Scripts (Python — repo policy: new automation → Python stdlib)

| Script | Role |
|--------|------|
| [`scripts/fetch_logs.py`](scripts/fetch_logs.py) | Aggregate CI, VPS and database hints for errors (`GITHUB_REPO`, `PROJECT_VPS_HOST`, `DB_STATUS_COMMAND`) |
| [`scripts/find_polluter.py`](scripts/find_polluter.py) | Bisection — which test pollutes a shared path (`.git`, lockfile, tmp dir) |

> Frontend browser smoke is `bunx agent-browser` via `Skill("webapp-testing")`, not a bundled script.

## References

| File | When to read |
|------|----------------|
| `references/diagnose.md` | **Steps 1–3 gate:** feedback-loop ladder, reproduce & minimise exit criteria, ≥3 falsifiable hypotheses, biases, Superpowers hand-off, the project reproducer recipes |
| `references/methodology.md` | **Steps 4–6:** instrument, root-cause trace, bisect, defense-in-depth, Fix Verification Criteria, postmortem, security/audit checklist |
| `references/pack-guides.md` | Per-pack execution (8a–8d) + Step-2 parallel-research templates |
| `references/anti-patterns.md` | First-line triage: project NEVER rules + ORM / API-layer / auth pitfalls index |
| `references/structural-quality.md` | Step 5 fix-shape check · `systematic-audit` structural sweep · `/pr-review` structural lens (§ 3C): code-judo doctrine, smells table, canonical homes, output discipline, presumptive blockers |
| `Skill("webapp-testing")` | browser evidence: install floor, named session, headless vs `--cdp` attach, verdict rules |

## Configuration

Resolve commands from `.graph-powers/config.json` (`tooling.*`) so the skill ports across repos; the project scripts (`type-check`, `lint:oxlint:check`, `test`, `build`) are canonical. Mode-specific flows (`audit`, `frontend`, `recover`, …) live in `${CLAUDE_PLUGIN_ROOT}/commands/debug.md`. To reuse this skill elsewhere: copy the folder, keep the `name`/`description` triggers, repoint `config.json` tooling labels.
