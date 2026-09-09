---
name: intent-layer
description: "Use when a repository's AGENTS.md hierarchy has to be built, grown or audited: the root node plus child nodes in the subtrees that earn one. Trigger on: set up AGENTS.md, add an intent layer, agents keep misreading where things live, which directories need their own AGENTS.md, this AGENTS.md is too long, audit our AGENTS.md files. Runs at setup step 4b and from /evolve. Not for loading context (/prime), a domain rule (setup step 5) or this plugin's wiring (skill-improve)."
---

# Intent Layer

For a diff audit, read `references/node-anatomy.md § Diff-scoped advisory audit` only when changed rules, paths, commands, consumers or invariants could contradict instructions. Otherwise report no relevant drift and stop. This route never builds a hierarchy.

For hierarchy work, build the smallest `AGENTS.md` hierarchy that tells an agent where rules change. Start at the root;
add a child only for a subtree with a distinct purpose, owner, tooling or safety rule. Each node
links downward; avoid copying global rules and remove no user decisions.

Read `references/capture-protocol.md` while deciding whether a node earns existence and
`references/node-anatomy.md` only while writing/auditing its shape. Validate navigation and
applicable instructions from root to target. Stop when every real boundary has one concise owner and
a new child would add no decision-relevant context.
