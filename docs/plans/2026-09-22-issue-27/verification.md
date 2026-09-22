# Issue 27 — verification and installation record

Baseline: main at d30ccc21f3296c0ecb77d57e94761238bd526585, clean, version 1.21.1.
Candidate: 1.22.0+codex.20260922193943. No commit, push, PR, issue publication or Kilo configuration change.

## Authorization

User approved the conversation plan, implementation, AGENT_SETUP update and existing installed
plugin refresh. A separate explicit reply authorized synthetic Codex Astra/high, Luna/medium|max,
and at most one paid Jev call. No credential changes or global parent model changes are authorized.

## Implementation evidence

- Model defaults RED: expected evaluator Astra/high, received old Sol/max; GREEN policy checker 12 defaults.
- Evaluation configuration RED: resolver missing; GREEN separate opt-in evaluation and chat rejection.
- Ledger RED: Jev backend unsupported; GREEN typed envelope/reservation/replay.
- Legacy fallback regression RED: Fable UNKNOWN -> evaluator record fingerprint mismatch; GREEN fixed without changing legacy semantics.
- Typed-result regression RED: conflicting verdict/choice incorrectly returned 0; GREEN now rejects it; SDD 77 tests.
- Adapter RED: module missing; GREEN real ledger plus mocked HTTP, exact wire fields, provider metadata normalization, timeout, errors, caps and replay.
- Scope regression RED: symlink plan accepted mixed roots; GREEN realpath and Git root binding for host/plan.
- CLI: 0 success/skip; 2 invalid input/config; 4 blocked/pending/cap; 1 unexpected failure.
- Native: 12 companions; native/clone parity and permission-limit contracts pass.
- Hermes: 39 registrations, static proof only; runtime remains UNVERIFIED.

## Gate evidence

Ordered inventory: `.graph-powers/logs/issue-27/gates/results.json` (30 commands for 29 entries).
Initial context budget failure fixed by shortening the changed assignment contract; ceiling
207918/208000, without raising a cap. Kilo's initial failure was an untrusted mise shim under
fixture HOME; running the existing Node 26.7.0 executable via process-only PATH passed, without
changing trust or configuration. Rechecks are under `.graph-powers/logs/issue-27/recheck/`.
Post-review affected gates are under `.graph-powers/logs/issue-27/final-gates/`.
`check_codex.py` fixture invocation is CI-only; type-check/build/lint are NOT DECLARED gates.

## Runtime evidence

See smoke.md: three real Codex turns passed with matching runtime model/effort headers and no
fallback notices. Jev real integration is NOT RUN: AI_GATEWAY_API_KEY is absent, zero paid
requests sent. Local mocks prove single sending and replay behavior, not account integration.
Native-economic/Ultra activation was not requested or performed; their runtime is NOT RUN.

## Installation

Backup prepared outside the source tree and auto-loaded directories (location recorded in
`.graph-powers/logs/issue-27/install-backup-location.txt`): previous plugin cache, twelve
managed roles, hashes of global config and personal roles. All twelve installed model/effort
pairs match the previous generated policy; no personal scalar overrides will be replaced.
Final independent acceptance: READY; all three original review findings independently confirmed
addressed. Native refresh completed with exit 0:

- `codex plugin add graph-powers@graph-powers --json` installed the candidate version.
- `bun <installed-cache>/codex/native-plugin.mjs --plugin <installed-cache> --config .graph-powers/config.json --out <active-codex-home>/agents` emitted the twelve managed roles.
- Nine decisive installed source files match the checkout byte-for-byte, including AGENT_SETUP.
- Ten installed roles resolve Astra/high and two resolve Luna/medium; no unresolved plugin token.
- All five non-plugin personal role files retain their original hashes; generic subagent defaults
  and concurrency match the captured pre-update values.
- The global config hash changed across the update interval. It was not edited manually; the
  native CLI performed registration. The old `.bak` does not match the captured baseline and was
  deliberately not restored. Whole-file byte preservation is NOT VERIFIED. Current effective
  parent is gpt-6-luna/max. No sandbox/auth policy was intentionally changed.
- Native client verification with `--probe-guardrail` passed: version matches, 16 registrations,
  Python available, commit guard denied its synthetic probe.

Detailed installed identity and hashes: `.graph-powers/logs/issue-27/installation.json`.
A new Codex conversation is needed to load the refreshed plugin/role definitions.

## Acceptance

| Requirement | Evidence/status |
|---|---|
| Ten Astra/high, two Luna/medium roles | Policy/native checks PASS |
| Latest family IDs and efforts | Official docs and real Codex smokes PASS |
| Parent/settings and Kilo | Parent currently Luna 6/max; five personal roles and generic defaults preserved; global config byte equality NOT VERIFIED; Kilo canonical unchanged |
| Evaluator read-only/leaf | Native permission contract PASS; per-role enforcement remains advisory |
| Jev never a chat role | Policy/projection negatives PASS |
| One attempt per decision and three-decision cap | Real-ledger mock/CLI regressions PASS |
| Typed choice agrees with verdict | SDD negative regression PASS |
| Same Git root for config and ledger | Symlink/nested repository negatives PASS |
| Parent call site and setup guide | Existing flow updated; wiring and references PASS |
| Real Jev integration | NOT RUN — credential absent |
| Installed package/roles refreshed | PASS — native refresh, 9 source byte matches, 12 role resolutions, client guardrail probe |

## Rollback

Revert only this issue's source/projection hunks, preserve any subsequent user work. Installation
backup retains the previous package and roles; restore only those owned artifacts if rollback is
needed. Do not reset the checkout or delete third-party roles/settings. Historical dispatch records
were retained when the setup-derived package ownership expanded; no additional spawn budget was granted.
