---
description: "Prove work holds before handoff: declared gates, safety floor, and an evidence-backed verdict. Modes: quick, full, loop. Use before claiming L3+ complete; not for review (/pr-review) or fixing failures (/debug)."
workflow_type: augmented-llm
---

# /verify

**ARGUMENTS:** $ARGUMENTS.

Modes: explicit `/verify quick` is gates + floor, `/verify full` runs the review agents, and `/verify loop` hands the plan-measured half to `graph-powers:ultra-verify`, § 1.6.
No arguments inherit the originating task's tier: **L1-L2 → `quick`; L3+ → `full`**.
Explicit `/verify quick` always remains `quick`.
An unknown tier is classified from the change set by `020-complexity-routing.md`; a risk surface or second domain raises it, and a tier still unclear defaults to `full`.
An argument-less L3+ run reuses a valid independent review of the same snapshot and scope (for example Phase C's final Evaluator) and dispatches only uncovered reviewer roles; explicit `/verify full` always runs the batch.

## 0. Resolve evidence

Read `.graph-powers/config.json` via `${CLAUDE_PLUGIN_ROOT}/references/shared/000-config-loader.md` and `${CLAUDE_PLUGIN_ROOT}/references/shared/125-change-set.md` for changed surfaces; report an empty change set and stop.
Only for JS/TS changes, read `${CLAUDE_PLUGIN_ROOT}/references/shared/130-typescript7-oxc-gates.md`.

An undeclared gate is `NOT DECLARED`, never PASS; PASS requires exit zero this session. Run matching `tooling.commands`, `${rulesDir}/verify-supplements.md` if present, conditional `chain.contractGates`, and `database.commands.status` only for schema. Report skips; database DRIFT/UNREACHABLE is NEEDS-WORK, never apply schema changes.

### 0.2 Structural evidence

For unanswered structural questions, apply `125-change-set.md § C` using supported provider capabilities; unavailable, unsupported, stale or `none` falls back to text. Current source needs no graph query.

## 1. Run gates and review

Run applicable declared commands in order, record exit/evidence, stop at first failure unless `--all`. Reuse PASS only while files, configuration and relevant environment match; rerun affected gates otherwise.

### 1.5 Full review batch

For explicit `full`, dispatch evaluator always, security-reviewer for auth/API/schema, web or user input, and ui-ux-designer for web. For argument-less L3+, first match independent review verdicts to the current snapshot, scope, relevant inputs and role; dispatch only uncovered roles (including security and ui-ux when their surfaces apply). Stale or incomplete proof never covers a role. Fold `chain.lenses` into those roles and report a missing role. Skip only for `quick`, classified L1-L2 or a `loop` owned by `ultra-verify`; reviewers are read-only and report findings and clean scope.

### 1.6 `loop`

For `loop` with a plan path, invoke `Workflow({ name: 'graph-powers:ultra-verify', args: { planPath, config } })`. If unavailable, unresolved or declined, report once and read `${CLAUDE_PLUGIN_ROOT}/references/verify-loop-fallback.md`. This command still owns floor, supplements, declaration status, rollback and reuse evidence.

## 2. Safety and scope

Check the safety floor: no unapproved irreversible/data action, secret in tracked diff or out-of-scope change; declared tooling only. Full uses Acceptance evidence; quick/loop gathers it locally. In non-quick modes read the plan and matching `REVIEW.md`/rules for acceptance, watchlist, reuse ledger and rollback. Pre-existing/out-of-scope observations are notes, not reopened work.

## 3. Verdict

At verdict read `${CLAUDE_PLUGIN_ROOT}/references/shared/090-verdict-matrix.md`. Return `VERIFIED` (gates/floor/checklist clean), `VERIFIED-WITH-NOTES` (non-blocking notes) or `NEEDS-WORK` (failure, violation or unverified item). Include base/confidence, commands/exit/evidence, skipped/undeclared rows and remaining decision. Include graph provider/scope/freshness and unsupported capabilities; missing graph proof is not a clean risk score.
