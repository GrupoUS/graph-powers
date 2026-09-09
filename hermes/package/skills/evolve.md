---
description: "Capture a session learning so the next one inherits it. Modes: default capture, auto for the AutoResearch Loop, handoff for session state. Do not store a personal preference in repository rules."
workflow_type: prompt-chaining
---

> Hermes: first load `skill_view("graph-powers:graph-engineering")` for native calls and host-policy limits. `content/` paths are `file_path` values relative to the common registered-document parent. Source tools/model frontmatter is not host enforcement.

# /evolve

**ARGUMENTS:** the user-provided arguments.

| Token | Action |
|---|---|
| none | capture §§ 1–4 |
| `auto [skill]` only | read and run `content/references/shared/100-autoresearch-loop.md`; target named skill or all with `content/skills/<selected-skill>/evals/evals.json` |
| `handoff` | write § 4 session state |

## 1. Capture

Read `.graph-powers/config.json`, apply the method bootstrap, then append one non-duplicate dated entry to `.graph-powers/logs/learnings.md`: task, symptom, cause, solution, touched files, and actual validation. Keep evidence concrete.

## 2. Destination

Use `content/references/shared/060-skill-domain-matrix.md` and modified paths to find project-owned writable skills; project rules override generic mapping. A skill body/description/reference/eval change loads `skill_view("graph-powers:skill-improve")` first; a simple log/reference entry does not. Ask when several writable destinations are materially plausible. Add the smallest stability rule, anti-pattern, known case, or quick-reference row; never write a global plugin skill from project learning.

When the learning is a reusable project rule, propose a diff for the nearest applicable `AGENTS.md` and request explicit approval before changing it. If no suitable node exists or it exceeds its budget, load `skill_view("graph-powers:intent-layer")` to prepare that proposal. Do not automatically alter project instructions or configuration.

## 3. Summary

Return log path, edited project-owned skills/AGENTS files, and actual gates. Say `Skills: none (global plugin unchanged)` when applicable.

## 4. `handoff`

Update `.graph-powers/HANDOFF.md`, preserving sections, with:

- Objective, completed/pending work, critical restrictions and open questions.
- Approved action/scope and user-message or approval-artifact provenance; decisions/reasons and rejected attempts.
- Project/worktree, branch/HEAD, relevant staged/unstaged/new/removed files; source/config/consumer digests.
- Gates: exact command, result/exit, evidence and tested snapshot (files/config/dependencies/environment), validity/invalidators. Reusable discovery includes provider/scope and decisive sources.
- Exactly one bounded next action and its prerequisites.

The session entry links the active plan/checkpoint; plan-local `HANDOFF.md` links its plan/sprint,
snapshots and existing ledgers without copying them or resetting counters. Handoffs record authority,
grant none and activate no opt-in. On resume, verify scope/provenance and current state; reuse valid
evidence, recheck invalidated dependents. HEAD alone is insufficient; compaction alone invalidates
nothing. No second memory or automatic per-turn learning entry.
