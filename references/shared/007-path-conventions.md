## Section 0.7: Path Conventions

**One plan is one directory**, with execution evidence at the runtime paths below:

| Artifact | Path |
|---|---|
| Plan directory | `${paths.planDir}/YYYY-MM-DD-<slug>/` |
| The plan | `<plan dir>/PLAN.md` — contract sections, phases, tasks, phase gates |
| Design and findings | `<plan dir>/spec.md` — [Phase A capture](${CLAUDE_PLUGIN_ROOT}/skills/planning/references/phase-a-brainstorm.md#step-3--consolidate-research-findings) |
| Plan handoff | `<plan dir>/HANDOFF.md` (a context reset mid-plan); `/evolve handoff` writes `.graph-powers/HANDOFF.md` |
| Map, when the request is fog | `${paths.planDir}/maps/YYYY-MM-DD-<slug>-map.md` |
| Audit report | `docs/AUDIT-REPORT-YYYY-MM-DD.md` |
| Phase tracker | `.graph-powers/logs/sdd/<plan-slug>/progress.md` — appended by `/implement` when a phase completes |
| Task-review ledger | `.graph-powers/logs/sdd/<plan-slug>/task-reviews.md` — every pass, retry and block |
| Plan-review bind | `.graph-powers/logs/sdd/<plan-slug>/plan-review.json` — last round, bound to the plan SHA-256 — and `.graph-powers/logs/sdd/<plan-slug>/PLAN-REVIEW-LOG.md`, append-only, one line per round; both written by `sdd.py review-bind` |

`${paths.planDir}` defaults to `docs/plans`; create folders only on authorized writes.

**Read either shape:** a plan directory or legacy `${paths.planDir}/*.md`. **Write the directory
shape.** L1–L2 need no artifacts; L3 keeps its inline design.
