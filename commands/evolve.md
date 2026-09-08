---
description: "Capture a session learning so the next one inherits it. Modes: default capture, auto for the AutoResearch Loop, handoff for session state. Do not store a personal preference in repository rules."
workflow_type: prompt-chaining
---

# /evolve

**ARGUMENTS:** $ARGUMENTS.

| Token | Action |
|---|---|
| none | capture §§ 1–4 |
| `auto [skill]` only | read and run `${CLAUDE_PLUGIN_ROOT}/references/shared/100-autoresearch-loop.md`; target named skill or all with `evals/evals.json` |
| `handoff` | write § 4 session state |

## 1. Capture

Read `.graph-powers/config.json`, apply the method bootstrap, then append one non-duplicate dated entry to `.graph-powers/logs/learnings.md`: task, symptom, cause, solution, touched files, and actual validation. Keep evidence concrete.

## 2. Destination

Use `060-skill-domain-matrix.md` and modified paths to find project-owned writable skills; project rules override generic mapping. A skill body/description/reference/eval change loads `Skill("skill-improve")` first; a simple log/reference entry does not. Ask when several writable destinations are materially plausible. Add the smallest stability rule, anti-pattern, known case, or quick-reference row; never write a global plugin skill from project learning.

Update the nearest applicable `AGENTS.md` only when the learning is a reusable project rule. If no suitable node exists or it exceeds its budget, load `Skill("graph-powers:intent-layer")` before adding a node. Otherwise append problem, cause and solution; do not duplicate guidance.

## 3. Summary

Return log path, edited project-owned skills/AGENTS files, and actual gates. Say `Skills: none (global plugin unchanged)` when applicable.

## 4. `handoff`

Overwrite `.graph-powers/HANDOFF.md` with: where work stopped; one next action; attempts not to repeat; open questions; branch/working-tree state; last real gates; touched files. It must be sufficient for `/prime` to resume without rediscovery.
