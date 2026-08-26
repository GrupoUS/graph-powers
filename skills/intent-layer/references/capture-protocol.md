# Capture protocol — where a node's content comes from

Step 5 of the skill. A node is a compressed answer to four questions, and the answers come from
the repository first and from a person second. The playbook's rule holds here as everywhere:
**never invent a value** — a contract nobody stated is not a contract, it is a guess an agent will
then enforce as fact.

## The four questions

1. What does this subtree own? What is explicitly out of its scope?
2. What must always be true here — what breaks if it is violated?
3. What repeatedly confuses someone new to it?
4. How is the usual change made — the one pattern that should always be followed?

## Source from the repository before asking

| Question | Where the repository already answers it |
|---|---|
| Ownership and scope | the manifest (`package.json`, `pyproject.toml`, `go.mod`), the directory's index or barrel file, what imports it and what it imports |
| Invariants | validators, type guards, database constraints, middleware that every route passes through, a test named after an incident |
| Confusion | `git log --oneline -- <dir>` for the reverts and the "fix again" commits; a `legacy/` or `v2/` directory that is still imported |
| The usual change | the last three commits that added the typical thing — a route, a migration, a component — and the files each one touched |

What that pass cannot answer is asked, one question at a time, and the answer is written down as
given. A person's "we had an incident where a retry double-charged" is worth more than a paragraph
of inferred rules, because it is the reason the rule exists.

## Interview set

Ask only what the repository pass left open.

**Purpose and scope** — "In one sentence, what does this area own?" · "What is explicitly not this
area's responsibility, even though it looks like it might be?"

**Entry points** — "Where does execution start here?" · "Which interface does other code use, and
which one looks public but is not?"

**Contracts and invariants** — "What must always be true here?" · "What breaks if it is not — and
has it broken?" · "Which rules are enforced by a type or a test, and which live only in someone's
head?"

**Patterns** — "How do you add a new [typical unit] here?" · "What is the canonical way to do
[the common operation]?"

**Anti-patterns** — "What mistake does someone new make here?" · "What should never be done even
though the code allows it?"

**Pitfalls** — "What is the most surprising thing about this code?" · "What looks deprecated and
is not?"

## Capture order

Leaf-first, clarity-first:

1. well-understood leaf areas — utilities, helpers, adapters;
2. domain modules — auth, billing, the product's own nouns;
3. integration layers — API clients, webhooks, queues;
4. tangled areas — legacy, the core nobody wants to touch;
5. the root and the intermediate nodes last, summarising the children.

The order is not administrative. A parent written before its children summarises code; written
after them it summarises nodes, which are already compressed and already checked.

## Summarisation rules for a parent node

1. **Summarise the children, never the raw code.** A parent that re-reads the files duplicates
   what the child already says, and the two drift.
2. **Shared facts move up.** A contract that applies to three children lives once, in their lowest
   common ancestor, and each child points at it.
3. **Cross-cutting context is the parent's own content** — how the children relate, what order
   a change crosses them in, which one owns the shared type.

## One capture, worked

```
Q: What does this area own?
A: Payment processing — the lifecycle from initiation to settlement. Billing is separate; they do
   invoicing.

→ Purpose: Owns the payment lifecycle: initiation → validation → processing → settlement.
  Does NOT own invoicing (`../billing/AGENTS.md`).

Q: What must never be violated?
A: Every payment mutation needs an idempotency key. A retry once created duplicate charges.

→ Contracts: Idempotency key on every mutation — enforced by the `ProcessorClient` type since the
  duplicate-charge incident; the type is the guard, this line is why it exists.
```

The second answer carries the incident. Keep it: an invariant with its cost attached survives the
next refactor, and one without it is the first line somebody "simplifies".
