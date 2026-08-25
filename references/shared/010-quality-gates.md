## Section 1: Quality Gates

| Timing | Gates |
|---|---|
| After each task | only the task's focused `CHECK`; never a whole-project suite |
| After each phase | resolved type-check + lint, once |
| Final | resolved type-check + lint + serial full tests, once |

Run literal `tooling.commands`; never reconstruct them. When the change set is JS/TS, apply
`130-bun-tsgo-gates.md`: forbidden declared executors are `NEEDS-WORK`. In fix loops use its
changed-only test; run the full suite once at the boundary.

> **Pre-commit:** run formatter+linter on every manually edited file. Most linters (`biome`, `eslint`) treat errors as build-breaking — they fail CI immediately.
