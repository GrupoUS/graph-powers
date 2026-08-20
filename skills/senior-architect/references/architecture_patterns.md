# Architecture Patterns — Deep-Module Vocabulary

The shared vocabulary for every output of `senior-architect`. Use these terms exactly; do not
substitute "component," "service," "API," or "boundary." Consistent language is the whole point.

## Glossary

**Module**: anything with an interface and an implementation. Deliberately scale-agnostic: a
function, class, package, or tier-spanning slice. _Avoid_: unit, component, service.

**Interface**: everything a caller must know to use the module correctly: the type signature, but
also invariants, ordering constraints, error modes, required configuration, and performance
characteristics. _Avoid_: API, signature (too narrow — they refer only to the type-level surface).

**Implementation**: what is inside a module, its body of code. Distinct from **Adapter**: a thing
can be a small adapter with a large implementation (a Postgres repo) or a large adapter with a
small implementation (an in-memory fake). Reach for "adapter" when the seam is the topic;
"implementation" otherwise.

**Depth**: leverage at the interface. The amount of behaviour a caller (or test) can exercise per
unit of interface they have to learn. A module is **deep** when a large amount of behaviour sits
behind a small interface, **shallow** when the interface is nearly as complex as the
implementation.

**Seam** _(Michael Feathers)_: a place where you can alter behaviour without editing in that place;
the location at which a module's interface lives. Where to put the seam is its own design decision,
distinct from what goes behind it. _Avoid_: boundary (overloaded with DDD's bounded context).

**Adapter**: a concrete thing that satisfies an interface at a seam. Describes *role* (what slot it
fills), not substance (what is inside).

**Leverage**: what callers get from depth. More capability per unit of interface they learn. One
implementation pays back across N call sites and M tests.

**Locality**: what maintainers get from depth. Change, bugs, knowledge, and verification
concentrate in one place rather than spreading across callers. Fix once, fixed everywhere.

## Deep vs Shallow

**Deep module** = small interface + lots of implementation:

```
┌─────────────────────┐
│   Small Interface   │  ← Few methods, simple params
├─────────────────────┤
│                     │
│  Deep Implementation│  ← Complex logic hidden
│                     │
└─────────────────────┘
```

**Shallow module** = large interface + little implementation (avoid):

```
┌─────────────────────────────────┐
│       Large Interface           │  ← Many methods, complex params
├─────────────────────────────────┤
│  Thin Implementation            │  ← Just passes through
└─────────────────────────────────┘
```

When designing an interface, ask:

- Can I reduce the number of methods?
- Can I simplify the parameters?
- Can I hide more complexity inside?

## Principles

**Depth is a property of the interface, not the implementation.** A deep module can be internally
composed of small, mockable, swappable parts; they just are not part of the interface. A module can
have **internal seams** (private to its implementation, used by its own tests) as well as the
**external seam** at its interface.

**The deletion test.** Imagine deleting the module. If complexity vanishes, it was a pass-through.
If complexity reappears across N callers, it was earning its keep.

**The interface is the test surface.** Callers and tests cross the same seam. If you want to test
*past* the interface, the module is probably the wrong shape.

**One adapter means a hypothetical seam. Two adapters means a real one.** Do not introduce a seam
unless something actually varies across it.

## Designing for Testability

Good interfaces make testing natural:

1. **Accept dependencies, do not create them.**

   ```typescript
   // Testable
   function processOrder(order, paymentGateway) {}

   // Hard to test
   function processOrder(order) {
     const gateway = new StripeGateway();
   }
   ```

2. **Return results, do not produce side effects.**

   ```typescript
   // Testable
   function calculateDiscount(cart): Discount {}

   // Hard to test
   function applyDiscount(cart): void {
     cart.total -= discount;
   }
   ```

3. **Small surface area.** Fewer methods = fewer tests needed. Fewer params = simpler test setup.

## Relationships

- A **Module** has exactly one **Interface** (the surface it presents to callers and tests)
- **Depth** is a property of a **Module**, measured against its **Interface**
- A **Seam** is where a **Module**'s **Interface** lives
- An **Adapter** sits at a **Seam** and satisfies the **Interface**
- **Depth** produces **Leverage** for callers and **Locality** for maintainers

## Anti-Patterns

**Pass-through module.** A module whose interface is as wide as its implementation — it adds a
layer without adding depth. Fails the deletion test: removing it makes callers simpler.

**Premature port.** A seam with exactly one adapter. Indirection without variation. The cost is the
interface itself; the benefit only arrives when a second adapter appears.

**Leaked abstraction.** When internal details of a module appear in its interface — callers must
know how the implementation works to use it correctly. The interface is not hiding complexity, it
is forwarding it.

**Testability extraction.** Extracting pure functions from a module solely for testability, when the
real bugs hide in how those functions are called. The locality of defects shifts away from where
tests can reach them.

**Interface obesity.** Adding methods, parameters, or configuration to a module's interface "for
flexibility" when no caller needs the flexibility today. Each addition is interface cost with no
leverage return.

## Rejected Framings

- **Depth as ratio of implementation-lines to interface-lines** (Ousterhout line count): rewards
  padding the implementation. We use depth-as-leverage instead.
- **"Interface" as the TypeScript `interface` keyword or a class's public methods**: too narrow.
  Interface here includes every fact a caller must know.
- **"Boundary"**: overloaded with DDD's bounded context. Say **seam** or **interface**.
