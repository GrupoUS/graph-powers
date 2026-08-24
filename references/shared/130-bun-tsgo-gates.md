# JS/TS gate resolution (Bun 1.4 + tsgo)

Used by `/verify` § 0 and by the Hermes `graph-engineering` Step 5.

1. If `.graph-powers/config.json` names `tooling.commands.<gate>`, run that string.
2. Else if the change set is JS/TS and `Skill("bun-verify")` applies, infer from that skill's table and label the row `INFERRED (bun-verify)`.
3. Else the row is `NOT DECLARED`.

Never infer `npx tsc`, `npm test`, or `node --test`. Those are Node-shaped fallbacks this harness does not want.

Bun 1.4 (Aug 2026) is the runtime for inferred tests: `--parallel`, `--changed`, `--shard`, `--timings`. Type-check is native `tsgo` (TypeScript 7), not `tsc` from `typescript@5`.
