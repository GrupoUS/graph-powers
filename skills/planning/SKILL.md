---
name: planning
description: "Use when deciding how to build or decompose a multi-step feature, exploring high-stakes open-ended implementation alternatives, or executing an approved plan with behaviour-first tests. Trigger on implementation plans, architecture trade-offs, brainstorm, divergent ideation, ADHD mode, integrations, unclear ordering, sprint scope, implement approved plan, TDD. Loaded by /plan and /implement. Not for a known single-file fix or diagnosis-only work."
---

# Planning

Classify before designing: reuse the smallest existing solution, state assumptions, and make each
goal observable. Read `references/step-0-inventory.md` only for work beyond a direct edit; use
`references/issue-triage.md` only for a GitHub issue and `references/wayfinding.md` only when open
decisions prevent a task list.

| Tier | Route | Stop when |
|---|---|---|
| L1-L2 | direct, bounded edit | focused proof passes |
| L3 | `references/phase-a-brainstorm.md` light path | design is acknowledged |
| L4+ | Phase A, then `references/phase-b-writing-plans.md` | approved executable plan exists |
| L5+ | Phase C via `references/phase-c-executing-plans.md` | tasks, gates and final review have evidence |

Read only the phase being entered. Phase A owns design/spec; B owns task grammar, ownership and
plan gates; C owns leases, writer waves, critics and close. A current approval covers its stated
transition; pause again only for a new decision, authority, or material scope change.
`references/loop-engineering.md` is for a loop that needs a cap or reset, and `references/dispatch-matrix.md`
and `references/layer-map.md` are for Phase B assignments/order.

`/gauntlet` is opt-in, never default: at L3+ it accepts either an objective or an approved plan. An
objective enters Step 0 → Phase A → Phase B first; only a validated eligible plan loads
`references/gauntlet-loop.md`. Preserve its leases, independent critic, configured caps and evidence.
For a task marked `TDD: required`, read `references/execution/tdd-policy.md`; load the other
execution prompts only for their dispatch/review event.

Do not code before the applicable gate. Stop and surface a missing binary goal, unresolved blocker,
correction-cap exhaustion, unsafe parallel ownership, or unapproved destructive/Git action. Keep
reviewable working-tree changes; commit, push, merge and staging each need action/scope authorization,
including valid approval already given in the session.

Shared routing, paths, parallel limits and verification remain in
`${CLAUDE_PLUGIN_ROOT}/references/shared/`. Subagent context and return shape are in
`../senior-prompt-engineer/references/agent-handoff-contracts.md`.
