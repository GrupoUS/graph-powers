# {{PROJECT_NAME}}

> Graph Powers template. Replace the `{{PLACEHOLDERS}}`, delete what does not apply, and remove this
> line. **Target: under 150 lines.** Above that adherence drops — and what is left over is usually
> generic process the plugin already provides.

## Identity

| | |
|---|---|
| Stack | {{STACK}} |
| Language | {{LOCALE}} |
| Work branch | {{WORK_BRANCH}} |
| Flow | branch → PR → approval → merge |
| Environments | {{ENVIRONMENTS}} |

Operational parameters — commands, paths, opt-in prefix — live in `.graph-powers/config.json`,
validated by the plugin's `schema/config.schema.json`. This file does not repeat them.

## What comes from the plugin

The process is Graph Powers': planning, debugging, verification, review, delegation, and the git and
execution guardrails. **Do not re-document any of it here.** If you felt like writing down how to
plan a feature in this file, that text already exists in the plugin, and the two copies will
diverge.

What this file carries is what only holds here.

## This project's invariants `[HARD]`

Five to twelve lines, at most. Each one exists because a violation already cost something — if you
cannot name the cost, it is not an invariant, it is a preference.

{{CARDINAL_RULES}}

## Path routing

When work touches these paths, load these rules before editing:

| Path | Load | Implement in |
|---|---|---|
{{ROUTING_TABLE}}

## Decision authority

| Situation | Who decides |
|---|---|
| Local, reversible change within an existing pattern | The agent decides and reports |
| New dependency, new pattern, broad refactor | Confirm first |
| Schema, migration, authentication, payment, personal data | Always ask |
| Anything visible outside the repository — commit, push, PR, deploy, send | Always ask |

{{DECISION_EXCEPTIONS}}

## Pointers

| Subject | Where |
|---|---|
| Domain rules | `.claude/rules/` |
| Parameters | `.graph-powers/config.json` |
| Identity and invariants | `AGENTS.md` at the root |
{{PROJECT_POINTERS}}

## Context hygiene

Work in progress lives in `.graph-powers/HANDOFF.md`, written by `/evolve handoff` and ignored by
git. **Read it first** when a session resumes work already under way, and update it before any
context reset.

Compacting preserves continuity; only a handoff gives a clean screen without losing the thread.
