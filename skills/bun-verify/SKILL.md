---
name: bun-verify
description: "JS/TS gates: Bun 1.4 tests and tsgo, never Node tsc."

---

# Bun 1.4 + tsgo gates

Resolve and run JavaScript/TypeScript verification on this harness. Project
`.graph-powers/config.json` `tooling.commands` always wins. When a JS/TS gate is
undeclared, use Bun 1.4 and native `tsgo` — not `npx tsc` and not `node --test`.

Loaded by `/verify` and by `graph-powers:graph-engineering` Step 5. Browser E2E
stays on `webapp-testing` + the `graph-powers:verification` agent.

## Cost model

| Mode | What runs | When |
|---|---|---|
| `/verify quick` (default) | Declared/inferred process gates + safety floor | Everyday, L1–L3 |
| `/verify` / `/verify full` | Gates + explorer/evaluator/security/design agents | PR, L4+, user asked for full |
| `/verify loop` | ultra-verify workflow | There is a plan file |

The agent batch is the expensive part (RAM and tokens). Process gates are cheap if scoped.

## When to Use

- Type-check, unit/integration tests, lint or format on a JS/TS tree.
- The user names Bun, `bun test`, tsgo, or "don't use Node tsc".
- A gate would otherwise default to npm/npx/Node.
- A declared command is `turbo run …` and the change set is under `apps/` or `packages/`.

**Not for:** Python/Rust/Go repos (this plugin's own `python3 hooks/test_hooks.py` stays), browser flows, choosing a product feature.

## Defaults (only if the project did not declare the command)

| Gate | Command |
|---|---|
| Type-check | `tsgo --noEmit -p <tsconfig>` |
| Test | `bun test --parallel` |
| Incremental test | `bun test --parallel --changed` |
| Lint | leave `NOT DECLARED` unless `tooling.commands.lint` exists |
| Scripts in parallel | `bun run --parallel <a> <b>` |

Do **not** infer `bun test` when `tooling.testRunner` is `null`, `python`, or a Vitest/`bun run test` command. A project that declared Vitest (`bun run test`) must keep that string — bare `bun test` skips its config.

`tsgo` is the TypeScript 7 native compiler (`@typescript/native-preview`). It is
not the `tsc` that ships with `typescript@5` under Node.

## Scope Turbo before running

If the resolved command contains `turbo run` and does not already contain `--filter`:

1. From the change set, collect unique directory names immediately under `apps/` or `packages/`.
2. One name → append `--filter=<name>`. Several → one `--filter` per name.
3. None (only repo root) → run the command as declared.
4. Report the final argv. Label `SCOPED` when filters were added.

This is how a monorepo avoids type-checking the untouched app.

## Inspect the Turbo graph without aborting

**[HARD]** Never pass `--dry=json` or `--dry-run` to turbo or `bun run test` in Bash. That
pipe panics turbo (EPIPE) and abort()s Node/bun; the hook denies it. Run
`scripts/turbo_dry_json.py`, then Read `TURBO_DRY_JSON`. Detail:
`references/turbo-dry-json-epipe.md`. Declared test gates are unchanged.

## Procedure

1. If `/verify` has no arguments, treat it as `quick`. Done when the mode is stated in the report.
2. Read `.graph-powers/config.json` `tooling.commands`. Done when each present key is the command you will run.
3. For a missing JS/TS key, apply the table above. Report `INFERRED (bun-verify)`, never pretend it was declared.
4. Apply Turbo scoping. Run through the harness shell tool. Capture exit code. A missing `tsgo` binary is `NEEDS-WORK`, not a silent `tsc` fallback.
5. Prefer `bun test --parallel` over a serial runner only when inferred. Add `--changed` only when the user asked for a cheap loop, not for the final verdict.
6. Dispatch `graph-powers:verification` for UI flows, never as part of `quick`. This skill does not open a browser.

## Pitfalls

- `npx tsc` / `node_modules/typescript/bin/tsc` is the slow Node compiler. Do not "helpfully" fall back to it.
- `bunx tsc` may still resolve TypeScript 5 from the project. Call `tsgo` by that name.
- `--parallel` implies isolate. Do not add `--no-isolate` to chase speed if tests share globals.
- Bun 1.4 `lockfileVersion` 2/3 is unread by older Bun. Do not rewrite the lockfile as a side effect of a gate.
- Declared `tooling.commands.test: null` means no tests on purpose. Do not invent `bun test`.
- Replacing Bash with another shell does not speed gates up. The cost is the compiler, the test runner, or the agent batch.

## Verification

A correct use names the mode (`quick`/`full`), the exact command (including `--filter`), the exit code, and whether it was declared, inferred or scoped.
`VERIFIED` still requires every declared gate, including non-JS ones.
