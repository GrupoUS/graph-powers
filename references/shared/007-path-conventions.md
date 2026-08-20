## Section 0.7: Path Conventions

**One plan is one directory.** Everything needed to execute it lives there, and nothing else does:

| Artifact | Path |
|---|---|
| Plan directory | `${paths.planDir}/YYYY-MM-DD-<slug>/` |
| The plan | `<plan dir>/PLAN.md` — contract sections, phases, tasks, phase gates |
| Design spec | `<plan dir>/spec.md` |
| Plan handoff | `<plan dir>/HANDOFF.md` (a context reset mid-plan); `/evolve handoff` writes `.graph-powers/HANDOFF.md` |
| Map, when the request is fog | `${paths.planDir}/maps/YYYY-MM-DD-<slug>-map.md` |
| Audit report | `docs/AUDIT-REPORT-YYYY-MM-DD.md` |
| Phase tracker | `.graph-powers/logs/progress.md` — appended by `/implement` when a phase completes |

`${paths.planDir}` defaults to `docs/plans`. Folders are created on first write.

**Reading a plan, accept both shapes**: the directory, or a bare `${paths.planDir}/*.md` written
before this convention. **Writing one, always the directory** — gates that live beside the plan are
gates somebody re-runs.
