# Audit — graph-powers — 2026-08-28

**Scope:** exact diff `5a1b9a6579ed4a6a78241a266dd73cecb0daec84` … `3a63ad5dd44258959820c8801dfdc96e41b7cdd4` — PR #14
**Gates at audit time:** `python3 hooks/test_hooks.py` PASS · `check_grok.py` PASS · `check_cursor.py` PASS · `check_wiring.py` PASS · `check_workflows.mjs` PASS · `test_hook_clients.py` PASS · clone/native/portability checks PASS · local JSON/AST/diff checks PASS
**Repository shape:** markdown / JSON / stdlib Python / dependency-free ESM · 20 changed files · 1 commit on the PR

## Follow-up repair in the current worktree

The four CI failures listed below were repaired after this audit snapshot. The changes are still
uncommitted: `.github/workflows/ci.yml` now sends valid heredoc Python and builds complete Cursor
fixtures; `hooks/test_hooks.py` uses byte-exact intent fixtures and an interpreter-backed formatter;
`skills/intent-layer/scripts/intent_layer.py` forces UTF-8 output; `hooks/commit_audit_gate.py`
enforces shell-tree timeouts and recognizes the Windows missing-command status; and
`bin/hook-client-verifier.mjs` resolves `python`/`py -3` on Windows for standalone Grok installs.

This is the changed-file `/debug audit pr` pass. The parent `/pr-review` evaluator and security
tracks cover the broader architecture and exploitability questions; the explorer track supplies
the repository call-chain evidence below.

## Findings

| # | Sev | Dimension | Location | Defect | Failure scenario |
|---|-----|-----------|----------|--------|------------------|
| 1 | P1 | D7 | `grok/install.mjs:247-255` → `bin/hook-client-verifier.mjs:41-46` | The branch makes standalone guarded Grok installs invoke the hook verifier, but the verifier launches a literal `python3`. The repository's Windows interpreter contract uses `python` / `py -3`; no platform-neutral resolution is supplied here. | On a supported Windows setup where only `python` or `py -3` is available, `grok/install.mjs --guarded` exits before writing `config.toml`, so guarded plugin discovery and native subagent enablement are not installed. The guarded path skipped this verifier before this PR. |

## What dropped

One P1 finding was retained. The security track inspected the same installer, hook verifier,
configuration, schema, workflow, and generated-client surfaces and returned no qualifying security
finding. No other evidence-backed regression survived consolidation.

## Not audited

- UI/UX: no web surface is in the diff.
- Project-specific lenses: `.graph-powers/config.json` declares none.
- Full repository quality beyond the changed-file audit.
- Live Grok client discovery: the local proof used a disposable home and simulated the missing
  `python3` interpreter; it did not launch a real Grok session.

## Baseline CI notes

The recorded PR check run was red in `gates`, `cursor`, `clone`, `Hook runtime (windows-latest)`,
and SonarCloud. The first four are now covered by the follow-up repair and all pass the local
equivalent gates. The Sonar quality gate remains a separate baseline issue: its annotations point
to pre-existing complexity/path findings outside the repair scope, so it still needs a fresh remote
analysis before merge readiness can be claimed.

## Recommended order

1. Run the complete PR check set on the repaired worktree, including `windows-latest`.
2. Resolve the separate SonarCloud baseline findings if that check remains required for merge.
