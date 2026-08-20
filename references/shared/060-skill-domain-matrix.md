## Section 6: Skill-to-Domain Matrix

Single source of truth — used by `/implement`, `/design`, `/verify`, `/debug audit`.

| Domain / task signal | Primary skill | Supporting skills |
|---|---|---|
| Bug fix / runtime error / regression | `debugger` | `second-opinion` when a fix keeps not sticking |
| Plan / decompose / architecture decision | `planning` (via `/plan`) | `senior-architect`, `senior-prompt-engineer` when the feature is an LLM feature |
| Delegation / who runs what | `agent-orchestration` | — |
| UI / component / page / design system | the project's design rule, plus the external `impeccable` plugin | `uxmaster` for the direction, `debugger` if mid-fix |
| UX direction / conversion / onboarding | `uxmaster` | — |
| Performance / SEO / security baseline / Core Web Vitals / bundle | `performance-optimization` | `librarian` for external tool docs |
| Browser verification / E2E evidence | `webapp-testing` | `verification` agent |
| Astro project surfaces | `astro` (when `project.stack` names Astro) | — |
| Database, provider or deploy specifics | the project's own skill, when it has one | `librarian` for external docs |
| Skill creation / iteration | `skill-creator` | — |
| Harness wiring audit | `harness-audit` | `skill-improver` agent |
| Prompt engineering / LLM apps / RAG | `senior-prompt-engineer` | — |

If domain isn't listed → no skill applies; use rules + tool docs directly.
