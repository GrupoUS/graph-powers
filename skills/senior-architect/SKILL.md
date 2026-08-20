---
name: senior-architect
description: "Trade-off analysis, deep-module design and structural review: when a decision is about where a seam goes, whether a module is too shallow, which design alternative wins, or how a change affects service boundaries. Loaded after planning has a shape. Not for debugging (debugger), prompt design (senior-prompt-engineer), or choosing what to build (planning)."

---

# Senior Architect

Architecture methodology — a shared vocabulary for structural decisions and the processes that use
it. Three capabilities: **review** an existing structure through architecture lenses, **scan** a
codebase for deepening opportunities, and **explore** alternative interfaces with parallel
sub-agents.

> The vocabulary in `references/architecture_patterns.md` is the single source. Every output of this
> skill — findings, recommendations, candidate cards — uses those terms exactly. No substitutes.

## Vocabulary (summary)

Full glossary, principles and anti-patterns live in `references/architecture_patterns.md`. The six
terms used everywhere:

| Term | Meaning |
|---|---|
| **Module** | Anything with an interface and an implementation. Scale-agnostic: function, class, package, tier |
| **Interface** | Everything a caller must know: type signature, invariants, ordering, error modes, performance |
| **Depth** | Leverage at the interface. Large behaviour behind a small interface = deep; interface as wide as implementation = shallow |
| **Seam** | Where you can alter behaviour without editing in that place; where the interface lives |
| **Adapter** | A concrete thing that satisfies an interface at a seam. Describes role, not substance |
| **Leverage / Locality** | What callers get from depth (capability per unit of interface) and what maintainers get (change concentrates in one place) |

**Never substitute:** component, service, unit (for module) · API, signature (for interface) ·
boundary (for seam) · layer, wrapper (for module, when you mean module).

## When this skill loads

- Planning identified a structural decision that needs trade-off analysis
- A PR review needs architecture lenses (evaluator routes here)
- User asks about module boundaries, depth, seam placement, or design alternatives
- Codebase improvement: identifying shallow modules for deepening
- Architecture decision record: writing or evaluating an ADR

---

## Capability 1 — Architecture Review

Structural review of code changes. Complements design capabilities — reviews through an
architecture lens, ensuring consistency with established patterns. Absorbed from the retired
`architect-reviewer` agent (2026-06-09).

**Lenses:**

- **Pattern adherence** — code follows established patterns (MVC, microservices, CQRS, layered)
- **SOLID compliance** — Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion
- **Dependency analysis** — correct dependency direction; no circular dependencies
- **Depth assessment** — modules are deep (small interface, large implementation), not shallow pass-throughs
- **Seam discipline** — one adapter means hypothetical seam; two adapters means real one; no premature ports

**Use for:** structural changes in a PR · designing new services/modules · refactoring for
architecture · keeping API modifications consistent with the existing design.

**Review process:**

1. **Map the change** within the overall system architecture
2. **Identify seams** the change crosses
3. **Apply the deletion test** — if the module were deleted, does complexity vanish (pass-through) or reappear across N callers (earning its keep)?
4. **Check consistency** with existing patterns
5. **Evaluate depth** — impact on coupling, cohesion, interface width
6. **Suggest improvements** where warranted, in vocabulary terms

**Output format:**

- **Architectural impact:** High | Medium | Low
- **Pattern compliance:** checklist of relevant patterns + adherence
- **Depth assessment:** which modules are deep, which are shallow, which seams are real
- **Violations:** specific findings, each with explanation in vocabulary terms
- **Recommendations:** recommended refactoring / design changes
- **Long-term implications:** effects on maintainability, leverage, and locality

> **Guiding principle:** good architecture enables change. Flag anything that makes future changes harder.

> **Routing:** for adversarial PR or architecture review, `graph-powers:evaluator` (Mode 3/4) is the
> agent that runs it. Use this section's lenses and output format when the review is architectural.

