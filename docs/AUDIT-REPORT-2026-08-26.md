# Review — PR #10 · 2026-08-26

## Summary

This release consolidates planning, implementation, review and TDD into one authority; adds the
intent-layer, design, motion and landing-page capabilities; removes duplicate execution surfaces;
and keeps the Codex, Cursor and Grok outputs generated from the canonical plugin artefacts. The
review hardened the new execution and eval helpers, hook permissions, reference scanning, motion
fallbacks and cross-platform path handling before merge.

## Blocking

| Sev | Location | Defect | Failure scenario |
|---|---|---|---|
| — | — | No open P0-P2 finding | All confirmed findings were corrected and re-tested before this report. |

## Non-blocking

| Sev | Location | Defect | Why it is not blocking |
|---|---|---|---|
| P3 | `skills/intent-layer/scripts/intent_layer.py:333` | A same-user process could race the symlink/confinement checks and the final read. | Static final and component symlink escapes are rejected without reading outside content. Exploitation additionally requires a concurrent local writer with the user's permissions; the same residual was independently covered as non-blocking. |

## Findings resolved during review

- Structured SDD plans now preserve field-shaped and nested-checkbox steps, map `T2a` to phase 2,
  require executable gates and observed RED/GREEN evidence, and acquire/release one atomic,
  owner-checked write lease with resumable progress and task-review ledgers.
- Briefs, review packages and plan state reject symlink escapes; Git revision inputs accept only
  `HEAD` or hexadecimal object IDs.
- Eval response directories reject unsafe IDs, symlinks and traversal, isolate missing/unreadable
  cases instead of aborting the suite, and no longer expose an arbitrary JSON output path.
- Intent-layer discovery is linear on long valid-tail lines, preserves route/dynamic groups,
  confines downlinks and nodes to the project root, canonicalises internal aliases, and refuses a
  symlinked node before reading its target.
- The Python hook allowance validates `-X utf8` exactly. The reported Windows quoted-path failure
  was not reproduced: `shlex.split(..., posix=False)` retains a quoted path with spaces as one
  token, and the existing quote stripping resolves it correctly.
- The canonical Markdown reference gate scans tracked dot-directories, distinguishes tracked from
  untracked runtime logs, fails conservatively when Git status is unknown, and limits the
  `learning.md` historical exemption to `skills/<slug>/learning.md`.
- Motion recipes provide an explicit reduced-motion result for WAAPI and drag dismiss/snap-back.
- Live dangling paths, the workflow lane comment, learning-ledger numbering and the retired-skill
  historical note were corrected. Dated plans and changelogs intentionally retain historical paths.

## Feedback triage

Kilo's 18 items were classified through the receiving-feedback protocol: `implement=14`,
`clarify=0`, `pushback=4`. The four pushbacks were the disproved Windows `shlex` tokenisation claim,
the intentionally historical dated-plan citation, `py -3.x` outside this repository's documented
`py -3` contract, and an unbraced environment spelling the plugin never emits. Independent review
added and closed the tracked-runtime, live-`learning.md` and static node-symlink findings.

## Structural quality

The reviewed change set is intentionally broad: 136 paths and roughly 9,421 additions / 3,751
deletions before this report. The PR body justifies that scope as one release consolidating copied
harness authorities and regenerating the dependent platform surfaces. No changed file crossed the
1,000-line approval threshold: the already-large hook test file was 1,374 lines on `main`; the two
largest new cohesive CLIs remain below the threshold (`sdd.py` and `intent_layer.py`, each under
900 lines). Their size is residual maintenance risk, not a duplicated authority or current blocker.

## Sensitive surfaces

CI and gate definitions, hook command approval, environment placeholders, subprocess invocation,
and local filesystem boundaries were touched. No payment, authentication, tenant/personal-data or
database-schema surface is present in this change.

## Verdict matrix

| Path | Result | Findings |
|---|---|---|
| evaluator (3A) | APPROVED | open P0=0 P1=0 P2=0 |
| security-reviewer (3B) | PASS | 0 blocking; one P3 local TOCTOU residual |
| explorer, performance lens (3C) | PASS | 0; 200K-character valid-tail probe completed in about 0.013 s |
| ui-ux-designer (3D) | PASS | 0; reduced-motion dismiss and snap-back both avoid the spring |
| code-review skill (3E) | UNAVAILABLE | optional skill not installed |
| `/debug audit pr` (3F) | PASS | 0 open findings |
| project lenses (`chain.lenses`) | NOT DECLARED | built-in structural, performance and motion lenses ran |
| Change set | baseRef `d9b43477963c4d45d01a14a1d173a4c3a6b3e0bf` · confidence high · graph SKIPPED | graph database unavailable; diff and focused probes used |
| Declared gates | PASS | 23/23 local gates pass; hooks, SDD 28/28, evals 6/6, file refs 7/7 |
| Project blocking list (`REVIEW.md`) | NOT DECLARED | root `REVIEW.md` is a host-project spec per `AGENTS.md`; repository gates are in `AGENTS.md` |
| CI checks | PENDING | Sonar's current-head failure was isolated to one false-positive Git subprocess sink; the justified suppression and CI must rerun green |
| Comments triaged | implement=14 clarify=0 pushback=4 | Kilo review; CodeRabbit was unavailable because the repository is below its automatic-review threshold |

## Decision

**COMMENT**

No open P0-P2 finding remains on the reviewed local tree. CI, hook permissions and filesystem
boundaries were sensitive surfaces; merge remains blocked until the committed final head passes all
remote checks.

## Ready to post

PR review completed on the corrected local tree. No P0-P2 finding remains, and all 23 local gates
pass, including hooks, SDD 28/28, evals 6/6 and file-reference regressions 7/7. Kilo's 18 items were
triaged as 14 implemented and 4 technical pushbacks. Sonar's sole Security Rating finding was a
false-positive Git subprocess sink (fixed executable, argv list, validated refs, no shell); the
final pushed head must rerun CI and Sonar green before merge.
