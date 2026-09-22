# Issue 27 — verification and installation

Baseline: main `d30ccc21f3296c0ecb77d57e94761238bd526585`, clean, version 1.21.1.
Implementation is now in remote main at `24812f0be2066a9b581129c26a9d362bd80f05fe`.
Installed version: `1.22.0+codex.20260922193943`.

## Authorization and scope

User authorized implementation, AGENT_SETUP and existing plugin refresh, synthetic Codex smokes,
one real Jev evaluation, then global credential storage/local opt-in and issue comments/closure.
No commit/push was performed in the closure turn. Parent model selection remains manual.

**Expanded objective: NEEDS_WORK.** The latest request requires Jev to coordinate agents, skills,
commands and round-trip handoffs through verified completion. Current code implements optional
routing only: it skips roles sharing a model, accepts no skill/command candidates and does not
connect the Jev result to the existing dispatch/return loop. The successful API smoke does not
prove that broader cycle. Issue 27 remains OPEN; revise the plan before claiming completion.
Audit: https://github.com/GrupoUS/graph-powers/issues/27#issuecomment-5783792693.

## Implemented scope and proof

- Ten Astra/high and two Luna/medium defaults; override precedence and evaluator read-only/leaf
  intent preserved. Native/clone parity passes for all twelve roles.
- Opt-in Jev evaluation is separate from chat; one fresh reservation permits one HTTP attempt.
  Fingerprint, cap three, typed probabilities, terminal errors and replay use the existing ledger.
- Regression RED/GREEN covers missing evaluation, duplicate/concurrent requests, legacy Fable
  fallback, conflicting verdict/choice, symlink/nested Git roots and CLI exit codes 0/2/4/1.
- Latest local policy/native checks and 77 SDD tests pass. Original full inventory: 30 commands;
  initial context and Kilo failures were corrected and affected gates repeated successfully.
  Context ceiling: 207918/208000. Kilo used existing Node 26.7.0 via process-only PATH; no trust
  setting changed. Build/typecheck/lint are NOT DECLARED gates.
- Evidence: `.graph-powers/logs/issue-27/gates/`, `recheck/`, `final-gates/` and `smoke/`.
  Independent final review returned READY for the original scope; the expanded audit did not.

## Installation and credential configuration

Native plugin add and explicit-config companion emission exited 0. Nine decisive installed source
files match the checkout, including AGENT_SETUP. All twelve roles match policy; five personal
roles retain their hashes. Generic subagent defaults were preserved. Native client verification
passed with 16 hook registrations and a denied synthetic commit-guard probe.
Installation evidence: `.graph-powers/logs/issue-27/installation.json`.
Backup is outside the source/autoload trees; its pointer is `install-backup-location.txt` there.

The global config hash changed during native refresh; no manual edit or stale backup restore was
performed then, so whole-file byte preservation was not claimed. Current parent is Luna 6/max.
The later authorized credential edit changed only the global native shell environment entry
`AI_GATEWAY_API_KEY`, kept mode 0600 and preserved other parsed settings. Local configuration stores
only the evaluation opt-in. A fresh Codex executor confirmed variable presence without its value.
No secret was copied into tracked files or the GitHub comment.

## Real integration and remaining platform proof

Three Codex smokes passed: Astra/high and Luna/medium|max. Jev returned HTTP 200 and a typed choice
in exactly one request. Empty-env replay with network forbidden returned the same record, zero
fetches. Details and generation ID are in smoke.md and `gateway-activation/live-result.json`.
Native-economic/Ultra activation and Hermes runtime remain NOT RUN/UNVERIFIED; Hermes static
package checks pass, with provenance refreshed after the implementation commit.

CI Windows hook runtime fails with cp1252 UnicodeEncodeError printing U+2192: current run
35779558466/job 106921280393 and baseline 35240317796/job 105266774345 have the same failure;
relevant files are unchanged by this issue. Other jobs, including Codex, passed. Do not claim
all CI green. Fix the Windows encoding separately; no workflow rerun was performed here.

## Rollback

Revert only issue-owned hunks; preserve concurrent user work, including the externally changed
AGENTS.md block. Restore only owned installation artifacts from the backup if needed. Never reset
the checkout or overwrite personal roles/settings. No closing action was taken after the expanded
coordination requirement was found unmet.
