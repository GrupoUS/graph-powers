---
name: debugger
description: "Use when an error, crash, failing test, 500, hydration mismatch or regression needs evidence-first diagnosis, or when a debug/TDD loop must resolve Oxc and bounded test gates. Loaded by /debug. Not for choosing what to build or proving an already-working change."
---

> Hermes: first load `skill_view("graph-powers:graph-engineering")` for native calls and host-policy limits. `content/` paths are `file_path` values relative to the common registered-document parent. Source tools/model frontmatter is not host enforcement.

# Debugger

## Iron Law (diagnose-first)

No hypothesis without a deterministic agent-runnable reproducer; no fix without confirmed root
cause; no behavior fix without the real-seam RED required by
`content/skills/planning/references/execution/tdd-policy.md`; no completion without
applicable gate evidence and browser/DB evidence when relevant. Do not expand incident scope or
cite unread lines. Never use `as any` or leave diagnostic logs in a shipped fix.

Never de-atomize transactions to silence an error. Read the connection module's driver import and
reproduce its actual limitation: an HTTP driver can reject transactions while the provider's
pool/WebSocket driver supports them. Fix that boundary before considering independent writes.

## Engine

| Steps | Read when entering | Exit evidence |
|---|---|---|
| 1–3 | `content/skills/debugger/references/diagnose.md` | minimal reproducer, ranked falsifiable hypotheses and disproving probes |
| 2, selected pack | `content/skills/debugger/references/pack-guides.md` | applicable A/B/C/D evidence; caller controls delegation |
| 4–6 | `content/skills/debugger/references/methodology.md` | confirmed cause, regression, fix verification criteria and cleanup |
| 5 | planning TDD policy above; `content/skills/debugger/references/structural-quality.md` | RED→GREEN on the owning boundary, no unrelated special case |
| 6 | `content/references/shared/015-verification-gate.md` | command/exit evidence; only valid unchanged evidence may be reused |

## JS/TS gate resolver

JS/TS changes load
`content/references/shared/130-typescript7-oxc-gates.md`. Use
`content/skills/debugger/scripts/turbo_dry_json.py`, never captured `turbo --dry=json`; rationale is in
`content/skills/debugger/references/turbo-dry-json-epipe.md`. Load anti-patterns for the relevant symptom, not wholesale.

## Step 0 — Classify & route
Choose the pack below; read nearest AGENTS.md, config and matching rules. Resolve declared gates
and baseline only the affected boundary. Browser evidence uses `skill_view("graph-powers:webapp-testing")`.

## Step 1 — Build feedback loop
Save a deterministic, red-capable command and failing input. Prefer a focused test or API/CLI
fixture, then browser/replay evidence; manual instructions alone cannot close this Step.

## Step 2 — Reproduce & minimise
Repeat enough to confirm the symptom; capture variance as a parameter. Remove inputs/callers one
at a time. Use the selected pack's templates only for independently useful parent-dispatched work.

## Step 3 — Hypothesise
Rank falsifiable causes and give each a disproving probe. Report the ranking before instrumentation;
retain evidence and counter-evidence rather than inventing extra guesses for a confirmed direct fix.

## Step 4 — Instrument
Test one prediction/variable at a time; prefer debugger/REPL over tagged temporary logs. Stop when
the root cause and owning boundary are confirmed; unavailable evidence is a blocker, not a guess.

## Step 5 — Fix + regression test
Follow methodology Step 5 and the TDD policy: observe the matching failure, change the owning
boundary minimally, observe GREEN. Run the focused regression first; preserve unrelated dirty work.

## Step 6 — Verify & cleanup
Apply methodology's Fix Verification Criteria and the shared evidence gate. Remove all temporary
`DEBUG_BUG_<ID>` probes, capture relevant browser/DB evidence, and report the root cause, ruled-out
alternatives, touched paths and prevention check. A commit is never required to report a fix.

## Stopping & escalation
Missing reproducible input, credentials or runtime evidence returns `BLOCKED` with an exact next
probe/unblock action. After 1–2 failed fixes return to Step 1; at three failed attempts with coupling
or cascading symptoms, stop and ask the parent for `graph-powers:evaluator` Mode 3 before another
fix. Repeated hypotheses without an architecture signal route to `/debug recover`. Review feedback
first follows `content/commands/pr-review.md § 4.1`.

## Pack selector

| Mode / aliases | Pack / evidence |
|---|---|
| default / `debug` / `auto` | choose from the concrete failing boundary; one scope question only if needed |
| `frontend` / `ui` / `react` | `frontend-debug`: browser before/after |
| `backend` / `api` | `backend-debug`: service/data evidence |
| `auth-db` / `auth` / `db` / `permissions` | `auth-db-debug`: tenant/auth/DB evidence |
| `audit` / `full` | `systematic-audit`: inventory before fixes; browser/DB when present |
| `recover` | `/debug recover`, no pack |

`content/skills/debugger/references/pack-guides.md` owns all pack deltas and templates A (browser evidence), B (code
archaeology), C (regression history), D (DB state). Resource-only symptoms route to `/perf resources`.

## Common Root Causes Catalog
Load the relevant symptom in `content/skills/debugger/references/anti-patterns.md`: uncontrolled→controlled values,
unguarded insert returns, auth matcher/context gaps, partial cache invalidation, SSE cleanup,
missing tenant predicates, or driver mismatch. Confirm it against the reproducer before editing.

## Scripts
Use `content/skills/debugger/scripts/fetch_logs.py` only for supplied CI/VPS/DB log sources; `content/skills/debugger/scripts/find_polluter.py` for
test-state bisection; `content/skills/debugger/scripts/turbo_dry_json.py` for file-backed Turbo graph capture.

## References
The Engine table owns method loading. `content/skills/debugger/learning.md` is historical evidence, read only for a matching
failure; mode-specific orchestration remains in `content/commands/debug.md`.

## Configuration
Resolve tooling from `.graph-powers/config.json`; absent gates are `NOT DECLARED`, never invented.
