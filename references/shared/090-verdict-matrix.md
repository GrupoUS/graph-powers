## Section 9: Verdict Matrix template

Used by `/verify` to consolidate signals from gates + agents + reviews into a single ship/no-ship verdict.

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
| Codex review | `codex:rescue` | PASS / FAIL / N findings | {by severity} |
| Codex adversarial | `codex:rescue` adversarial-review | PASS / FAIL / N findings | {by severity} |
| Architecture review | `evaluator` Mode 3 | PASS / WARNINGS | {warnings if any} |

## Decision
- **Ship** if: all PASS + no P0/P1 findings unresolved
- **Hold** if: any FAIL or unresolved P0/P1
- **Ship with follow-up** if: only P2/P3 findings + tracked in tasks

## Open follow-ups
- {list of P2/P3 to schedule}
```
