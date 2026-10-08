---
description: "Review a PR, branch or diff and its comments, then fix accepted findings. Never commits, approves or merges. Modes: <PR#>, --current, --branch <name>, full. Flags: --quick, --no-fix."
workflow_type: routing
---

# /pr-review

**ARGUMENTS:** $ARGUMENTS. Target: PR number, `--current` (default), or `--branch <name>`. Accept `full`, `--quick`, `--no-fix` (`--fix`: default); reject conflicting/unknown flags.

## 0. Pre-flight

Read `.graph-powers/config.json`, matching `${rulesDir}` and root `REVIEW.md`. Only `full` loads `${CLAUDE_PLUGIN_ROOT}/references/safety-floor.md` and full review references. `--branch` has no PR comments.

For a PR, read body, checks and unresolved threads (`gh pr view <n> --comments`, `gh api repos/{owner}/{repo}/pulls/<n>/comments`) as § 4.1 items.

When resolving target/base and surfaces, read `${CLAUDE_PLUGIN_ROOT}/references/shared/125-change-set.md §§ A–B`; § C only when structural risk stays unanswered.

## 1. Bounded review

Dispatch read-only reviewers together: evaluator for correctness/diff (not `--quick`), security-reviewer for auth/API/data/payment/secrets, ui-ux-designer for web; fold compatible `chain.lenses` into them. `--quick` keeps only security, at most COMMENT.

Read changed files whole with callers/tests. Each finding has opened `file:line`, severity, evidence and fix step; deduplicate.

When changed rules, paths, commands or invariants could contradict instructions, load `Skill("graph-powers:intent-layer")` for its diff audit; advisory, never edit consumer rules.

## 2. Output

Fix mode reports after § 3: fixes with evidence, then skips with their § 4.1 reason. Findings alone only for `--no-fix`/`--quick`/head not checked out. Include target/base, comment decisions, sensitive surfaces, verdict and ready replies (posting needs approval). APPROVE requires evaluator evidence.

## 3. Fix

Runs unless `--no-fix`/`--quick` or the head is not checked out (never switch). Fix every accepted item in this run without asking; never stop at a list. Route by disjoint ownership: general/security → `graph-powers:debugger`; web → `graph-powers:frontend-specialist`; performance → `graph-powers:performance-optimizer`; mobile → `graph-powers:mobile-developer`; mechanical fixes stay local. Focused tests per package, then one final gate; after `graphGuardrails.maxRepatch` failures on a file, `/debug recover`. Re-review once with a fresh evaluator; P0/P1 stays REQUEST CHANGES. Leave changes unstaged; never commit.

## 4. Modes

### 4.1 Feedback evaluation

Verify each comment in code and its nearest test; gather missing evidence yourself. Fix what holds: defects, suggestions, nits, and defects in touched files. If the reason is wrong but the concern real (duplication, magic number, intent, a11y), fix the concern minimally. A failing guard found on the way is fixed too. Skip only what would regress, break a project rule/safety floor, or needs an unmade product/auth/payment/schema decision; record file:line and the check. Bot test pings need no change.
