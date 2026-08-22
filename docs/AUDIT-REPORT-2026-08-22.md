# Audit — graph-powers — 2026-08-22

**Scope:** diff against `origin/main` (`6c83c4ed`) … `HEAD` (`2f4fabb7`) — PR #9
**Gates at audit time:** `python3 hooks/test_hooks.py` PASS · `check_cursor.py` PASS · `check_grok.py` PASS · `check_wiring.py` PASS · dangling-refs FAIL (`hooks/db_apply_gate.py` in PLAN.md) · `check_version_bump.py` vs PR base PASS (1.8.3 → 1.9.0)
**Repository shape:** markdown / JSON / stdlib Python / dependency-free ESM · hook suite is the test surface · 2 commits on the PR

`/debug audit pr` Codex `adversarial-review --scope branch` does not exist on Codex CLI v0.149 (`codex review --base origin/main` was started; it had not returned a verdict before this file was written). Dimensions D3 / D8 / D9 / D7 on changed files only, via a read-only explorer. Security exploit tracing is in the parent `/pr-review` 3B track, not duplicated here.

## Findings

| # | Sev | Dimension | Location | Defect | Failure scenario |
|---|-----|-----------|----------|--------|------------------|
| 1 | P0 | D7 | `docs/plans/2026-08-22-generic-database-verification/PLAN.md:431` | Out-of-scope table cites `hooks/db_apply_gate.py`, which does not exist. CI dangling-refs excludes only `CHANGELOG.md`. | `gates` job exits 1; the PR cannot merge. |
| 2 | P1 | D7 | `hooks/test_hooks.py` (no `harness="cursor"` branch) | Fourth harness ships with generated `hooks/hooks-cursor.json` and zero Cursor payload tests. | Cursor-specific deny-shape and matcher defects stay green under `python3 hooks/test_hooks.py`. |
| 3 | P1 | D3 | `hooks/_config.py:155-165` | `_TOOL_ALIASES` maps Grok names only. Cursor `StrReplace` / `EditNotebook` / `Task` / `Shell` are unmapped; `graph_guardrails.py:223,282` then misses spawn cap and write lease. | Two writers on one file via `StrReplace`; spawn ceiling never counts Cursor `Task`. |
| 4 | P2 | D3 | `cursor/install.mjs:57-61` ≡ `grok/install.mjs:36-40` | `pluginRootFromArgv`, `buildPluginManifest`, and `main()` duplicated while both already import `codex/lib.mjs`. | A manifest field added on one harness stays green on both `check_cursor` / `check_grok` while the shapes diverge. |
| 5 | P2 | D3 | `grok/install.mjs:166-171` | `ensureMarketplaceSource` matches `name = "graph-powers"` against the whole `config.toml`. | An unrelated occurrence skips registering the marketplace source; plugin never loads. |
| 6 | P2 | D7 | `.github/check_version_bump.py:39-48,92` | Local `HEAD~1` vs CI `origin/main` disagree; mode-only change of `hooks/tool_approver.py` fails locally after the bump commit. | Contributors learn to ignore a gate that is red on their machine and green on the PR. |
| 7 | P2 | D7 | `hooks/_config.py:253-273` | `emit_pretool_deny` adds top-level `"decision": "deny"` on every harness; only Grok is asserted (`hooks/test_hooks.py:181-183`). | If Claude or Cursor rejects the extra key, every PreToolUse deny becomes silence. |
| 8 | P3 | D7 | `.github/check_grok.py:97,108` | `/tmp/gp-clone` string in a `.py` file; portability scanner has no `/tmp` rule for Python. | Gate that cardinal 8 rests on cannot see the class of path it was written to forbid. |
| 9 | P3 | D9 | `docs/plans/` | Tracked plan directory is not in the AGENTS.md “where things live” table; dangling-refs treats it as a description of the present. | Next plan repeats finding 1. |

## What was dropped

Explorer returned 11 findings, under the cap of 15. Nothing truncated. Findings about Cursor deny *vocabulary* (`permission` vs `permissionDecision`) were left to `/pr-review` 3B rather than duplicated here.

## Not audited

- D1/D2 architecture (evaluator 3A)
- D4/D5 documentation completeness beyond the dangling path
- D6 UX (no web surface)
- D8 dependencies: **clean** — `package.json` has no `dependencies` block; installers import `node:*` and `codex/lib.mjs` only
- Exploitability of installer permission writes (3B)
- Codex `review` stdout (still running at report time)

## Recommended order

1. De-path `hooks/db_apply_gate.py` in PLAN.md (or exclude `docs/plans/**` from dangling-refs) so `gates` can go green.
2. Make Cursor PreToolUse deny actually deny (`permission`, and/or exit 2), then add `_TOOL_ALIASES` for Cursor names and one `harness=cursor` negative test — otherwise (1) is a green CI over an inert Cursor floor.
3. Then the duplicated installer helpers and the unscoped Grok marketplace regex, which will otherwise reintroduce harness drift.
