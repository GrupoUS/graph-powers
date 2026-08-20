# Tech Decision Guide

Trade-off analysis framework and decision records for architecture decisions. Uses the vocabulary
in `architecture_patterns.md`.

---

## Trade-off Analysis Framework

Every architecture decision is a trade-off. This framework makes the trade-off explicit.

### The Three Questions

Before any structural change, answer:

1. **What depth does this create or destroy?** Does the module become deeper (more behaviour behind
   a smaller interface) or shallower (wider interface, thinner implementation)?
2. **Where does change concentrate after this?** Does locality improve (bugs and modifications in
   one place) or scatter (the same change touches N files)?
3. **What is the interface cost?** Every abstraction, port, adapter, and parameter is interface
   cost. What leverage does the caller get in return?

### Decision Matrix

| Factor | Favours deepening | Favours keeping current |
|---|---|---|
| Hot-spot frequency | Module changes often | Module is stable, rarely touched |
| Test coverage | Current tests require knowledge of internals | Current tests work through the interface already |
| Caller count | Many callers repeat the same setup | One or two callers, each with different needs |
| Deletion test | Deleting the module pushes complexity to N callers | Deleting the module makes things simpler |
| Adapter count | Two+ real adapters (prod + test, or prod + staging) | Only one adapter exists or is foreseeable |
| Interface width | Interface is nearly as wide as implementation | Interface is already small relative to implementation |

### When NOT to Deepen

- The module is stable and rarely touched — deepening is a cost with no leverage return
- Only one adapter exists and no second is foreseeable — the seam is hypothetical
- The module fails the deletion test by making things simpler — it is dead weight, not shallow
- The refactor would cross a domain boundary that exists for organisational, not technical, reasons
- An ADR records a load-bearing reason for the current structure

---

## Dependency Category Quick Reference

Used when assessing deepening candidates and designing interfaces. Full detail in
`system_design_workflows.md`.

| Category | Signal | Test approach |
|---|---|---|
| In-process | No I/O, pure computation | Direct — no adapter |
| Local-substitutable | Has a local stand-in (PGLite, in-memory FS) | Stand-in in test suite |
| Remote but owned | Your own services across the network | Port + in-memory adapter |
| True external | Third-party API you do not control | Port + mock adapter |

---

## Architecture Decision Records

When a deepening candidate is rejected with a load-bearing reason, offer an ADR. Only when the
reason would genuinely prevent a future explorer from re-suggesting the same thing. Skip ephemeral
reasons ("not worth it right now") and self-evident ones.

### ADR Shape

```markdown
# ADR-NNNN: [Title — what was decided]

## Status: Accepted | Superseded by ADR-MMMM

## Context
What prompted the decision. Which modules, seams, or interfaces were involved.
State the trade-off in vocabulary terms.

## Decision
What was chosen and why. Name the alternative(s) that were considered.

## Consequences
What this enables (leverage, locality gains) and what it costs (interface width,
seam placement constraints, adapters that cannot be introduced).
```

### When to Revisit an ADR

An ADR is not permanent. Revisit when:

- The trade-off balance shifts (a second adapter becomes real, a hot spot moves)
- The friction the ADR accepted has grown beyond what was anticipated
- New information about the domain invalidates the original context
- A deepening scan surfaces the same candidate with stronger evidence

Mark the old ADR as superseded, linking to the new one.

---

## SOLID Through the Vocabulary Lens

SOLID principles mapped to the vocabulary, for use in architecture reviews:

| Principle | In vocabulary terms |
|---|---|
| **Single Responsibility** | One module, one reason to change. Locality: change concentrates |
| **Open/Closed** | Extend through a new adapter at the seam, not by editing the module |
| **Liskov Substitution** | Any adapter at a seam satisfies the full interface, not a subset |
| **Interface Segregation** | Keep interfaces small — depth, not width. Separate seams for separate callers |
| **Dependency Inversion** | Depend on the interface at the seam, not the adapter behind it |
