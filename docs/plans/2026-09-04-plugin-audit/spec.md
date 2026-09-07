# Graph Powers improvement specification

**Date:** 2026-09-04
**Status:** completed locally on 2026-09-05; all four reviewed plans executed and validated. Version 1.19.2 remains unstaged and unpublished.
**Evidence authority:** [audit report](../../AUDIT-REPORT-2026-09-04.md).

## Destination

Make the existing plugin safer to install and refresh, truthful about its capabilities, and cheaper
to route for small tasks. Done means the accepted failure probes have regression tests that now
pass, all retained clients and modes remain available, and the declared final gates pass without
relaxing their ceilings or modifying the operator's environment.

## Requirements

| ID | Observable requirement | Work order |
|---|---|---|
| N1 | Dry-run performs no update; unsupported CLI input fails before side effects | installation T1.1 |
| N2 | Reinstall preserves every existing adopted project rule | installation T2.1 |
| N3 | Missing recorded role/skill artifacts invalidate same-version completion | installation T2.2 |
| N4 | Generated references resolve under the selected Codex home | Codex settings T1.1 |
| N5 | Refresh preserves explicit native model/effort assignments | Codex settings T1.2 |
| N6 | The reference gate catches a missing dot-relative live path | validation T1.1 |
| N7 | Existing capture regressions run in CI and local verification | validation T1.2 |
| N8 | Small debug tasks avoid irrelevant context and read-only dispatch follows the floor | context/routing T1.1 |
| N9 | Resource aliases reach the implemented resource audit | context/routing T1.1 |
| N10 | Capability descriptions match runtime and do not assume a user's global settings | context/routing T2.1 |

## Architecture and reuse

Keep the existing source directories, client generators, config reader, hook manifest and SDD
engine. Reuse the existing fixture tests and validators. Extend copy/completion behavior at its
current owner. No generic installer framework, second config registry, new specialist or hook
dispatcher is part of this design.

Prefer preserving native scalar model/effort assignments during ordinary companion refresh.
An explicit config/model override still wins. Unknown or malformed existing role syntax must
exit nonzero before mutating any destination file, not cause guessed settings to replace user choices.
This deliberately covers the native role configuration already produced by this project; it is not
a reason to add a general TOML editor.

## Constraints

- Preserve the current checkout and the pre-existing manifest formatting.
- Execute locally; real global settings and installed caches are observational scope only.
- No commit, push, merge, publication or destructive cleanup is included.
- Keep all current clients, commands, agents, skills, safety decisions and negative guarantees.
- Preserve Python/Bun compatibility, fail-open hooks and the current project runner.
- No model selection change; no permission loosening; no new production dependency.
- A line-count reduction is not accepted if it merely hides context from the estimator.

## Risk and rollback

| Risk | Score (probability × impact) | Mitigation |
|---|---|---|
| Installation overwrites project-owned files | 6 | Sentinel tests in both scopes; seed missing files only |
| A completeness fix rewrites intact installations every time | 4 | Positive same-version idempotency fixture; existence checks before any expensive work |
| Refresh loses manual model choices | 6 | Parse preserved supported scalar assignments, explicit override tests, safe handling of malformed files |
| Prompt shortening drops a safety or mode boundary | 6 | Keep shared authorities; negative route cases and bounded real traces before acceptance |
| A new gate produces false positives | 4 | Test valid relative paths, historical records and malformed/missing paths separately |
| Broad execution exceeds the Gauntlet spawn budget | 4 | Four independent plans; count reviewers and final verification before each dispatch; stop at the cap |

Changes stay unstaged. Rollback restores only the accepted slice's files from the pre-slice snapshot
or manually reverses its diff. Never use a blanket reset, stash deletion or reinstall against the
operator's home. Existing user changes are excluded from every restoration.

### ADR: preserve the source; repair boundaries

**Options:** rewrite installation/orchestration as a new framework, or repair the proven seams.
**Decision:** repair the seams using current generators, helpers, regression suites and phase engine.
**Reason:** the working baseline already provides the capabilities; the failures are concentrated
in ownership, option handling, completion checks and stale routing.
**Consequence:** compatibility code remains where it has a current consumer; simplification is
measured through less unconditional context and fewer conflicting instructions.

## Acceptance and exclusions

Each work order has its own acceptance, ownership, dependency, TDD status and gate. No task is
complete while its evidence is pending. Provider/Desktop/macOS/Windows checks are reported at the
level actually run; simulated fixtures never become a native-runtime PASS.

A policy decision about automatic permission repair, a new live provider evaluation campaign,
global cleanup and actual installation/publication are outside these four plans.

## Acceptance outcome

N1–N10 are met by the ten completed task blocks and 26 completed phase gates in the child plans.
The full local declared gate batch passed 25/25, with changed final inputs checked again.
The debug context estimate fell about 12.0% without a raised budget. Manual/global settings,
the current checkout and the user's initial manifest formatting were preserved.

One advisory provenance-comment issue remains nonblocking; supported native refresh input is
the canonical emitted header, not arbitrary TOML. Reviewer contexts were retained due runtime
limits, and the final reserved reviewer used two explicit acceptance stages. These limitations,
plus unrun provider/remote-platform checks, are recorded in the audit rather than claimed covered.
