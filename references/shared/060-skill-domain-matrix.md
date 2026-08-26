## Section 6: Skill-to-Domain Matrix

Single source of truth — used by `/implement`, `/design`, `/verify`, `/debug audit` and `/evolve`.

| Domain / task signal | Primary skill | Supporting skills |
|---|---|---|
| Bug fix / runtime error / regression | `graph-powers:debugger` | `graph-powers:evaluator` Mode 5, the blind second opinion, when a fix keeps not sticking |
| Plan / decompose / architecture decision | `planning` (via `/plan`) | `senior-architect`, `senior-prompt-engineer` when the feature is an LLM feature |
| Delegation / who runs what | none — `references/execution-floor.md` is always in force, §4 carries the contract | — |
| Existing implemented UI / production-readiness repair / design fix | `design-fix` (via `/design fix`) | `designer` only when the repair is structural; `uxmaster` for behavioral criteria |
| UI / component / page / design system | `designer` — the direction, then the craft passes in `${CLAUDE_PLUGIN_ROOT}/skills/designer/references/craft-passes.md` — with the project's design rule | `uxmaster` for conversion, `animate` for motion, `graph-powers:debugger` if mid-fix |
| Visual direction / look and feel / generic, template-like or AI-looking UI | `designer` (via `/design`) | `animate` for the motion inside the direction |
| Motion, animation, gesture | `animate` | `graph-powers:mobile-developer` for React Native |
| UX direction / conversion / onboarding | `uxmaster` | `landing-page-design` on a landing or marketing page, including its Astro implementation floor |
| Performance / SEO / security baseline / Core Web Vitals / bundle | `performance-optimization` | `graph-powers:librarian` for external tool docs |
| Browser verification / E2E evidence | `webapp-testing` | `graph-powers:verification` agent |
| JS/TS type-check, unit tests, inferred gates | `graph-powers:debugger` § JS/TS gate resolver | `/verify` reads `130-bun-tsgo-gates.md` directly; never Node `tsc` |
| Database, provider or deploy specifics | the project's own skill, when it has one | `graph-powers:librarian` for external docs |
| AGENTS.md hierarchy — the root node and the child nodes a subtree earns; agents misreading where things live | `graph-powers:intent-layer` | `AGENT_SETUP.md § 4b` at install, `/evolve § 5` afterwards; `/prime` only reads the nodes |
| Skill authoring, iteration or harness wiring audit | `skill-improve` | `graph-powers:skill-improver` agent |
| Prompt engineering / LLM apps / RAG | `senior-prompt-engineer` | — |

If domain isn't listed → no skill applies; use rules + tool docs directly.

### Write ownership

Selecting a skill chooses a method. It never grants permission to edit the files that implement
that method.

Before a flow writes a `SKILL.md`, `references/` entry or skill-owned learning file, resolve the
canonical current-project root, `${CLAUDE_PLUGIN_ROOT}`, the source `SKILL.md` and every proposed
destination. A skill is writable only when source and destination are contained by the current
project root and neither resolves through a symlink outside it. Use canonical path containment,
never a string-prefix comparison. If the plugin root differs from the current-project root, files
inside the plugin root are installed harness files and stay read-only even when that installation
is nested inside the project. The Graph Powers source checkout is the deliberate exception: when
the two canonical roots are the same directory, its own skill files are project-owned.

An unresolved path, a missing project root, a cache/global skill or a mixed set fails closed for
the unsafe destinations. Keep the selected skill as methodology, update only project-owned skills,
and put the durable host learning in the project's log and `AGENTS.md`. Report skipped global
methods as `none (global plugin unchanged)` rather than silently mutating the shared installation.
