## Section 2: Complexity Routing

The one ladder — everything else cites it. A second table with different rows is how a plan ends up
prescribing more agents than the width cap allows.

| Level | Indicators | Execution mode | Chain |
|---|---|---|---|
| L1-L2 | Single file, known pattern, trivial | Direct — no agents | direct edit, no plan file |
| L3 | Multi-file, single domain | at most 1 existing specialist, only for an independently useful scope | inline spec |
| L4-L5 | Multi-domain, parallel changes | 2-3 existing specialists maximum, on disjoint files; fewer when fewer scopes exist | spec + plan file |
| L6+ | Architecture, migration, multi-service, or any surface in `chain.riskSurfaces` | coordinator + only the necessary specialists; Agent Teams only when the runtime exposes them | + pre-mortem, ADR, architecture pass |

L6+ is the ceiling — the plan workflow classifies into `L1..L6`, and nothing downstream can
represent an L7. **Unsure between two levels → the lower one, said in one line; a surface in
`chain.riskSurfaces`, a second domain or a failing gate raises it, doubt does not.** Tier decides
which gates apply; each dispatch still needs an independently useful scope. Available slots are
capacity, never a quota to fill. `025-solution-ladder.md` sizes the solution at every tier.

### Model and effort per unit of work

Tier by what the unit *is*, not by how big the task around it is. **Mechanical** — a rename sweep,
fixtures, applying an already-decided pattern across files — takes the cheaper model or lower effort.
**Design, integration and every verification pass** take the strong model, and so does the driver,
always: a weak driver invalidates every verification below it.

Below roughly half an hour of real work, or when the work has no useful independent split, do not
orchestrate at all: a subagent's context re-establishment costs more than the parallelism buys. Stay
in one session, with the same gates. A one-line fix gets no plan and no gate.
