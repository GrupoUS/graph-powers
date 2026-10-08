---
description: "Review a PR, branch or diff and its comments, then fix accepted findings. Never commits, approves or merges. Modes: <PR#>, --current, --branch <name>, full. Flags: --quick, --no-fix."
workflow_type: routing
---

# /pr-review

**ARGUMENTS:** $ARGUMENTS. Target: PR number, `--current` (default), or `--branch <name>`. Accept `full`, `--quick`, `--no-fix` (`--fix`: default); reject conflicting/unknown flags.

## 0. Pre-flight

Read `.graph-powers/config.json`, matching `${rulesDir}` and root `REVIEW.md` when present. Only for `full`, load `${CLAUDE_PLUGIN_ROOT}/references/safety-floor.md` and full review references. `--branch` has no PR metadata/comments.

For a PR, read body, checks, comments and threads (`gh pr view <n> --comments`, `gh api repos/{owner}/{repo}/pulls/<n>/comments`); unresolved ones are § 4.1 items.

When resolving target/base and surfaces, read `${CLAUDE_PLUGIN_ROOT}/references/shared/125-change-set.md §§ A–B`.

When structural risk remains unanswered, read `${CLAUDE_PLUGIN_ROOT}/references/shared/125-change-set.md § C`; decisive source needs no graph probe.

## 1. Bounded review

Dispatch read-only reviewers together: evaluator for correctness/plan/diff (except `--quick`), security-reviewer for auth/API/data/payment/secrets, ui-ux-designer for web. Fold compatible `chain.lenses` into these roles; report unresolved lenses. `--quick` skips evaluator/design, keeps applicable security and returns at most COMMENT.

Read changed files whole with callers/tests (edge/error paths, contract drift, missing tests). Each finding needs opened `file:line`, severity, evidence and fix step; deduplicate and separate introduced regressions from pre-existing/out-of-scope.

Only when changed rules, paths, commands, consumers or invariants could contradict instructions, load `Skill("graph-powers:intent-layer")` for its diff audit. Advisory only; never edit consumer rules.

## 2. Output

Return target/base, scope, blocking/non-blocking tables, comment decisions, sensitive surfaces, skipped tracks, verdict, ready review comment and replies (posting needs approval). Structural rows carry provider/scope/freshness and capability gaps; unsupported risk/orphan operations use source/text, never a second backend. APPROVE requires evaluator evidence; disclose unreviewed sensitive surfaces.

## 3. Fix

Runs unless `--no-fix`/`--quick` or the target head is not checked out (never switch). Decide each item by § 4.1; `clarify` ones stay unfixed. Route accepted in-scope items and follow-ups by disjoint ownership: general/security → `graph-powers:debugger`; web → `graph-powers:frontend-specialist`; performance → `graph-powers:performance-optimizer`; mobile → `graph-powers:mobile-developer`. Mechanical fixes stay local. Run focused regression evidence per package, then one final gate. After `graphGuardrails.maxRepatch` failures on a file, use `/debug recover`. Re-review the fixed diff once with a fresh evaluator; P0/P1 remains REQUEST CHANGES. Report fixes, evidence and open follow-ups. Leave changes unstaged; never commit.

## 4. Modes

### 4.1 Feedback evaluation

Implement evidenced in-scope defects; clarify missing evidence; push back on incorrect, pre-existing or out-of-scope feedback with file:line. Record decisions before edits.
