---
name: bun-verify
description: "JS/TS gates: Bun 1.4 tests and tsgo, never Node tsc."

---

# Bun 1.4 + tsgo gates

Resolve and run JavaScript/TypeScript verification on this harness. Project
`.graph-powers/config.json` `tooling.commands` supplies the command, but never overrides the
resource safety floor below. When a JS/TS gate is undeclared, use Bun 1.4 and native `tsgo` —
not legacy `tsc`, `node --test`, or a `tsgo` shebang that starts Node.

Loaded by `/verify`; `ultra-verify` reads the shared resolver directly. Browser E2E stays on
`webapp-testing` + the `graph-powers:verification` agent.

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
| Type-check | `bunx --bun --no-install --package @typescript/native-preview tsgo --noEmit -p <tsconfig> --checkers 1` |
| Test | `bun test --smol` |
| Incremental test | `bun test --changed --bail=1 --smol` |
| Lint | leave `NOT DECLARED` unless `tooling.commands.lint` exists |

Do **not** infer `bun test` when `tooling.testRunner` is `null`, `python`, or a Vitest/`bun run test` command. A project that declared Vitest (`bun run test`) must keep that string — bare `bun test` skips its config.

Bare `tsgo` follows a Node shebang; the exact command above forces Bun, forbids gate-time installs
and caps checker workers. Missing local tooling is `NEEDS-WORK`. Setup, TypeScript 7 naming and
framework limits: `references/low-resource-js-ts-gates.md`.

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

1. Empty `/verify` means `quick`; state the mode.
2. Read literal `tooling.commands`; expand `bun run <script>` from `package.json`.
3. Apply the deny list in `references/low-resource-js-ts-gates.md`; forbidden or missing tooling is `NEEDS-WORK`, with no fallback.
4. Infer only missing JS/TS keys from the table; label them `INFERRED (bun-verify)`.
5. Scope Turbo, run changed-only tests in loops, and run the serial full suite once at the final gate.
6. Browser UI uses `graph-powers:verification`, never `quick`.

## Pitfalls

Never rewrite the lockfile during a gate. `tooling.commands.test: null` means no tests on purpose.
Replacing the shell does not reduce gate cost; compiler/test workers and agent batches do.

## Verification

A correct use names the mode (`quick`/`full`), the exact command (including `--filter`), the exit code, and whether it was declared, inferred or scoped.
`VERIFIED` still requires every declared gate, including non-JS ones.
