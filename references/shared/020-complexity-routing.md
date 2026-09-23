## Section 2: Complexity Routing

The one ladder — everything else cites it. A second table with different rows is how a plan ends up
prescribing more agents than the width cap allows.

| Level | Indicators | Execution mode | Chain |
|---|---|---|---|
| L1-L2 | Single file, known pattern, trivial | Direct local edit; one planner for explicit plan output | direct edit or concise plan |
| L3 | Multi-file, single domain | at most 1 existing specialist, only for an independently useful scope | inline spec |
| L4-L5 | Multi-domain, parallel changes | 2-3 existing specialists maximum, on disjoint files; fewer when fewer scopes exist | spec + plan file |
| L6+ | Architecture, migration, multi-service, or any surface in `chain.riskSurfaces` | coordinator + only the necessary specialists; Agent Teams only when the runtime exposes them | + pre-mortem, ADR, architecture pass |

L6+ is the ceiling — the plan workflow classifies into `L1..L6`, and nothing downstream can
represent an L7. **Unsure between two levels → the lower one, said in one line; a surface in
`chain.riskSurfaces`, a second domain or a failing gate raises it, doubt does not.** Tier decides
which gates apply; each dispatch still needs an independently useful scope. Available slots are
capacity, never a quota to fill. `025-solution-ladder.md` sizes the solution at every tier.

### Model and effort per unit of work

Tier by unit, not task. **Mechanical** units use a cheaper model/lower effort. The role's declared
model (agent frontmatter; workflows pass `M(role)`) governs the driver and verification; neither
upgrades by default. Escalate a single unit once only for material failure, contradictory evidence
or demonstrated risk.

At L3+, delegate self-contained work when briefing costs less than doing it in the parent. Send
multi-file reading, test/gate loops and mechanical sweeps to the matching specialist on its declared
model. Without a useful independent split, stay in one session with the same gates.
A one-line fix gets no plan and no gate.
