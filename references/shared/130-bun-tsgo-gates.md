# JS/TS gate resolution (Bun 1.4 + tsgo)

Used by `/verify` § 0, `ultra-verify`, and `010-quality-gates.md`. Load `Skill("bun-verify")`.

## Resolve the command

1. Resolve literal `tooling.commands.<gate>`; expand `bun run <script>` from `package.json`.
2. Reject Node tests, legacy `tsc`, bare `tsgo`, or Bun concurrency above two: `NEEDS-WORK`, no execution or fallback.
3. Infer only missing JS/TS keys from `bun-verify`; label `INFERRED (bun-verify)`.
4. Otherwise: `NOT DECLARED`.

A safe declared Vitest/`bun run test` stays declared; bare `bun test` would skip its config.

## Scope before spawn

If the command contains `turbo run` and has no `--filter`:

- Unique `apps/<name>` / `packages/<name>` in the change set → append `--filter=<name>` for each.
- No such path → run as declared.

Label scoped rows `SCOPED`.

## Mode

Empty `/verify` arguments mean `quick` (process gates + floor). Agent tracks (explorer, evaluator, security, design) run only for `full` or `loop`.

Bash/terminal is the launcher. Do not replace it to chase performance.

Tests: `bun test --changed --bail=1 --smol` in loops; `bun test --smol` once finally.
Type-check: `bunx --bun --no-install --package @typescript/native-preview tsgo --noEmit -p <tsconfig> --checkers 1`.
Missing tools fail. Parallelism is opt-in and capped at two. Internal plugin ESM scripts are not tests.
