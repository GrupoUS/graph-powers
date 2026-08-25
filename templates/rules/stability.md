---
paths:
  - "{{PATHS_GLOB}}"
---

# Stability — the invariants that do not bend

> Graph Powers template. Every item below exists because the violation already broke something in
> production somewhere. Delete what demonstrably does not apply here; do not delete what "probably
> will not happen".

## Errors and limits

- **No non-null assertion** (`!`, `as T`, `unwrap()`) over an optional result, an environment
  variable or a query return. Use a type guard, an explicit default, or an early return.
- **Every collection is checked before access.** An empty array is truthy; an out-of-range index
  does not warn.
- **Every side effect has error handling** — network, disk, database, browser API. It either
  degrades with a warning or fails loudly. What it must not do is vanish silently.
- **No cast to `any`.** At the boundary: `unknown` plus schema validation.
- **A server process handles uncaught exceptions and unhandled rejections** without exiting quietly.

## Configuration

- **A required variable fails on first read.** Never fall back to `localhost`, a fake key or an
  empty string — a silent default turns a configuration error into a production incident.
- **Every build variable is in `.env.example`**, with a comment saying what it does.
- **No secret in the code or the repository.** Credential, token, private URL: out.

## Data

- **Every foreign key has an index** on the column that carries it. Without it, cascades and joins
  scan the whole table.
- **User-visible removal is logical**, by flag — never a physical `DELETE` on a row somebody might
  need to audit.
- **A write mirrored in two places happens in one transaction.** Two separate writes create a window
  where the two sides disagree.
- **A webhook handler is idempotent and verifies its signature** before any effect.

## Interface

- **WCAG AA contrast**, `prefers-reduced-motion` honoured, never information carried by colour alone.
- **Semantic tokens, not colour literals.** A `#hex` in a component is a decision nobody can change
  later.
- **Loading, empty and error states exist** on every screen that fetches data.
- **The error page shows generic text and a way back.** A production build does not expose a stack.

## Hygiene

- **No debug logging in shipped code.** A warning only on the degradation path.
- **LF line endings**, enforced by `.gitattributes` or a hook.

## Gates

This project's commands are in `.graph-powers/config.json::tooling.commands`. Running them is what
separates "I think it is right" from "it is right":

```bash
{{TOOLING_COMMANDS}}
```

- **JS/TS gates are Bun + native tsgo, with a resource ceiling.** Never run `node --test`, legacy
  `tsc`, bare `tsgo` (its package shebang starts Node), unbounded `bun test --parallel`, or
  `--concurrent` without `--max-concurrency=2`. Use the exact commands from `Skill("bun-verify")`;
  a forbidden declared command is `NEEDS-WORK`, not an exception.
- **Whole-project gates run once per phase/final boundary.** Per-task proof is the task's focused
  `CHECK`; do not re-run the full type-check and test suite after every file edit.
- **Turbo dry-run is a file, never a pipe.** `turbo --dry=json` and `bun run test --dry=json`
  through an agent's captured stdout panics on EPIPE and abort()s Node/bun. Inspect the graph
  with bun-verify's `turbo_dry_json.py`. Declared `${tooling.commands.test}` is unchanged.

## Signals specific to this project

{{PROJECT_SIGNALS}}
