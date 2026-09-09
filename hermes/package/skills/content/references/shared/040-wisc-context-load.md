> Hermes auxiliary: `content/` paths are `file_path` values relative to the registered-document parent. Apply the loaded graph-engineering mapping and host policy; this file is served without template expansion.

## Section 4: WISC Context Load

Before any task, load the right tier:

| Domain | Command | Loads |
|---|---|---|
| Frontend | `/prime frontend` | The project's design rule + the nearest `AGENTS.md` under `${paths.frontendRoot}` + only the references they name |
| Backend / API / data | `/prime backend` | The project's backend, data and stability rules from `${rulesDir}/` + targeted references |
| Full-stack / multi-domain | `/prime` (auto) or `/prime fullstack` | Intent-based Tier 2 + exact Tier 3 only when justified |
| Continuing prior session | Read `.graph-powers/HANDOFF.md` first | — |

The staged loads behind each row — how far into a tier to go and when to stop — are
`content/references/shared/045-context-staging.md`, one section per domain. Read the section for the mode dispatched, not
the file.

**Tier 3 (read on demand only):**
- `skill_view("graph-powers:senior-architect")` — runtime and environment shape, architecture decisions, trade-off analysis
- `skill_view("graph-powers:designer")` — visual direction before code: derive from the subject, refuse the defaults, one signature
- `skill_view("graph-powers:uxmaster")` — UX judgement: conversion, onboarding, hierarchy, retention
- `${rulesDir}/` — the project's own rules and references, including anything it keeps outside skills
