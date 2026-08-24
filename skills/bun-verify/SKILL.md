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

## When to Use

- Type-check, unit/integration tests, lint or format on a JS/TS tree.
- The user names Bun, `bun test`, tsgo, or "don't use Node tsc".
- A gate would otherwise default to npm/npx/Node.

**Not for:** Python/Rust/Go repos, browser flows, choosing a product feature.

## Defaults (only if the project did not declare the command)

| Gate | Command |
|---|---|
| Type-check | `tsgo --noEmit -p <tsconfig>` |
| Test | `bun test --parallel` |
| Incremental test | `bun test --parallel --changed` |
| Lint | leave `NOT DECLARED` unless `tooling.commands.lint` exists |
| Scripts in parallel | `bun run --parallel <a> <b>` |

`tsgo` is the TypeScript 7 native compiler (`@typescript/native-preview`). It is
not the `tsc` that ships with `typescript@5` under Node.

## Procedure

1. Read `.graph-powers/config.json` `tooling.commands`. Done when each present key is the command you will run.
2. For a missing JS/TS key, apply the table above. Report `INFERRED (bun-verify)`, never pretend it was declared.
3. Run through the harness shell tool. Capture exit code. A missing `tsgo` binary is `NEEDS-WORK`, not a silent `tsc` fallback.
4. Prefer `bun test --parallel` over a serial runner. Add `--changed` only when the user asked for a cheap loop, not for the final verdict.
5. Dispatch `graph-powers:verification` for UI flows. This skill does not open a browser.

## Pitfalls

- `npx tsc` / `node_modules/typescript/bin/tsc` is the slow Node compiler. Do not "helpfully" fall back to it.
- `bunx tsc` may still resolve TypeScript 5 from the project. Call `tsgo` by that name.
- `--parallel` implies isolate. Do not add `--no-isolate` to chase speed if tests share globals.
- Bun 1.4 `lockfileVersion` 2/3 is unread by older Bun. Do not rewrite the lockfile as a side effect of a gate.
- Declared `tooling.commands.test: null` means no tests on purpose. Do not invent `bun test`.

## Verification

A correct use names the exact command, the exit code, and whether it was declared or inferred.
`VERIFIED` still requires every declared gate, including non-JS ones.
