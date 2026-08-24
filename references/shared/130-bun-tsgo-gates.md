# JS/TS gate resolution (Bun 1.4 + tsgo)

Used by `/verify` § 0 and by the Hermes `graph-engineering` Step 5.
Load `Skill("bun-verify")` before applying this file.

## Resolve the command

1. If `.graph-powers/config.json` names `tooling.commands.<gate>`, that string is the command.
2. Else if the change set is JS/TS and `bun-verify` applies, infer from that skill's table and label the row `INFERRED (bun-verify)`.
3. Else the row is `NOT DECLARED`.

Never infer `npx tsc`, `npm test`, `node --test`, or bare `bun test` on top of a declared Vitest/`bun run test` command.

## Scope before spawn

If the command contains `turbo run` and has no `--filter`:

- Unique `apps/<name>` / `packages/<name>` in the change set → append `--filter=<name>` for each.
- No such path → run as declared.

Label scoped rows `SCOPED`.

## Mode

Empty `/verify` arguments mean `quick` (process gates + floor). Agent tracks (explorer, evaluator, security, design) run only for `full` or `loop`.

Bash/terminal is the launcher. Do not replace it to chase performance.

Bun 1.4 is the inferred test runtime (`--parallel`, `--changed`, `--shard`). Type-check is native `tsgo` (TypeScript 7), not `tsc` from `typescript@5`.
