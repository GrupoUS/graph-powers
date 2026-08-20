## Section 9: Verdict Matrix template

Loaded by `/verify` § 4 to consolidate every signal — declared gates, the § 1.5 review tracks, the
project's supplements and contract gates — into one verdict.

One row per signal, and **a signal that did not run is its own row**, never an absent one: `SKIPPED`
with its reason and `NOT DECLARED` are different answers from `PASS`, and collapsing them is how a
matrix reads as coverage.

```markdown
## Verdict — {feature/task}

| Signal | Source | Status | Notes |
|---|---|---|---|
| Type-check | `${tooling.typeChecker}` | PASS / FAIL | {output tail or error count} |
| Lint | `${tooling.linter}` | PASS / FAIL | {error count} |
| Tests | `${tooling.testRunner}` | PASS / FAIL | {N passed / N failed} |
| Static analysis | `/debug` | PASS / FAIL / N issues | {summary} |
| Performance | `/perf` | PASS / FAIL | {Lighthouse / CWV} |
| E2E | `/debug frontend` | PASS / FAIL | {snapshots captured / regressions} |
| Spec compliance | manual or eval | PASS / FAIL | {requirements satisfied?} |
| Codex review | `codex:codex-rescue` | PASS / FAIL / N findings | {by severity} |
| Codex adversarial | `codex:codex-rescue` adversarial-review | PASS / FAIL / N findings | {by severity} |
| Architecture review | `graph-powers:evaluator` Mode 3 | PASS / WARNINGS | {warnings if any} |

## Decision
- **`VERIFIED`** — every declared signal ran and passed, no unresolved P0/P1.
- **`VERIFIED-WITH-NOTES`** — everything that ran passed; only P2/P3 remain, each one listed.
- **`NEEDS-WORK`** — a signal failed, **or could not be run**. "I could not check this" and "this is
  fine" are different answers.

These three are the harness's vocabulary, and they are deliberately the same words
`graph-powers:ultra-verify` returns, so a chained run and a direct `/verify` can be compared. This
block used to say Ship / Hold / Ship-with-follow-up — a third vocabulary for one concept, in a file
that nothing loaded.

## Open follow-ups
- {list of P2/P3 to schedule}
```
