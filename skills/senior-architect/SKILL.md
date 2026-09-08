---
name: senior-architect
description: "Trade-off analysis, deep-module design and structural review: when a decision is about where a seam goes, whether a module is too shallow, which design alternative wins, or how a change affects service boundaries. Loaded after planning has a shape. Not for debugging (debugger), prompt design (senior-prompt-engineer), or choosing what to build (planning)."
---

# Senior Architect

Use after planning has a bounded problem. Compare viable seams and module boundaries against the
current system, select the smallest design that hides complexity, and name the contract, failure
mode, migration/rollback and proof. Do not invent layers or turn a local repair into architecture.

Read `references/architecture_patterns.md` for vocabulary and anti-patterns,
`references/system_design_workflows.md` for a deepening/design-twice review, and
`references/tech_decision_guide.md` for dependency/seam trade-offs. Stop when one option is
recommended with evidence and an implementation-ready boundary; route a bug, prompt, or open plan to
its owner.
