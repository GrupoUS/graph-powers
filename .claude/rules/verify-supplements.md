---
# `/verify` reads this file by explicit path, so these globs are not how it arrives there — they
# exist to stop it arriving anywhere else. A rule in this directory with no `paths:` field loads
# unconditionally into every session at `.claude/CLAUDE.md` priority, and a gate inventory is the
# last thing that needs to be resident while somebody edits a skill description. Scoped here to the
# surface where the list is worth having open: the gate scripts themselves and the config that
# declares them.
paths:
  - ".github/**"
  - ".graph-powers/config.json"
---

# Verification supplements — the gates `tooling.commands` cannot hold

Read by `/verify § 0`, after the declared gates and before the verdict.

This repository declares exactly one command in `tooling.commands`: `test`. That is not an
oversight and it is not a gap to fill by inventing values for the other six keys. There is no type
check and no build here — the tree is markdown, JSON and standard-library Python — and the linters
are deliberately not gates (`AGENTS.md § The linter configuration is not a gate`: they exist so a
contributor's editor says the same thing on every machine, and none of them can fail a pull
request).

What this repository does have is thirteen checks that fail CI, none of which fit a key named
`typeCheck`, `lint` or `build`. Before this file existed `/verify` ran one of them and reported a
clean line, which is the exact failure mode `§ 0` warns about: a gate nobody declared reads like a
gate nobody needed.

Run all of them, in this order, from the repository root. Every one exits 0 on success.

| # | Gate | Command | A failure means |
|---|---|---|---|
| 1 | Manifest | `claude plugin validate .` | `plugin.json` or `marketplace.json` is malformed — the plugin will not load at all |
| 2 | Guardrails | `python3 hooks/test_hooks.py` | a hook lost a guarantee. This is the declared `test` gate; it is listed here so the set is readable in one place |
| 3 | Hook syntax | `python3 -c "import ast,glob;[ast.parse(open(f).read()) for f in glob.glob('hooks/*.py')]"` | a hook would raise on import, and a hook that cannot start is a guardrail that is not running |
| 4 | JSON | `python3 -c "import json,glob;[json.load(open(f)) for f in glob.glob('**/*.json',recursive=True)+glob.glob('.*/*.json')]"` | a config file is unparseable. Claude Code ignores such a file wholesale rather than erroring |
| 5 | Workflows | `bun .github/check_workflows.mjs` | a workflow does not parse, or its `meta.name` disagrees with its filename, so the name will not resolve at runtime |
| 6 | Wiring | `python3 .github/check_wiring.py` | an agent, skill, workflow or cited section does not resolve. These fail silently: the model reads the instruction, finds nothing, and continues with less than it thinks it has |
| 7 | Portability | `python3 .github/check_portability.py` | something POSIX-only entered a command an agent executes, breaking Windows installs quietly |
| 8 | Command cost | `python3 .github/check_context_budget.py` | a command's floor grew — every future invocation pays it before reading its arguments |
| 9 | Listing budget | `python3 .github/check_listing_budget.py` | the plugin's share of the skill listing grew past its ceiling, which drops somebody else's skill description on a shared machine |
| 10 | Machine paths | `python3 .github/check_machine_paths.py` | a home directory reached a tracked file — cardinal 2 |
| 11 | Placeholders | `python3 .github/check_placeholders.py` | a `${...}` placeholder names a field the schema does not declare, so it resolves to nothing |
| 12 | Version | `python3 .github/check_version_bump.py` | a shipped file changed without a version bump. Installed machines compare versions, not commits, so the change reaches nobody |
| 13 | CLI | `bun bin/graph-powers.mjs --help` | the installer entry point is broken |

Two more that need arguments and therefore run in CI rather than here:
`python3 .github/check_codex.py <root> <project> <scope>` and `python3 .github/check_clone.py`.
`/verify` reports them as **CI-only**, never as passed.

## What is deliberately not a gate

- `ruff`, `basedpyright`, `oxlint`, `biome`. `biome ci` reports formatting drift in the five `.mjs`
  files and always has; the same tree produced 190 ruff findings while CI was green. Reformatting
  them is a standalone change with its own commit, never a rider on somebody else's work.
- The tracked-file count `python3 .github/check_clone.py` prints is a number to read, not a
  threshold to pass. A clone is the artefact here; nothing is packed, so the count only matters
  when it moves for a reason nobody can name. (It used to be spelled `git ls-files | wc -l`, which
  is two coreutils cardinal 8 bans — the script reports the same number and runs on Windows.)
