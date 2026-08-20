## Section 4: WISC Context Load

Before any task, load the right tier:

| Domain | Command | Loads |
|---|---|---|
| Frontend | `/prime frontend` | The project's design rule + the nearest `AGENTS.md` under `${paths.frontendRoot}` + only the references they name |
| Backend / API / data | `/prime backend` | The project's backend, data and stability rules from `${rulesDir}/` + targeted references |
| Full-stack / multi-domain | `/prime` (auto) or `/prime fullstack` | Intent-based Tier 2 + exact Tier 3 only when justified |
| Continuing prior session | Read `.graph-powers/HANDOFF.md` first | — |

**Tier 3 (read on demand only):**
- `Skill("senior-architect")` — runtime and environment shape, architecture decisions, trade-off analysis
- `Skill("uxmaster")` — UX judgement: conversion, onboarding, hierarchy, retention
- `${rulesDir}/` — the project's own rules and references, including anything it keeps outside skills
