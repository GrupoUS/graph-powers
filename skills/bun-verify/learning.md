# learning.md — round history for `bun-verify`

## Round 1 — 2026-08-24 · turbo `--dry=json` EPIPE abort

**Hypothesis:** agents invent `turbo run test --dry=json` to inspect the graph; documenting the
safe form in SKILL.md is not enough because they will not load the skill first.

**Change:** [HARD] rule + `scripts/turbo_dry_json.py` in this skill; deny in
`hooks/smart_bash_approver.py` so the crashing argv cannot run even when bun-verify is not
loaded. Detail in `references/turbo-dry-json-epipe.md`.

**Measurement:** hook suite cases for the six crashing argv (deny under autonomous and guarded)
and the five legitimate test/type-check/wrapper forms (not deny). Script in an empty directory:
non-zero, stdout does not start with `{`.

**Verdict:** kept. The hook is the prevention; the skill is the replacement. A prose-only rule
would have been Round 0 of the same crash.

## Round 2 — 2026-08-25 · Node/tsc and unbounded workers

**Hypothesis:** the old defaults optimized wall-clock time (`bun test --parallel`) but not machine
health; one worker per CPU core and TypeScript's default checker pool can increase peak RAM. Bare
`tsgo` also follows a Node shebang, contradicting a no-Node gate policy.

**Change:** serial `bun test --smol`, changed-only fail-fast loops, tsgo forced through Bun with one
checker, and a hook deny for Node tests, legacy tsc, bare tsgo, and unbounded Bun workers. Project-
wide gates move to phase/final boundaries instead of every task.

**Measurement:** hook cases cover explicit and package-script-hidden forbidden executors, bounded
Bun forms, and the safe tsgo-through-Bun launcher. Official rationale and commands live in
`references/low-resource-js-ts-gates.md`.

**Verdict:** kept. `python3 hooks/test_hooks.py` returned `EVERY GUARANTEE HELD`.
