# Step 0 — destination, reuse-first inventory, blast radius

> Canonical Step 0 for `Skill("graph-powers:planning")`. Read it end to end at L3+. At L1-L2 use only 0.0, two
> targeted searches from 0.2, and one consumer search from 0.4, then state the reuse verdict inline.
> Research only — no design, code or file writes.

## Why this runs before anything is designed

Two failure modes, symmetric, and this step is the answer to both.

**Build new → break working.** A need already met by existing code must never grow a second
implementation, and you cannot map what a change breaks until you know what already exists. That is
0.2 through 0.5.

**Plan detail nobody can defend.** A task list written on top of an unmade decision is invented
detail, and it fails verification later for a reason verification cannot name. That is 0.0, 0.1 and
0.6.

The destination comes first because scope is what decides which of the two halves a finding belongs
to — and because a need you cannot yet phrase is fog to be declared, not a task to be invented.

## 0.0 The destination, and the three buckets

Name what **reaching the end of this effort looks like**: the spec handed off, the decision locked,
the change made in place. One or two lines, stated as an observable condition ("done when `X` is
true"), never as a direction ("improve X") — a destination that is not observable cannot close a loop
(`loop-engineering.md` GOAL-GUARD), and it is what fixes the scope of every step below.

The destination splits the request into three buckets, and they stay separate to the end:

| Bucket | What lands here | Where it lives |
|---|---|---|
| **In scope** | needs you can state now → `N1..Nn` | the reuse ledger, then the plan's tasks |
| **Out of scope** | work consciously ruled *past* the destination | `## Out of scope` — with the trigger that would reopen it |
| **Not yet specified** | in-scope questions you cannot yet phrase sharply | `## Not yet specified` — graduates into a task when it sharpens |

**Chart the way, do not charge the destination.** `/plan` produces decisions; `/implement` produces
deliverables. The urge to start editing while still charting means you already reached the edge of
what needs planning — hand off, do not keep planning. Doctrine, the fog test, decision types and map
mode: `wayfinding.md`.

## 0.1 Decompose the ask into needs

Restate the request as atomic needs `N1..Nn`, one capability per row, **before** searching. Searching
for "the feature" finds nothing; searching for "file upload with a per-tenant quota" finds the
service that already does it.

**A need you cannot phrase precisely is not a row — it is fog.** The test is whether you can state
the *question* now, not whether you can answer it. Sharp question → row, even if blocked. Not
phrasable → one loose line under `## Not yet specified`, never a row carrying `TBD`. Do not pre-slice
fog into need-sized pieces.

## 0.2 Search order — stop at the first hit

Preferred instrument is the code graph: contract, install state and `[HARD]` limits in
`${CLAUDE_PLUGIN_ROOT}/references/shared/115-code-graph.md`. It answers "does this already exist?"
structurally, in one command, instead of a grep sweep over every string match. Unavailable is
SKIPPED, never blocking — the grep order below is the fallback, slower and noisier but not wrong.

Then confirm each candidate by reading it. The graph tells you *where*, never *whether it fits*.

Fallback and confirmation order:

1. The nearest `AGENTS.md` of the target subtree (`${paths.backendRoot}`, `${paths.frontendRoot}`,
   and any shared package root) — they map what already exists.
2. The project's cross-cutting singletons — logger, database client, providers, middleware.
   **Never re-instantiate one.**
3. Shared packages — types, constants and orchestration used by more than one app.
4. `${paths.componentsRoot}` primitives and existing hooks before any new component.
5. The project's script directory — automation frequently already exists.
6. An existing handler or procedure on the same domain router, before adding a new one.

At **L3+** dispatch this in ONE message, background: `graph-powers:explorer` for the codebase
inventory, plus `graph-powers:librarian` only when an external API or version fact is genuinely in
doubt.

## 0.3 Reuse ledger — mandatory output

| # | Need | Existing asset (`path:line`) | Verdict | Justification (required only for NEW) |
|---|---|---|---|---|
| N1 | … | `<existing-service-file>:42` | REUSE | — |
| N2 | … | `…:88` | EXTEND | new param, no signature break |
| N3 | … | (none found) | NEW | searched `<terms>` in `<paths>`; nearest analog `<path>` does not model `<X>` |

Verdicts: **REUSE** (call it as-is) · **EXTEND** (add to the existing unit, backward-compatible) ·
**NEW**. The default posture is REUSE → EXTEND → NEW, in that order. **A `NEW` row without the "why
extending fails" line is not a plan, it is a preference** — rewrite it or downgrade it.

In issue mode the ledger is evidence: a triage row whose need is already met by an existing asset is
`CUT` or `SIMPLIFY`, with that `path:line` as its evidence line.

## 0.4 Blast radius — what this change can break

Run this for every file or symbol the ledger marks REUSE or EXTEND, i.e. every place existing code
gets touched. The graph widens the consumer set; grep is what closes it.

**Grep with the agent's own `Grep` tool, never a shell `grep`.** The binary does not exist on
Windows, and cmd.exe does not treat `'` as a quote, so `--include='*test*'` is passed through
literally and matches nothing — an empty consumer list that reads as "no consumers", which is exactly
the false negative this step exists to prevent.

- `Grep` the exported symbol scoped to `${paths.backendRoot}` and `${paths.frontendRoot}`, then drop
  the definition file from the results yourself.
- `Grep` it again with `glob: "*test*"`, and again with `glob: "*spec*"`.

The union of graph and grep is the consumer list. A consumer only the graph found is real; one only
grep found is also real. Neither tool alone is the answer — per `115-code-graph.md § Limits` the
graph misses client call paths, route ids, ORM columns and dynamic imports, and under-reports tests.

Map each hit to the runtime surface it lives on:

| Surface | What to record | Why it matters |
|---|---|---|
| **Data** (`${paths.schemaRoot}`) | tables and columns read or written; a column dropped or narrowed; a new schema file that must be registered with the ORM; uniqueness a conflict clause depends on; every new foreign key that needs an index | A schema that compiles but was never applied fails on the next deploy, not in review — the plan must name who applies it and when. If staging and production share a database, say so here: a "staging" write is a production write |
| **Service / API** (`${paths.backendRoot}`) | handlers, procedures, webhooks, newly required environment variables, and middleware registration order | A new environment variable means the deploy target's configuration changes, and often that the process must be recreated rather than restarted. Misplaced middleware breaks routes the plan never mentions |
| **Client** (`${paths.frontendRoot}`) | routes added or renamed, generated route or type artefacts that are committed build inputs, route guards, components, props, shared types, build-time variables | A build-time variable needs a rebuild, not a redeploy. A stale generated artefact fails in the deployed bundle while every local test passes |
| **UX** | the flows that reach the touched screen — entry points, adjacent views, the smallest supported viewport | Breakage usually lands on the *neighbouring* flow, not the edited one |

> These rows are the shape, not the content. When the project declares its own surfaces in
> `${rulesDir}/`, those replace these — a surface list that does not match the repository is worse
> than none, because it reads as coverage.

## 0.5 Regression watchlist — mandatory output

```markdown
## Regression watchlist
| # | Existing behaviour that must still work after this change | How to prove it | Owner phase |
|---|---|---|---|
| W1 | <flow / procedure / query that exists today> | <test file, route, or probe command> | <plan phase> |
```

One row per consumer found in 0.4 that this change does **not** update. **A row with no proof command
is the plan's first task** — write the characterization test before the change. An empty watchlist is
valid only for a strictly additive change with zero consumers, and it must say so explicitly.

## 0.6 Open decisions — what must be decided before tasks can be written

The inventory answers "what exists". It does not settle a **decision**, and a task list written on
top of an unmade one is invented detail.

| # | Decision (name it; a number alone is illegible) | Type | Mode | Resolver | Blocks |
|---|---|---|---|---|---|
| D1 | … | research | AFK | `graph-powers:explorer` / `graph-powers:librarian`, background | N2, N3 |
| D2 | … | grilling | HITL | `AskUserQuestion`, one topic at a time | N4 |

Types and resolvers are canonical in `wayfinding.md § Decision types`: `research` (AFK), `prototype`
(HITL, a throwaway artifact to react to), `grilling` (HITL, the default), `task` (a manual
prerequisite that unblocks a decision and delivers nothing by itself).

Two rules, both cheap and both violated constantly:

- **AFK first.** Never open a HITL decision that a `Grep`, the code graph or a background explorer
  closes. Research is parallel and free of the user's attention; grilling is the scarcest resource in
  the chain.
- **HITL floor.** The agent never stands in for the human side. A HITL decision auto-answered to keep
  moving is labeled `[ASSUMED]` **and** surfaced in the same turn. The unlabeled auto-answer is the
  defect, not the answer.

**Fog check.** If ≥3 open decisions block the writing of the task list itself, or the destination
does not fit in one plan or context (CTX-GUARD ~80K), or resolving any one decision would invalidate
most of the tasks you would write today → this is **map mode**, not a plan (`wayfinding.md § Map
mode`). Below all three thresholds, resolve the decisions and keep going.

## 0.7 Baseline + rollback

- Record the green baseline in the plan: gate status, test counts, and — when the change reaches a
  deployed surface — the health probe. Use
  `python -X utf8 -c "import urllib.request,sys;print(urllib.request.urlopen(sys.argv[1],timeout=10).status)" <url>`,
  not `curl`: in PowerShell `curl` is an alias of `Invoke-WebRequest`, which rejects `-s`. GET only.
- Every plan carries `## Rollback`: how to undo each phase — revert the commit, turn the flag off,
  leave the column in place. Schema work is forward-only unless the rollback is written down.

## 0.8 Two contract rules that keep a plan loadable

- **`## Not yet specified` may be empty, but then say so** — "no fog: the path to the destination is
  closed". An absent section and a closed path are different claims. A `TBD` inside a task is still a
  defect; the fog section is where an honest unknown goes instead.
- **Index, not store.** A decision lives in exactly one artifact — the spec, an ADR, or the task
  itself. Everywhere else gists it in one line and links, referring to it **by name**: `#4 / T2.3`
  alone is illegible.
