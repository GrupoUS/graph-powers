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

What this repository does have is twenty-eight verification checks, none of which fit a key named
`typeCheck`, `lint` or `build`. Before this file existed `/verify` ran one of them and reported a
clean line, which is the exact failure mode `§ 0` warns about: a gate nobody declared reads like a
gate nobody needed.

Run all of them, in this order, from the repository root. Every one exits 0 on success.

For Hermes gates 8–9, first generate the candidate from the current source revision with
`bun hermes/install.mjs --package-only`, then run `bun hermes/install.mjs --check`.
These are static checks; no candidate import, scanner, Doctor or installation belongs to them.
Runtime validation is not implemented and remains `UNVERIFIED`: the reserved
`--hermes-proof runtime` route requires explicit installed `--package-root` and `--expected-version`
and returns nonzero pending separately approved native identity, exact-byte scan and sandbox proof.

| # | Gate | Command | A failure means |
|---|---|---|---|
| 1 | Manifest | `claude plugin validate .` | `plugin.json` or `marketplace.json` is malformed — the plugin will not load at all |
| 2 | Guardrails | `python3 hooks/test_hooks.py` | a hook lost a guarantee. This is the declared `test` gate; it is listed here so the set is readable in one place |
| 3 | Client package safety | `python3 .github/test_hook_clients.py` | an incomplete/stale client package could receive bypass, unrestricted or always-approve posture; or an interrupted Codex clone would be skipped |
| 4 | Structured plans | `python3 skills/planning/scripts/test_sdd.py` | plan parsing, TDD or review packaging regressed |
| 5 | Skill eval runner | `python3 skills/skill-improve/scripts/test_run_evals.py` | the eval path or CLI contract regressed |
| 6 | Skill trigger-eval capture | `python3 skills/skill-improve/scripts/test_capture_trigger_evals.py` | clean-session trigger-eval capture drifted |
| 7 | Oxc and Zed policy | `python3 .github/check_oxc_policy.py` | TypeScript 7, Oxc or editor policy drifted |
| 8 | Hermes static regressions | `python3 -X utf8 .github/test_hermes_package.py` and `python3 -X utf8 .github/test_hermes.py --static` | package generation, byte integrity or no-import isolation regressed |
| 9 | Hermes static package proof | `python3 -X utf8 bin/verify-hook-clients.py --client hermes --hermes-proof static --plugin-root . --package-root hermes/package --json` | source-derived inventory, closure, provenance or packaged bytes differ |
| 10 | Hook syntax | `python3 -c "import ast,glob;[ast.parse(open(f).read()) for f in glob.glob('hooks/*.py')]"` | a hook would raise on import, and a hook that cannot start is a guardrail that is not running |
| 11 | JSON | `python3 -c "import json,glob;[json.load(open(f)) for f in glob.glob('**/*.json',recursive=True)+glob.glob('.*/*.json')]"` | a config file is unparseable. Claude Code ignores such a file wholesale rather than erroring |
| 12 | Workflows | `bun .github/check_workflows.mjs` | a workflow does not parse, or its `meta.name` disagrees with its filename, so the name will not resolve at runtime |
| 13 | Codex policy | `bun .github/check_codex_policy.mjs` | semantic model routing, override precedence or the Ultra boundary drifted |
| 14 | Codex native companions | `python3 .github/check_codex_native.py` | native companion and clone policy differ, runtime paths leak, or generated files are stale |
| 15 | Wiring | `python3 .github/check_wiring.py` | an agent, skill, workflow or cited section does not resolve. These fail silently: the model reads the instruction, finds nothing, and continues with less than it thinks it has |
| 16 | File-reference negatives | `python3 .github/test_file_references.py` | the live-file reference gate no longer rejects a known bad fixture |
| 17 | File references | `python3 .github/check_file_references.py` | a live Markdown path resolves to nothing |
| 18 | Portability | `python3 .github/check_portability.py` | something POSIX-only entered a command an agent executes, breaking Windows installs quietly |
| 19 | Command cost | `python3 .github/check_context_budget.py` | a command's floor grew — every future invocation pays it before reading its arguments |
| 20 | Listing budget | `python3 .github/check_listing_budget.py` | the plugin's share of the skill listing grew past its ceiling, which drops somebody else's skill description on a shared machine |
| 21 | Machine paths | `python3 .github/check_machine_paths.py` | a home directory reached a tracked file — cardinal 2 |
| 22 | Placeholders | `python3 .github/check_placeholders.py` | a `${...}` placeholder names a field the schema does not declare, so it resolves to nothing |
| 23 | CLI | `bun bin/graph-powers.mjs --help` | the installer entry point is broken |
| 24 | Clone artefacts | `python3 .github/check_clone.py` | required files are missing, Git inventory is unavailable, source exceeds 4 MiB, the self-contained Hermes package exceeds 2 MiB, or candidate files contain generated Python bytecode |
| 25 | Version | `python3 .github/check_version_bump.py` | a shipped file changed without a version bump. Installed machines compare versions, not commits, so the change reaches nobody |
| 26 | Grok projection and configuration | `python3 .github/check_grok.py` | Grok metadata or configuration preservation/idempotence differs from its supported contract |
| 27 | Cursor projection and context | `python3 .github/check_cursor.py` | Cursor metadata, generated hooks, native context output or configuration preservation regressed |
| 28 | Issue plan comment | `python3 skills/issue-improve/scripts/test_issue_comment.py` | preview, scoped author/marker selection, pagination or safe retry/publication regressed |

One additional installation assertion needs fixture arguments and therefore runs in CI rather than
here: `python3 .github/check_codex.py <root> <project> <scope>`. `/verify` reports it as
**CI-only**, never as passed.

## What is deliberately not a gate

- `ruff`, `basedpyright` and `oxlint`. The repository is not a Python or JavaScript lint gate; these
  tools exist so a contributor's editor says the same thing on every machine. Reformatting the five
  `.mjs` files is a standalone change with its own commit, never a rider on somebody else's work.
- The file count `python3 .github/check_clone.py` prints is informational. Its byte budgets are
  gates: 4 MiB for everything outside `hermes/package/` and 2 MiB for that independently verified,
  self-contained package. The total ceiling is therefore 6 MiB, an explicit revision of the old
  4 MiB whole-clone budget after the Hermes distribution was added. This is not a size reduction.
  The check reports both groups and their actual aggregate; tracked files and non-ignored untracked
  candidates count, while a published clone contains only tracked files. Hermes gates 8–9 continue
  to reject extra payload or missing dependencies, so its separate budget cannot hide source files.
