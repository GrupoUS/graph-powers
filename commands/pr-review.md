---
description: "Review a PR, branch or diff before merge. Read-only unless --fix; never approves or merges. Modes: <PR#>, --current, --branch <name>, full. Flags: --quick, --fix."
workflow_type: routing
---

# /pr-review

**ARGUMENTS:** $ARGUMENTS. Resolve one target: PR number, `--current`, or `--branch <name>`; default is current diff. Accept `full`, `--quick`, and `--fix`; reject conflicting/unknown flags. Never use this for implementation (`/implement`) or gate proof (`/verify`).

## 0. Pre-flight

Read `.graph-powers/config.json`, resolve the diff/base and touched surfaces, and load matching `${rulesDir}` plus root `REVIEW.md` when present. Only when `full` is requested, load `${CLAUDE_PLUGIN_ROOT}/references/safety-floor.md` and the full review references. `--branch` has no PR metadata or comments.

## 1. Bounded review

Dispatch read-only reviewers together: evaluator for correctness/plan/diff (except `--quick`), security-reviewer only for auth, API, data, payment or secrets, and ui-ux-designer only for web. Fold compatible `chain.lenses` into those roles; name an unresolved lens rather than claiming it ran. `full` requires source citation per finding. `--quick` may run security on a sensitive surface but skips evaluator/design and therefore can only return COMMENT.

Every finding needs opened `file:line`, severity, evidence and an actionable recommendation. Consolidate duplicates and distinguish introduced regressions from pre-existing or out-of-scope observations. Do not turn a suggestion into unbounded work.

## 2. Output

Return target/base, scope, blocking and non-blocking tables, sensitive surfaces, skipped tracks, verdict and a ready review comment. Never state APPROVE without evaluator evidence; never hide an unreviewed sensitive surface.

## 3. `--fix`

First evaluate every item using § 4.1; any `clarify` item stops the fix wave. Under explicit `--fix`, package accepted in-scope P0/P1 findings by disjoint existing writer ownership: general/security → `graph-powers:debugger`; web UI → `graph-powers:frontend-specialist`; measured performance → `graph-powers:performance-optimizer`; mobile → `graph-powers:mobile-developer`. Never send a reviewer to fix or invent a role. Run focused regression evidence per package, then one final applicable gate; reuse it only while its files, configuration and environment remain valid. After `graphGuardrails.maxRepatch` failed attempts on the same file, route to `/debug recover`. Re-review the whole corrected diff once with a fresh evaluator; P0/P1 remains REQUEST CHANGES. Leave changes unstaged and never commit.

## 4. Modes

| Phase | default/full | `--quick` | `--branch` | `--fix` |
|---|---|---|---|---|
| scope + risk | yes | yes | yes, no PR metadata | yes |
| evaluator | yes | skip | yes | yes |
| conditional security/design | yes | security only if sensitive | yes | yes |
| fix loop | no | no | no | accepted findings only |

### 4.1 Feedback evaluation

Implement a supported, in-scope defect; clarify missing evidence; push back with file:line evidence when the feedback is incorrect, pre-existing, or out of scope. Record the decision before changing the diff.
