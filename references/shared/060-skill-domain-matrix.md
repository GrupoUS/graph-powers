## Section 6: Skill-to-Domain Matrix

Single source of truth — used by `/implement`, `/design`, `/verify`, `/debug audit`.

| Domain / task signal | Primary skill | Supporting skills |
|---|---|---|
| Bug fix / runtime error / regression | `graph-powers:debugger` | `second-opinion` when a fix keeps not sticking |
| Plan / decompose / architecture decision | `planning` (via `/plan`) | `senior-architect`, `senior-prompt-engineer` when the feature is an LLM feature |
| Delegation / who runs what | none — `references/execution-floor.md` is always in force, §4 carries the contract | — |
| UI / component / page / design system | the project's design rule, plus the external `impeccable` plugin | `uxmaster` for the direction, `graph-powers:debugger` if mid-fix |
| UX direction / conversion / onboarding | `uxmaster` | — |
| Performance / SEO / security baseline / Core Web Vitals / bundle | `performance-optimization` | `graph-powers:librarian` for external tool docs |
| Browser verification / E2E evidence | `webapp-testing` | `graph-powers:verification` agent |
| JS/TS type-check, unit tests, inferred gates | `bun-verify` | `/verify`; never Node `tsc` |
| Astro project surfaces | `astro` (when `project.stack` names Astro) | `bun-verify` for JS/TS gates |
| Database, provider or deploy specifics | the project's own skill, when it has one | `graph-powers:librarian` for external docs |
| Skill authoring, iteration or harness wiring audit | `skill-improve` | `graph-powers:skill-improver` agent |
| Prompt engineering / LLM apps / RAG | `senior-prompt-engineer` | — |

If domain isn't listed → no skill applies; use rules + tool docs directly.
