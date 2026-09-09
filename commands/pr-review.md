---
description: "Review a PR, branch or diff before merge. Read-only unless --fix; never approves or merges. Modes: <PR#>, --current, --branch <name>, full. Flags: --quick, --fix."
workflow_type: routing
---

# /pr-review

**ARGUMENTS:** $ARGUMENTS. Target: PR number, `--current` (default), or `--branch <name>`. Accept `full`, `--quick`, `--fix`; reject conflicting/unknown flags. Implementation uses `/implement`; gate proof uses `/verify`.

## 0. Pre-flight

Read `.graph-powers/config.json`, matching `${rulesDir}` and root `REVIEW.md` when present. Only for `full`, load `${CLAUDE_PLUGIN_ROOT}/references/safety-floor.md` and full review references. `--branch` has no PR metadata/comments.

When resolving target/base and surfaces, read `${CLAUDE_PLUGIN_ROOT}/references/shared/125-change-set.md §§ A–B`.

When structural risk remains unanswered, read `${CLAUDE_PLUGIN_ROOT}/references/shared/125-change-set.md § C` for retrieval/fallback; decisive source needs no graph probe.

## 1. Bounded review

Dispatch read-only reviewers together: evaluator for correctness/plan/diff (except `--quick`), security-reviewer for auth/API/data/payment/secrets, ui-ux-designer for web. Fold compatible `chain.lenses` into these roles; report unresolved lenses. `--quick` skips evaluator/design, retains applicable security, and can only return COMMENT.

Every finding needs opened `file:line`, severity, evidence and a bounded recommendation. Deduplicate and distinguish introduced regressions from pre-existing/out-of-scope observations.

Only when changed rules, paths, commands, consumers or invariants could contradict instructions, load `Skill("graph-powers:intent-layer")` for its diff audit. Findings stay advisory even with `--fix`; do not edit consumer rules.

## 2. Output

Return target/base, scope, blocking/non-blocking tables, sensitive surfaces, skipped tracks, verdict and ready review comment. Structural rows carry provider/scope/freshness and capability gaps; unsupported risk/orphan operations use source/text, never a second backend. APPROVE requires evaluator evidence; disclose unreviewed sensitive surfaces.

## 3. `--fix`

First evaluate every item using § 4.1; any `clarify` item stops the fix wave. Under explicit `--fix`, package accepted in-scope P0/P1 findings by disjoint existing writer ownership: general/security → `graph-powers:debugger`; web UI → `graph-powers:frontend-specialist`; measured performance → `graph-powers:performance-optimizer`; mobile → `graph-powers:mobile-developer`. Never send a reviewer to fix or invent a role. Run focused regression evidence per package, then one final applicable gate; reuse it only while its files, configuration and environment remain valid. After `graphGuardrails.maxRepatch` failed attempts on the same file, route to `/debug recover`. Re-review the whole corrected diff once with a fresh evaluator; P0/P1 remains REQUEST CHANGES. Leave changes unstaged and never commit.

## 4. Modes

§§ 0–2 define mode coverage; only `--fix` enters § 3, for accepted findings.

### 4.1 Feedback evaluation

Implement evidenced in-scope defects; clarify missing evidence; push back on incorrect, pre-existing or out-of-scope feedback with file:line. Record decisions before edits.
