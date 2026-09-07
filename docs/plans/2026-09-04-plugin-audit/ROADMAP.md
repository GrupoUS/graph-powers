# Graph Powers — phased improvement roadmap

**Date:** 2026-09-04 · **Completed:** 2026-09-05 · **Status:** all ten tasks and 26 phase gates closed; local version 1.19.2, reviewed and unstaged.
**Baseline:** 1.19.1 / `0a59d3a7`.
**Design authority:** [specification](spec.md).
**Evidence:** [full audit](../../AUDIT-REPORT-2026-09-04.md).

The audit found 11 evidence-backed findings, grouped into **10 atomic tasks across four plans**.
This roadmap is an index, not a Gauntlet execution file. Select a child `PLAN.md` explicitly.
Splitting here respects the existing 12-task and 8-dispatch caps; it does not authorize automatic
continuation into another plan or reset a capped workflow.

## Phase 0 — Audit and baseline (completed)

Inventory: 327 tracked files. Initial gates: 24/24 pass. Additional client, frontmatter and install
fixtures pass. Seven targeted probes expose gaps. Native installation: 225 source files match,
12 roles exist, old copied entries are disabled. No source fixes were made during initial discovery; implementation results appear in phases 1–4 below. The live installation was not changed.

## Phase 1 — Predictable installation (completed)

**Plan:** [01-installation/PLAN.md](01-installation/PLAN.md).
**Value:** a preview stays a preview; reinstall retains project-owned instructions; missing assets repair.

| Task | Deliverable | Priority |
|---|---|---|
| T1.1 | Strict arguments and side-effect-free update dry-run | F01 P1 + F07 P2 |
| T2.1 | Seed adopted rules without overwriting existing files | F02 P1 |
| T2.2 | Verify recorded required assets before same-version skip | F04 P2 |

## Phase 2 — Preserve Codex choices (completed)

**Plan:** [02-codex-settings/PLAN.md](02-codex-settings/PLAN.md).
**Value:** custom homes resolve correctly and automatic refresh retains manual model/effort choices.

| Task | Deliverable | Priority |
|---|---|---|
| T1.1 | Correct reference destinations for custom Codex home | F05 P2 |
| T1.2 | Preserve existing model/effort during ordinary role refresh | F03 P1 |

These fixes are independently useful. Their ordering after phase 1 is for review focus; only shared
file ownership serializes them. It is not an invented data dependency.

## Phase 3 — Gates that catch the observed misses (completed)

**Plan:** [03-validation/PLAN.md](03-validation/PLAN.md).
**Value:** enforce the promised path contract and run the already existing capture tests.

| Task | Deliverable | Priority |
|---|---|---|
| T1.1 | Dot-relative reference detection and proven stale-path repair | F06 P2 |
| T1.2 | Capture-regression CI invocation and current verification inventory | F11 P2 |

## Phase 4 — Smaller context, accurate routes and contracts (completed)

**Plan:** [04-context-routing/PLAN.md](04-context-routing/PLAN.md).
**Value:** less irrelevant reading for small fixes, correct resource routing, no misleading capability claims.

| Task | Deliverable | Priority |
|---|---|---|
| T1.1 | Conditional debug context, canonical inspection dispatch and perf resource routing | F08/F09 P2 |
| T2.1 | Synchronize current capabilities with runtime evidence | F10 P2 |
| T2.2 | Prepare synchronized local version/changelog metadata | Required delivery contract |

## Execution and review

Read each child plan's ownership, dependencies, subtasks and regression watchlist. Start with the
smallest focused check, observe RED for behavior changes, make the minimum patch, observe GREEN,
then run phase gates. No phase may claim an independent review that did not occur.

Each plan must reserve capacity for its writer wave, independent wave reviewer, final reviewer and
`/verify loop`. The schema currently caps a workflow at 8 dispatches, width 3, re-patches 2, and
tasks 12. Count every consultation and verification dispatch; do not treat 8 as a new allowance per
phase. Group related tasks in the same writer lane only when their explicit order and ownership
remain valid. If the required remaining work cannot fit, stop with an honest checkpoint and return
for a narrower approved slice; never omit a reviewer or launch a new workflow to bypass the cap.

Initial discovery ran locally. The user then explicitly authorized specialist/reviewer execution.
The runtime retains only three child contexts, so registered roles are reused for independent
acceptance passes. No builder reviews its own work; newly isolated reviewer contexts are unavailable
and are not claimed.

## Final integration and delivery boundary

The selected local release metadata is 1.19.2 across all six version-bearing files. The changelog
records accepted work, and the existing Codex manifest formatting was preserved. The final declared
checks and relevant client-generation/fixture checks passed; detailed outputs are linked from
the audit and task ledgers. Commit, push, publishing and refreshing the actual installation were
not performed and still require their separate authorization.

## Not scheduled

No hook dispatcher, model upgrade, new agent, registry, generic configuration engine, global
cleanup, provider-wide evaluation campaign or permission-policy change. Reopen only with a measured
failure, a named consumer or an explicit owner decision.

## Review status

Audit and plan author self-review: complete.
Mechanical Gauntlet validation: recorded with the audit evidence after authoring.
Independent review: all four plans, task waves and final acceptance boundaries PASS.
Every requested correction has deciding evidence in its plan/ledger. One nonblocking native
provenance-comment note remains documented in the audit; no runtime field is incorrect.
Execution approval: granted by the user for all scoped local corrections; no publication/global change.

## Final validation

- 25/25 declared checks passed; all ten task and 26 phase-gate checkboxes have evidence.
- Debug mandatory context estimate: 59,276 -> 52,147 bytes (-12.0%); total floor 261,858 bytes.
- Six version-bearing files: 1.19.2; native manifest formatting preserved against TASK_BASE.
- HEAD/index and external hook changes preserved; no commit, publication or real installation.
- All plan leases released. Runtime reviewer-context and platform limitations are recorded in the audit.
