## Section 4.5: Context staging, per domain

The staged loads `/prime` performs once it knows which domain the task is in. `040-wisc-context-load.md`
says which tier; this says how far into it to go, and when to stop.

Read only the section for the mode that was dispatched. Reading all three is the failure this file
exists to prevent.

### 4.5a — Backend

**Stage 0, base.** List `${rulesDir}/` and read only the rules whose `paths:` match the backend and
data roots — typically the project's backend, data and stability rules. **Read what is there, not a
fixed list:** naming a rule file the project never wrote produces a silent miss, not an error.

```bash
git log --oneline -5 -- ${paths.backendRoot}
git log --oneline -5 -- ${paths.schemaRoot}
```

No deep references and no subdirectory `AGENTS.md` yet.

**Stage 1, classify the task shape.**

| Task shape | Examples | Stage 2 load |
|---|---|---|
| API / handler | route, validator, auth guard, response shape | `${paths.backendRoot}/AGENTS.md` if present |
| Schema / data | columns, relations, indexes, enum alignment | `${paths.schemaRoot}/AGENTS.md` if present, plus the project's schema reference if it has one |
| Service / integration | webhooks, external APIs, third-party providers | the project's integration rule if it has one; provider docs through `graph-powers:librarian` |
| Runtime / env | env vars, deploy config, runtime behaviour | the project's architecture notes if any, otherwise `Skill("senior-architect")` |
| Historical bug pattern | tenant resolution, aggregation, date boundary | the project's backend-learnings document if it keeps one |
| Multi-domain | API + schema + integration | only the exact combination required |

Unclear task shape: ask one short question rather than load more.

**Stage 2, targeted.** Only the files Stage 1 justified. If the project keeps a routing supplement in
`${rulesDir}/`, consult it for the bindings this plugin cannot know — where a flow lives, which
provider handles what.

**Loading rules.** Never all backend references by default. Never a subdirectory `AGENTS.md` unless
the task touches that directory. Stop at the minimum sufficient load; expand in stages rather than
restarting with a full preload. Past four files in one stage, the classification is wrong.

### 4.5b — Frontend

**Stage 1, baseline, always.** The project's design rule from `${rulesDir}/`, then the nearest
`AGENTS.md` under `${paths.frontendRoot}`.

```bash
git log --oneline -5 -- ${paths.frontendRoot}
```

Stage 1 alone covers small UI fixes, class changes, simple component edits, and bug fixes with a
known pattern.

**Stage 2, design foundation.** Escalate for new UI, layout redesign, page structure, colour and
typography decisions, design review, design-system alignment, interaction design. Load the project's
design canon — root `DESIGN.md` or its equivalent — and its extend-versus-create philosophy document
if it keeps one.

**Stage 3, historical patterns.** Escalate for re-render and performance regressions, polling or
query churn, virtualised lists, drag-and-drop, mutation UX, sanitisation and HTML rendering, media
flows, scroll bugs in tabs and panels. Load the project's frontend-learnings document if it has one.

**Stage 4, canonical authority.** Only when editing under `${paths.frontendRoot}/**`, when the
compact rules are not enough, when a compact rule and the domain authority disagree, or when the
change spans several frontend subsystems.

**Feature-specific.** For one surface — a dashboard, a form, a checkout flow — load `${rulesDir}/design.md`
for tokens and constraints, and **only** the references it names for that surface.

| Task shape | Stages |
|---|---|
| Trivial L1-L2 | 1 |
| Explicit frontend implementation | 1, then 2 if structure or design is involved |
| Performance or debugging | 1, then 3 |
| New page or component architecture | 1, 2, 4 |
| Complex refactor | 1, then 2 or 3, then 4 as needed |

### 4.5c — Fullstack

**Always:** `${rulesDir}/stability.md`, plus the Tier 2 rules whose `paths:` match the domains in
scope — one per domain the task actually touches, never the whole directory. API plus UI is two
rules; schema plus API plus UI is three. If a domain in scope has no rule, **say so**: a missing rule
is a finding about the project, not a silent pass.

**Tier 3, only what is justified:** the architecture map when planning cross-domain work, the design
foundation when UI design is in scope, one targeted feature spec — never a whole specs folder.

**Stop** when the task has not been given yet (confirm the baseline and say you are ready), when the
minimum sufficient load is reached, or the moment the work turns schema-changing, auth-changing or
payment-related — that is flagged before implementation, not after.
