## Section 2: Complexity Routing

The one ladder — everything else cites it. A second table with different rows is how a plan ends up
prescribing more agents than the width cap allows.

| Level | Indicators | Execution mode | Chain |
|---|---|---|---|
| L1-L2 | Single file, known pattern, trivial | Direct — no agents | direct edit, no plan file |
| L3 | Multi-file, single domain | 1 background agent | inline spec |
| L4-L5 | Multi-domain, parallel changes | 2-3 agents on disjoint files | spec + plan file |
| L6+ | Architecture, migration, multi-service, or any surface in `chain.riskSurfaces` | coordinator + specialists; Agent Teams only when the runtime exposes them | + pre-mortem, ADR, architecture pass |

L6+ is the ceiling — the plan workflow classifies into `L1..L6`, and nothing downstream can
represent an L7. **Unsure between two levels → take the higher one:** one extra phase is cheap, a
phase skipped on risky work is not.

### Model and effort per unit of work

Tier by what the unit *is*, not by how big the task around it is. **Mechanical** — a rename sweep,
fixtures, applying an already-decided pattern across files — takes the cheaper model or lower effort.
**Design, integration and every verification pass** take the strong model, and so does the driver,
always: a weak driver invalidates every verification below it.

Below roughly half an hour of real work, do not orchestrate at all: a subagent's context
re-establishment costs more than the parallelism buys. Stay in one session, with the same gates. A
one-line fix gets no plan and no gate.
