# System Design Workflows

Detail for the deepening scan and design-it-twice capabilities in `SKILL.md`. Both use the
vocabulary in `architecture_patterns.md`.

---

## Deepening a Module

How to deepen a cluster of shallow modules safely, given its dependencies.

### Dependency Categories

When assessing a candidate for deepening, classify its dependencies. The category determines how
the deepened module is tested across its seam.

| Category | What it is | Deepening strategy | Test strategy |
|---|---|---|---|
| **In-process** | Pure computation, in-memory state, no I/O | Merge modules, test through new interface directly | No adapter needed |
| **Local-substitutable** | Dependencies with local test stand-ins (PGLite for Postgres, in-memory filesystem) | Deepen if stand-in exists. Seam is internal | Test with stand-in running in test suite |
| **Remote but owned** | Own services across a network (microservices, internal APIs) | Define a port at the seam. Deep module owns logic; transport injected as adapter | In-memory adapter for tests, HTTP/gRPC adapter for production |
| **True external** | Third-party services (Stripe, Twilio) you do not control | Take external dependency as injected port | Mock adapter for tests |

**Recommendation shape for remote-but-owned:** "Define a port at the seam, implement an HTTP
adapter for production and an in-memory adapter for testing, so the logic sits in one deep module
even though it is deployed across a network."

### Seam Discipline

- **One adapter means a hypothetical seam. Two adapters means a real one.** Do not introduce a port
  unless at least two adapters are justified (typically production + test). A single-adapter seam is
  just indirection.
- **Internal seams vs external seams.** A deep module can have internal seams (private to its
  implementation, used by its own tests) as well as the external seam at its interface. Do not
  expose internal seams through the interface just because tests use them.

### Testing Strategy: Replace, Do Not Layer

- Old unit tests on shallow modules become waste once tests at the deepened module's interface
  exist; delete them
- Write new tests at the deepened module's interface. The **interface is the test surface**
- Tests assert on observable outcomes through the interface, not internal state
- Tests should survive internal refactors — they describe behaviour, not implementation. If a test
  has to change when the implementation changes, it is testing past the interface

---

## Design-it-Twice (Detail)

Exploring alternative interfaces for a deepening candidate or a new module. Each step below expands
the summary in `SKILL.md`.

### Step 1 — Frame the Problem Space

Before spawning sub-agents, write a user-facing explanation:

- The constraints any new interface would need to satisfy
- The dependencies it would rely on, and which category they fall into (see above)
- A rough illustrative code sketch to ground the constraints — not a proposal, just a way to make
  the constraints concrete

Show this to the user, then proceed immediately. The user reads and thinks while sub-agents work
in parallel.

### Step 2 — Spawn Sub-agents

Spawn 3+ sub-agents in parallel. Each must produce a **radically different** interface for the
module.

Prompt each sub-agent with a separate technical brief (file paths, coupling details, dependency
category, what sits behind the seam). The brief is independent of the user-facing explanation in
Step 1. Give each agent a different design constraint:

- **Agent 1 — Minimal:** "Minimize the interface: aim for 1 to 3 entry points max. Maximise
  leverage per entry point."
- **Agent 2 — Flexible:** "Maximise flexibility: support many use cases and extension."
- **Agent 3 — Default-optimised:** "Optimise for the most common caller: make the default case
  trivial."
- **Agent 4 — Ports (if applicable):** "Design around ports and adapters for cross-seam
  dependencies."

Include the vocabulary from `architecture_patterns.md` and the project's domain language in the
brief so each sub-agent names things consistently.

Each sub-agent outputs:

1. Interface (types, methods, params, plus invariants, ordering, error modes)
2. Usage example showing how callers use it
3. What the implementation hides behind the seam
4. Dependency strategy and adapters (category from above)
5. Trade-offs: where leverage is high, where it is thin

### Step 3 — Present and Compare

Present designs sequentially so the user can absorb each one, then compare them in prose. Contrast
by:

- **Depth** — leverage at the interface
- **Locality** — where change concentrates
- **Seam placement** — where the seam sits, how many adapters justify it

Give a strong recommendation: which design is strongest and why. If elements from different designs
combine well, propose a hybrid. Be opinionated — the user wants a strong read, not a menu.

---

## Deepening Scan — Candidate Presentation

Each candidate gets a card with:

- **Title:** short, names the deepening (e.g. "Collapse the Order intake pipeline")
- **Strength badge:** `Strong` | `Worth exploring` | `Speculative`
- **Dependency category:** `in-process` | `local-substitutable` | `ports-and-adapters` | `mock`
- **Files:** monospaced list
- **Problem:** one sentence. What hurts. In vocabulary terms.
- **Solution:** one sentence. What changes.
- **Benefits:** bullets, each 6 words or fewer. E.g. "Tests hit one interface", "Pricing logic
  stops leaking", "Delete 4 shallow wrappers"
- **ADR callout** (if applicable): one line when the candidate contradicts an existing ADR — only
  surface it when the friction is real enough to warrant revisiting

**Phrasings that fit the style:**

- "Order intake module is shallow: interface nearly matches the implementation."
- "Pricing leaks across the seam."
- "Deepen: one interface, one place to test."
- "Two adapters justify the seam: HTTP in prod, in-memory in tests."

**Benefits bullets** name the gain in vocabulary terms: "locality: bugs concentrate in one module",
"leverage: one interface, N call sites", "interface shrinks; implementation absorbs the wrappers".
Do not write "easier to maintain" or "cleaner code" — those terms are not in the vocabulary and
do not earn their place.

No hedging, no throat-clearing, no "it is worth noting that". If a sentence could be a bullet,
make it a bullet. If a bullet could be cut, cut it.
