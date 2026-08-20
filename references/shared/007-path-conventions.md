## Section 0.7: Path Conventions

Specs, plans, and learnings produced by the superpowers pipeline use these canonical paths:

| Artifact | Path | Producer |
|---|---|---|
| Design spec | `${paths.planDir}/specs/YYYY-MM-DD-<topic>-design.md` | `Skill("superpowers:brainstorming")` |
| Implementation plan | `${paths.planDir}/YYYY-MM-DD-<topic>-plan.md` | `Skill("superpowers:writing-plans")` |
| Session handoff | `.graph-powers/HANDOFF.md` | `/evolve handoff` |
| Audit report | `docs/AUDIT-REPORT-YYYY-MM-DD.md` | `/debug audit` |
| Phase tracker | `.graph-powers/logs/progress.md` | `/implement` (append on phase complete) |

Folders are created on first write. `.graph-powers/logs/progress.md` is the chronological phase tracker; `/implement` appends to it when a phase completes.