---

## Capability 2 — Deepening Scan

Surface architectural friction and propose deepening opportunities: refactors that turn shallow
modules into deep ones. Full process in `references/system_design_workflows.md`.

### Process

#### Step 1 — Scope

**YAGNI.** Deepening pays off by making future changes easier, so put extra weight on the parts
that have recently changed.

- If the user named a direction (a module, a subsystem, a pain point), take it
- Otherwise, walk back commit history to find hot spots — files and areas that keep coming up — and
  let those paths pull your attention first
- Read the project's domain glossary and any ADRs in the area first

#### Step 2 — Explore

Spawn a sub-agent to walk the codebase. Note where you experience friction:

- Where does understanding one concept require bouncing between many small modules?
- Where are modules shallow — interface nearly as complex as the implementation?
- Where have pure functions been extracted just for testability, but the real bugs hide in how they're called (no locality)?
- Where do tightly-coupled modules leak across their seams?
- Which parts are untested, or hard to test through their current interface?

Apply the **deletion test** to anything suspected shallow: would deleting it concentrate complexity,
or just move it? "Concentrates" is the signal.

#### Step 3 — Present candidates

For each candidate, report:

- **Files:** which files/modules are involved
- **Problem:** why the current architecture causes friction (in vocabulary terms)
- **Solution:** what changes
- **Benefits:** explained as locality and leverage gains, and how tests would improve
- **Dependency category:** in-process | local-substitutable | ports-and-adapters | mock (see `references/tech_decision_guide.md`)
- **Recommendation strength:** `Strong` | `Worth exploring` | `Speculative`

End with a **top recommendation**: which candidate first and why.

Do NOT propose interfaces yet. Ask: "Which of these would you like to explore?"

#### Step 4 — Grilling loop

Once the user picks a candidate, walk the decision tree: constraints, dependencies, the shape of
the deepened module, what sits behind the seam, what tests survive.

Side effects happen inline as decisions crystallize — naming a new concept means defining it in the
project's domain glossary; sharpening a fuzzy term means updating it.

If the user rejects a candidate with a load-bearing reason, offer an ADR when the reason would
genuinely prevent a future explorer from re-suggesting the same thing.

Want to explore alternative interfaces? → Capability 3.

---

## Capability 3 — Design-it-Twice

When the user wants to explore alternative interfaces for a module or deepening candidate. Based on
Ousterhout's "Design It Twice": your first idea is unlikely to be the best. Full process in
`references/system_design_workflows.md`.

### Process

1. **Frame the problem space** — constraints any new interface must satisfy, dependencies and their
   categories (see `references/tech_decision_guide.md`), a rough illustrative code sketch to ground
   the constraints. Show to user, then proceed immediately.

2. **Spawn 3+ sub-agents in parallel** — each produces a radically different interface. Give each a
   different design constraint:
   - Agent 1: Minimize the interface — 1 to 3 entry points max. Maximise leverage per entry point.
   - Agent 2: Maximise flexibility — support many use cases and extension.
   - Agent 3: Optimise for the most common caller — make the default case trivial.
   - Agent 4 (if applicable): Design around ports and adapters for cross-seam dependencies.

   Each sub-agent outputs: interface (types, methods, params, invariants, error modes) · usage
   example · what the implementation hides behind the seam · dependency strategy and adapters ·
   trade-offs (where leverage is high, where thin).

3. **Present and compare** — contrast by depth (leverage at interface), locality (where change
   concentrates), and seam placement. Give a strong recommendation. If elements from different
   designs combine well, propose a hybrid. Be opinionated.

---

## References

| File | Content |
|---|---|
| `references/architecture_patterns.md` | Full vocabulary, principles, testability, anti-patterns |
| `references/system_design_workflows.md` | Deepening methodology + design-it-twice detail |
| `references/tech_decision_guide.md` | Dependency categories, seam discipline, trade-off analysis framework |
