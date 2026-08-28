## Section 1: Quality Gates

| Timing | Gates |
|---|---|
| After each task | only the task's focused `CHECK`; never a whole-project suite |
| After each phase | resolved type-check + lint, once |
| Final | resolved type-check + lint + serial full tests, once |

Run literal `tooling.commands`; never reconstruct them. When the change set is JS/TS, apply
`130-typescript7-oxc-gates.md`: local TypeScript 7 and Oxc are the JavaScript/TypeScript gate,
while Oxc type-aware analysis is an optional final lint gate. In fix loops use the runner's
changed-only form; run the full suite once at the boundary.

> **Hooks:** PostToolUse formats one changed supported file with one local Oxfmt process. Stop lint is
> changed-JS/TS-only and never runs a full-tree fallback or type-aware analysis. TypeScript and test
> gates remain explicit final evidence.
