# Phase A — Brainstorm

> Sequential guide for the first phase of the planning chain.
> **Direct-invokes `superpowers:brainstorming` as the engine** and wraps it with harness deltas. Honors the tier gating in this skill (`SKILL.md § Step 0`).
> Consolidates the former Phase 0 framing + discovery-protocol references into this single Phase A guide.

---

## HARD GATE

<EXTREMELY-IMPORTANT>
Do NOT invoke any implementation skill, write any code, or scaffold anything until you have presented a design and the user has approved it.
</EXTREMELY-IMPORTANT>

Tier-gated: L1-L2 skip the gate entirely (autonomy rule authorizes direct edit); L3+ never skip. For L4+ the gate begins at **Phase 0 framing**, not at the implementation step — *"too simple to need a design"* is itself a red flag at L4+ (unexamined assumptions cost the most rework on "simple" work).

**Anti-hallucination:** never speculate about code you haven't read; read files before asserting; if unknown → research or mark a `[Knowledge Gap]`.

---

## Entry contract

- Main agent has classified the task as **L3+** (per `.claude/CLAUDE.md § Intent classification`).
- `Skill("planning")` is loaded.
- Branch is `${git.workBranch}`. If not, return to it before any action.

## Exit contract

- **L3:** inline 3-section spec (architecture / data / validation) printed in chat. No file. Skip to direct edit.
- **L4+:** spec file at `${paths.planDir}/specs/YYYY-MM-DD-<topic>-design.md` in the working tree. GATE 1 (project-planner) PASS. User approved. Proceed to `phase-b-writing-plans.md`.

---

## Loop contract

> Phase A is a goal-gated loop. Model: `references/loop-engineering.md`.

- **trigger:** task classified L3+ on `${git.workBranch}`.
- **goal (binary):** spec file exists **AND** GATE 1 `graph-powers:project-planner` = PASS **AND** user approved **AND** zero TBD/placeholder tokens **AND** every `[ASSUMED]` labeled. *(L3: inline 3-section spec acknowledged by user — no file, no GATE 1.)*
- **body:** `superpowers:brainstorming` generates the spec → `graph-powers:project-planner` evaluates (Step 8) → revise inline.
- **guards:** HARD-STOP 3 spec revisions → escalate · GOAL-GUARD: if Phase 0 question (a) names no observable state change, do not plan · devil's-advocate question at L6+.
- **terminal:** goal PASS → Phase B. Any guard trips → escalate to user.

---

## Engine — invoke `superpowers:brainstorming`

For every L4+ entry (and L3 in light form), **invoke `Skill("superpowers:brainstorming")`** and let it drive the core loop. Do NOT reimplement its steps — the engine owns them:

| The engine owns | the harness wraps (the deltas below) |
|---|---|
| explore project context · clarifying questions one-at-a-time · 2-3 approaches w/ recommendation · design sections w/ inline approval · write spec to `${paths.planDir}/specs/` · spec self-review · user review gate · terminal "invoke writing-plans" | Phase 0 framing + 5-10→3 divergence (below) · parallel `graph-powers:explorer`+`graph-powers:librarian` dispatch (Step 1) · `AskUserQuestion` UI (Step 2) · `layer-map.md` cross-check (Step 3) · GATE 1 `graph-powers:project-planner` after self-review (Step 8) · branch policy · tier-gated entry · intercept terminal → Phase B |

The engine's HARD-GATE ("every project gets a design") is overridden by the tier gating in this skill: L1-L2 skip the engine entirely; L3 runs the light path; L4+ runs the full engine + all deltas. The numbered steps below are the **harness deltas in execution order** — interleave them with the engine.

---

## Phase 0 — Framing (L4+, runs BEFORE Step 1)

> Pre-decision framing: is this the right problem, is it one project, what are the real options?
> | Tier | Phase 0 | What runs |
> |---|---|---|
> | **L1-L2** | SKIP | direct edit |
> | **L3** | LIGHT | question (a) + scope-decomp check, ~30s, no file |
> | **L4-L5** | MANDATORY-LITE | full 0.1 + 0.2 + 0.3; 0.4 optional |
> | **L6+** | MANDATORY-FULL | all four sub-steps incl. 0.4 devil's-advocate |

### 0.1 — Problem framing ("is this the right problem?")
Three pinned questions, asked **ONE AT A TIME**. At L3, ask only (a).

