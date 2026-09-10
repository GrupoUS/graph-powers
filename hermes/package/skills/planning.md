---
name: planning
description: "Use when deciding how to build or decompose a multi-step feature, exploring high-stakes open-ended implementation alternatives, or executing an approved plan with behaviour-first tests. Trigger on implementation plans, architecture trade-offs, brainstorm, divergent ideation, ADHD mode, integrations, unclear ordering, sprint scope, implement approved plan, TDD. Loaded by /plan and /implement. Not for a known single-file fix or diagnosis-only work."
---

> Hermes: first load `skill_view("graph-powers:graph-engineering")` for native calls and host-policy limits. `content/` paths are `file_path` values relative to the common registered-document parent. Source tools/model frontmatter is not host enforcement.

# Planning

Classify before designing: reuse the smallest existing solution, state assumptions, and make each
goal observable. Read `content/skills/planning/references/step-0-inventory.md` only for work beyond a direct edit; use
`content/skills/planning/references/issue-triage.md` only for a GitHub issue and `content/skills/planning/references/wayfinding.md` only when open
decisions prevent a task list.

| Tier | Route | Stop when |
|---|---|---|
| L1-L2 | direct, bounded edit | focused proof passes |
| L3 | `content/skills/planning/references/phase-a-brainstorm.md` light path | design is acknowledged |
| L4+ | Phase A, then `content/skills/planning/references/phase-b-writing-plans.md` | approved executable plan exists |
| L5+ | Phase C via `content/skills/planning/references/phase-c-executing-plans.md` | tasks, gates and final review have evidence |

Read only the phase being entered. Phase A owns design/spec; B owns task grammar, ownership and
plan gates; C owns leases, writer waves, critics and close. A current approval covers its stated
transition; pause again only for a new decision, authority, or material scope change.
`content/skills/planning/references/loop-engineering.md` is for a loop that needs a cap or reset, and `content/skills/planning/references/dispatch-matrix.md`
and `content/skills/planning/references/layer-map.md` are for Phase B assignments/order.

`/gauntlet` is opt-in, never default: at L3+ it accepts either an objective or an approved plan. An
objective enters Step 0 → Phase A → Phase B first; only a validated eligible plan loads
`content/skills/planning/references/gauntlet-loop.md`. Preserve its leases, independent critic, configured caps and evidence.
For a task marked `TDD: required`, read `content/skills/planning/references/execution/tdd-policy.md`; load the other
execution prompts only for their dispatch/review event.

Do not code before the applicable gate. Stop and surface a missing binary goal, unresolved blocker,
correction-cap exhaustion, unsafe parallel ownership, or unapproved destructive/Git action. Keep
reviewable working-tree changes; commit, push, merge and staging each need action/scope authorization,
including valid approval already given in the session.

Shared routing, paths, parallel limits and verification remain in
`content/references/shared/`. Subagent context and return shape are in
`content/skills/senior-prompt-engineer/references/agent-handoff-contracts.md`.
