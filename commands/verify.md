---
description: "Prove work holds before handoff: declared gates, safety floor, and an evidence-backed verdict. Modes: quick, full, loop. Use before claiming L3+ complete; not for review (/pr-review) or fixing failures (/debug)."
workflow_type: augmented-llm
---

# /verify

**ARGUMENTS:** $ARGUMENTS.

Modes: explicit `/verify quick` is gates + floor, `/verify full` runs the review agents, and `/verify loop` hands the plan-measured half to `graph-powers:ultra-verify`, § 1.6.
No arguments inherit the originating task's tier: **L1-L2 → `quick`; L3+ → `full`**.
Explicit `/verify quick` always remains `quick`.
An unknown tier defaults to `full`; only an explicitly classified L1-L2 run may infer `quick`.

## 0. Resolve evidence

Read `.graph-powers/config.json` through `${CLAUDE_PLUGIN_ROOT}/references/shared/000-config-loader.md`.

Read `${CLAUDE_PLUGIN_ROOT}/references/shared/125-change-set.md` to resolve change set/surfaces. Empty change set is reported and stops.

Only when JS/TS changed, read `${CLAUDE_PLUGIN_ROOT}/references/shared/130-typescript7-oxc-gates.md`.

A declared gate that lacks a command is `NOT DECLARED`, never PASS; a command is PASS only when it exits zero this session.

Run matching `tooling.commands`, `${rulesDir}/verify-supplements.md` when present, conditional `chain.contractGates`, and `database.commands.status` only for a schema surface. Report skipped/undeclared separately. Database DRIFT or UNREACHABLE is NEEDS-WORK; `/verify` never applies schema changes.

### 0.2 Structural evidence

For an unanswered structural question, apply the already-loaded `125-change-set.md § C`. Use the selected provider's supported capabilities; `none`, unavailable, unsupported or stale evidence falls back to text. Sufficient current source needs no graph/status query.

## 1. Run gates and review

Run each applicable declared command in its declared order, capture exit code and meaningful evidence, and stop at the first failure unless `--all` is present. Reuse passing evidence only while its files, configuration and relevant environment remain valid; otherwise rerun the affected gate.

### 1.5 Full review batch

In `full`, or an argument-less L3+/unknown-tier run, dispatch in parallel: evaluator always; security-reviewer for auth/API/schema; ui-ux-designer for web. Fold `chain.lenses` into those three roles and report a missing role. Skip this batch only for explicit `quick`, explicitly classified L1-L2, or `loop`; reviewers are read-only and return findings plus a clean-scope statement.

### 1.6 `loop`

With `loop` and a plan path, invoke `Workflow({ name: 'graph-powers:ultra-verify', args: { planPath, config } })`. If unavailable, unresolved, or declined, run §§ 1–3 directly and report that route once; never retry it. The workflow owns the plan completeness, skeptic panel, bounded fix/regate loop. This command still owns floor, supplements, declaration status, rollback and reuse evidence.

## 2. Safety and scope

Check the safety floor: no unapproved irreversible/data action; no secret in tracked diff; declared tooling only; and no out-of-scope change. Full mode uses the Acceptance evidence; quick/loop gathers it locally. Read the plan and matching `REVIEW.md`/rules only in non-quick modes to check acceptance criteria, watchlist, reuse ledger and rollback. Pre-existing or out-of-scope observations are notes, never reopened work.

## 3. Verdict

At verdict, read `${CLAUDE_PLUGIN_ROOT}/references/shared/090-verdict-matrix.md`.

Return one: `VERIFIED` (all gates/floor/checklist clean), `VERIFIED-WITH-NOTES` (non-blocking notes), or `NEEDS-WORK` (failure, violation, or unverified item). Include base/confidence, executed commands, exit/evidence, skipped/undeclared rows and remaining decision. Include any graph provider/scope/freshness and unsupported capabilities; missing graph evidence is never a clean risk score.