- **(a)** What observable user/system state changes when this is done? → if the user can't name a state change, the task is unframed. STOP.
- **(b)** What's the cheapest experiment that would invalidate the framing? → reveals testable assumptions.
- **(c)** Who, if anyone, is harmed if we DON'T do this? → surfaces urgency vs. preference; if nobody → defer/cancel candidate.

### 0.2 — Scope decomposition pre-check
**Heuristic:** if you can name **≥ 3 distinct deliverables** shipping to different users or layers, decompose **first**, plan **second**. ≥ 3 children confirmed by user → **STOP planning**, suggest per-child planning invocations. Do not proceed.

### 0.3 — Divergent ideation (L4+ only)
Generate **≥ 5 candidate approaches** with no filtering. MUST include **≥ 1** of: no-code workflow · cancel/postpone · buy-vs-build (third-party SaaS) · reuse/extend an existing internal solution (LEVER) · "contrarian" inverted approach. Then **narrow to top 3** with a one-line trade-off each. These 3 feed Step 4 — do NOT regenerate options there. Jumping straight to "the obvious 2-3" locks in the framing the user arrived with (#1 cause of bad designs).

### 0.4 — Devil's advocate / inversion (L6+ required, L4-L5 optional)
For the top-ranked option, write a paragraph titled exactly **"Why this approach is WRONG"** answering: (a) what assumption, if false, kills it? (b) what does the inverse look like? (c) what would a hostile reviewer attack first? Steel-man the opposite, not your pick.

**Output artifact (L4+):** embed this block at the TOP of the spec doc (Step 6):

```markdown
## Problem
[one paragraph from 0.1 (a)(b)(c)]
## Considered (5-10)
[full list from 0.3]
## Chosen (3)
1. [top option] — [trade-off one-liner]   2. …   3. …
## Recommendation
[lead with one of the 3, justify in ≤ 3 sentences]
## Inversion (L6+ required)
**Why this approach is WRONG:** [paragraph from 0.4]
```

**L3:** 2-3 sentences inline in chat, no file.

---

## Step 1 — Parallel research dispatch (single message, ALWAYS)

For every L3+ Phase A entry, fire two background agents in ONE assistant message:

```ts
Agent({
  subagent_type: "graph-powers:explorer",
  run_in_background: true,
  prompt: "Codebase pattern scan for {{task topic}}. Return: existing files matching the domain, current patterns + conventions, hot files (recent commits), reusable functions/utilities, layer boundaries touched. Surface anything contradicting the user's framing. Cap output 1500 tokens.",
})
Agent({
  subagent_type: "graph-powers:librarian",
  run_in_background: true,
  prompt: "External docs + CVE scan for {{task topic}} on {{stack: ${project.stack}}}. Return: current best practice (version + year), recent breaking changes, integration pitfalls, security advisories. Context7 for API truth; `mcp__tavily__tavily_research` (model: auto) for the deep best-practice pass. Cap output 1500 tokens.",
})
```

While agents work, main agent: reads `references/layer-map.md` to confirm touched layers · reads recent commits + modified files (`git status`, `git log -n 10`) · drafts clarifying-question candidates.

## Step 2 — Clarifying questions

Use `AskUserQuestion`. **One topic per question.** Prefer 2-4 multiple-choice options. Cover: **Purpose** (business/user outcome) · **Constraints** (deadlines, surfaces, must-keep-working) · **Success criteria** (observable "done") · **Reuse vs new** (which existing pattern/file to extend) · **Scope edges** (explicit non-goals).

**Skip questions the user already answered** — re-asking burns trust. **L6+ extra:** add a devil's-advocate question (per § Phase 0 — 0.4).

## Step 3 — Consolidate research findings

When both background agents return: read each summary (< 2000 tokens combined) · cross-reference `references/layer-map.md` ordering · flag contradictions between user framing and findings (if blocking → surface as a clarifying question) · label assumptions `[ASSUMED]` for the spec · **if findings span >2 technical areas with contradictions** → `mcp__sequential-thinking__sequentialthinking` to map the dependency graph **before** Step 4 (L4+ MUST · L3 SHOULD).

## Step 4 — Propose 2-3 approaches

> Engine-owned. Harness delta: use the option format below; the 3 options come from Phase 0's narrowed set — never start ideation here.

Lead with the **recommended** option:

```
**Option N — <name>**
- Approach: <one-sentence summary>
- Pros / Cons: <2-3 bullets each>
- Project risks: <ORM pitfall, platform-specific runtime bug, split deploy target, session handling, etc.>
- Layer chain: <which layers touched, in order>
```

Get user pick.

## Step 5 — Present design in sections

> Engine-owned. Harness delta: error handling mandatory at L4+, inversion paragraph at L6+. Incremental validation — ~200-300 words/section, ask "Section reads correct?" after each, rewind on pushback.

Sections (scaled to complexity): **Architecture** (modules, boundaries, data flow) · **Components** (files + responsibilities, paths inline) · **Data flow** (request/event traversal) · **Error handling** (failure modes + recovery, mandatory L4+) · **Testing** (existing coverage, what to add, mock vs real) · **L6+ inversion paragraph** ("Why this approach is WRONG", per `phase-b-writing-plans.md § Risk — pre-mortem + ADR`).

## Step 6 — Write spec doc

> Engine writes the working-tree artifact. Harness delta: the richer template below.

**Path:** `${paths.planDir}/specs/YYYY-MM-DD-<kebab-case-topic>-design.md` (today's ISO date, UTC).

```markdown
# <Title> — Design spec

## Context              — why this work (problem/constraint/deadline) + outcome (observable state)
## Background research  — internal (explorer) + external (librarian) findings + contradictions resolved
## Approach (chosen)    — one-paragraph summary + why over alternatives
## Architecture         — modules + boundaries + full file paths (layer-labeled)
## Data flow            — request/event traversal + state transitions
## Error handling       — failure modes + recovery paths
## Testing              — existing coverage + new test plan
## Assumptions          — [ASSUMED] every inferred constraint
## Out of scope         — explicit non-goals
## Open questions       — anything unresolved at spec time
## References           — spec lineage (related specs, ADRs, prior plans)
```

> L4+ embeds the Phase 0 framing block (§ 0.3 output artifact) at the top.

Run the relevant Markdown/config checks, but do not stage or commit the spec
without explicit current-turn user approval.

## Step 7 — Spec self-review

Scan before GATE 1: no "TBD"/"TODO"/placeholder/"similar to N" · no internal contradictions (architecture ↔ data flow ↔ testing) · scope tight (one project, not three masquerading — if three, **stop, decompose, brainstorm only the first**) · no ambiguity (any requirement readable two ways → pick one) · every `[ASSUMED]` labeled. Fix inline.

## Step 8 — GATE 1 — project-planner review (L4+ mandatory)

```ts
Agent({
  subagent_type: "graph-powers:project-planner",
  prompt: "Plan Review mode. Review spec at <path>. Verify: scope tight, layer ordering valid, missing risks, user-intent alignment, no contradictions, no scope creep. Return: PASS / FAIL+specifics / BLOCKED. < 2000 tokens.",
})
```

**PASS** → Step 9. **FAIL** → revise inline addressing each specific, re-invoke (loop body); **HARD-STOP at 3 iterations** → escalate. **BLOCKED** → surface to user, do not retry.

## Step 9 — User approval

> "Spec written to `${paths.planDir}/specs/<file>` and project-planner returned PASS. Approve to proceed to Phase B (writing-plans)?"

Wait for explicit "yes"/"approve"/"go". On change request → revise + re-loop self-review + Step 8.

## Step 10 — Transition

```
"Phase A complete. Spec at <path>. Invoking Phase B (writing-plans)."
```
Read `phase-b-writing-plans.md` next.

---

## L3 light path (truncated flow)

For L3 explicit tasks: (1) brief codebase grep, no parallel agents · (2) one clarifying question if ambiguous · (3) inline 3-section spec in chat (`**Architecture:** … **Data shape:** … **Validation:** <command>`) · (4) user nod · (5) direct edit, skip Phase B + C. No file, no GATE 1.

## L6+ extra

Devil's advocate at Step 2 · inversion paragraph at Step 5 · pre-mortem block in spec + ADR if architecture is novel (per `phase-b-writing-plans.md § Risk — pre-mortem + ADR`).

---

## Stopping conditions

| Condition | Action |
|---|---|
| Phase 0 (a): user answers "I don't know what problem this solves" | STOP, escalate, do not plan |
| Phase 0.2 produces ≥ 3 child tasks confirmed by user | STOP planning, suggest per-child invocations |
| User rejects 3 design proposals | Stop, ask for explicit constraints, do not auto-iterate |
| project-planner FAIL 3× on same spec | Escalate; spec likely has fundamental ambiguity |
| Background agents both return BLOCKED | Halt Phase A, surface, do not invent design from nothing |
| Scope keeps expanding | Stop, decompose into sub-projects, brainstorm only first |
