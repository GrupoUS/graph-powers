# Phase A — Brainstorm

> Canonical brainstorming method for the planning chain. Read it at L3+ after Step 0 has fixed the
> destination, reuse ledger and tier. Nothing else re-declares this sequence.

---

## HARD GATE

Do not invoke an implementation skill, write code or scaffold until the design has been presented
and the user has approved it.

Tier-gated: L1-L2 skip the design gate and edit directly; L3+ never skip it. Step 0 already fixed
the destination and tier, so Phase A starts from evidence rather than reopening scope.

**Anti-hallucination:** never speculate about code you haven't read; read files before asserting; if unknown → research or mark a `[Knowledge Gap]`.

---

## Entry contract

- Main agent has classified the task as **L3+** (per `${CLAUDE_PLUGIN_ROOT}/references/shared/020-complexity-routing.md`).
- `Skill("graph-powers:planning")` is loaded.
- Branch is `${git.workBranch}`. If not, return to it before any action.

## Exit contract

- **L3:** inline 3-section spec (architecture / data / validation) printed in chat. No file. Skip to direct edit.
- **L4+:** spec at `${paths.planDir}/YYYY-MM-DD-<slug>/spec.md` in the working tree — one plan is one directory (`${CLAUDE_PLUGIN_ROOT}/references/shared/007-path-conventions.md`). GATE 1 (`graph-powers:project-planner`) PASS. User approved. Proceed to `phase-b-writing-plans.md`.

---

## Loop contract

> Phase A is a goal-gated loop. Model: `references/loop-engineering.md`.

- **trigger:** task classified L3+ on `${git.workBranch}`.
- **goal (binary):** spec file exists **AND** GATE 1 `graph-powers:project-planner` = PASS **AND** user approved **AND** zero TBD/placeholder tokens **AND** every `[ASSUMED]` labeled. *(L3: inline 3-section spec acknowledged by user — no file, no GATE 1.)*
- **body:** inspect → clarify → compare approaches → present design → review → correct.
- **guards:** HARD-STOP 3 spec revisions → escalate · GOAL-GUARD: no observable destination means
  no design · no speculative feature or abstraction without a current requirement.
- **terminal:** goal PASS → at L3, return to the requested implementation path; at L4+, continue to
  Phase B. Any guard trips → escalate to user.

---

## Core method and sizing

Step 0 has already chosen the path:

| Path | Planning depth | Output |
|---|---|---|
| **Spike** | `/research`; the answer is the deliverable | Evidence-backed recommendation; any artifact is throwaway |
| **L3 bounded** | Existing flow, one domain | Short design in chat; no spec or plan file |
| **L4+ architectural** | New subsystem, cross-domain contract or structural change | Approved `spec.md`, then Phase B |

Hidden complexity only moves upward: stop, state what changed, and reclassify. Do not downgrade a
task merely to avoid a spec.

KISS and YAGNI bind the design. Prefer the existing unit named by the reuse ledger. Compare only
approaches that could genuinely win; two is enough when there are two, and one is honest when the
constraints leave no meaningful alternative. Do not add a feature, abstraction, compatibility shim
or extension point without a current requirement or named consumer.

---

## Step 1 — Inspect before asking

Read the current flow, its nearest `AGENTS.md`, recent relevant changes, the reuse candidates from
Step 0 and `references/layer-map.md`. At L3 use one background `graph-powers:explorer`, as the
execution floor requires. Add `graph-powers:librarian` only when the decision depends on current
external API, security or version behaviour; when both are needed, dispatch them in one message.
Every prompt follows `${CLAUDE_PLUGIN_ROOT}/references/execution-floor.md § 4`.

## Step 2 — Clarifying questions

Use `AskUserQuestion`. **One topic per question.** Prefer 2-4 multiple-choice options. Cover: **Purpose** (business/user outcome) · **Constraints** (deadlines, surfaces, must-keep-working) · **Success criteria** (observable "done") · **Reuse vs new** (which existing pattern/file to extend) · **Scope edges** (explicit non-goals).

**Skip questions the user already answered** — re-asking burns trust. For a real L6 risk surface,
ask which assumption would invalidate the preferred approach; do not add ceremony merely because of
the label.

## Step 3 — Consolidate research findings

Consolidate the returned evidence, cross-check layer order, and surface only contradictions that can
change the design. Mark unresolved in-scope assumptions `[ASSUMED]`; unknowns that prevent a task
list return to Step 0's fog gate instead of being guessed closed.

## Optional divergent pass — gated

This pass is expensive and off by default. Run it immediately when the user explicitly asks for
"ADHD mode", a wide brainstorm or divergent ideation. Without opt-in, run it only when **all** hold:
the problem has multiple viable answers, choosing the obvious answer wrongly is costly, and the user
did not ask for a quick, standard, canonical, textbook or one-line answer. Otherwise go to Step 4.

**Diverge without critique.** Select up to five frames within the wave width supplied by
`${CLAUDE_PLUGIN_ROOT}/references/shared/070-parallel-agent-spawn.md`: four problem-relevant and one
wild when width allows; at reduced width, retain one wild. A smaller explicit request may use up to
three. Useful frames fit in one pool: constraints/hardware · regulator/provability · novice/no
conventions · attacker/failure
inversion · biology/emergence · logistics/queues · game/feedback loops · markets/incentives · direct
inversion · zero-resource or unlimited-resource extreme · remove the load-bearing assumption ·
speedrunner/skips · on-call/operability.

Dispatch one isolated, read-only background batch under
`${CLAUDE_PLUGIN_ROOT}/references/shared/070-parallel-agent-spawn.md`. Besides the required delegation
wrapper, each branch receives only the problem, known constraints, one frame and this contract:

> DIVERGE. Produce six terse, distinct ideas from this frame. Do not critique, rank or hedge. Ban the
> first three obvious answers. Return only a JSON array of `{"text":"...","rationale":"..."}`.

Keep branches mutually blind; never reveal one branch's output to another, because shared context
anchors the set. Stop early when new ideas repeat existing shapes. Generate six ideas per selected
frame; an explicitly small request uses four.

**Converge separately.** After the batch, the main thread becomes the evaluator; generators never
judge their own output (`references/loop-engineering.md § Generator-Evaluator Loop`). Score each idea
0–10 on novelty, viability and fit; rank by `0.35N + 0.40V + 0.25F`, flag hidden-cost or premature-
abstraction traps, and cluster 3–6 groups by underlying angle rather than wording. Exclude traps and
take the top three. Deepen those in one second isolated parallel batch: 4–8 sentence sketch,
load-bearing risk, first concrete step, and 3–5 variations, hybrids or unlocks.

**Present proportionally.** For explicit wide ideation, show: brief → clustered pool with
`[N# V# F#]` → 2–4 shortlisted options and separate traps → three deep dives → one wildcard
provocation. Mark the non-obvious viable pick with `★`. For an automatic high-stakes pass, omit the
full pool and carry only the shortlist, traps and deep dives into Step 4.

## Step 4 — Compare viable approaches

When a real trade-off exists, present two or three approaches and lead with the recommendation. One
approach is enough when repository constraints eliminate the others; say why instead of inventing
contrast. Include reuse/extend or do-nothing when either can meet the destination. If the divergent
pass ran, use its shortlist here; do not reopen discarded branches.

```
**Option N — <name>**
- Approach: <one-sentence summary>
- Pros / Cons: <2-3 bullets each>
- Project risks: <ORM pitfall, platform-specific runtime bug, split deploy target, session handling, etc.>
- Layer chain: <which layers touched, in order>
```

Get user pick.

## Step 5 — Present design in sections

Sections scale to the decision: a few sentences when straightforward, up to roughly 200-300 words
when nuanced. Cover **architecture**, **components and responsibilities**, **data flow**, **error
handling** and **testing**. After each section ask whether it is correct so far; rewind on pushback.

Design for isolation: one purpose per unit, explicit interfaces, independently testable boundaries.
Follow existing repository patterns and keep targeted improvements inside touched code only. No
unrelated refactor and no new layer merely to make the diagram look cleaner.

## Step 6 — Write spec doc

**Path:** `${paths.planDir}/YYYY-MM-DD-<kebab-case-slug>/spec.md` (today's ISO date, UTC). The plan that Phase B writes lands beside it as `PLAN.md`, so the whole effort is one directory.

```markdown
# <Title> — Design spec

## Destination          — observable condition from Step 0
## Context              — why this work (problem/constraint/deadline)
## Reuse ledger         — link or copy the binding rows from Step 0, unchanged
## Regression watchlist — existing behaviour that must survive, with proof commands
## Background research  — internal findings; external findings only when required; contradictions resolved
## Approach (chosen)    — one-paragraph summary + why over alternatives
## Architecture         — modules + boundaries + full file paths (layer-labeled)
## Data flow            — request/event traversal + state transitions
## Error handling       — failure modes + recovery paths
## Testing              — existing coverage + new test plan
## Assumptions          — [ASSUMED] every inferred constraint
## Out of scope         — explicit non-goals
## Not yet specified    — declared fog; empty only when explicitly stated
## Rollback             — how each risky or externally visible step is undone
## References           — spec lineage (related specs, ADRs, prior plans)
```

Run the relevant Markdown/config checks, but do not stage or commit the spec
without explicit current-turn user approval.

## Step 7 — Spec self-review

Scan before GATE 1: every in-scope need is covered · no placeholder or invented detail · architecture,
data flow and testing agree · scope is one coherent project · every ambiguity is resolved or lives
under `## Not yet specified` · every assumption is `[ASSUMED]` · no design element serves an
out-of-scope row.
Fix inline once.

## Step 8 — GATE 1 — planning review (L4+ mandatory)

Dispatch `graph-powers:project-planner` with the seven-section prompt from
`${CLAUDE_PLUGIN_ROOT}/references/execution-floor.md § 4`. It reviews only the spec against the
destination, reuse ledger, repository evidence, scope, layer order, internal consistency and YAGNI.
It is read-only and returns the canonical Context Handoff.

**PASS** → Step 9. **FAIL** → revise inline against cited findings, then re-run; **HARD-STOP at 3
iterations** → escalate. **BLOCKED** → surface to the user, do not retry blind.

## Step 9 — User approval

> "Spec written to `<plan dir>/spec.md` and the planning review passed. Approve Phase B, which writes the implementation plan?"

Wait for explicit "yes"/"approve"/"go". On change request → revise + re-loop self-review + Step 8.

## Step 10 — Transition

```
"Phase A complete. Spec at <path>. Starting Phase B."
```
Read `phase-b-writing-plans.md` next.

---

## L3 light path (truncated flow)

For L3: (1) targeted repository inspection with one background explorer · (2) one clarifying question
only if it changes the design · (3) inline three-section spec (`Architecture`, `Data shape`,
`Validation`) · (4) user approval · (5) hand off to the requested implementation path. No file and no
reviewer gate.

## L6+ extra

Add a pre-mortem and ADR only when the task has a real risk surface or more than one viable
architecture, per `phase-b-writing-plans.md § Risk — pre-mortem + ADR`.

---

## Stopping conditions

| Condition | Action |
|---|---|
| No observable destination | STOP; clarify the outcome before designing |
| Scope contains independent deliverables | STOP; split them and design only the first approved slice |
| User rejects 3 design proposals | Stop, ask for explicit constraints, do not auto-iterate |
| evaluator FAIL 3× on same spec | Escalate; spec likely has fundamental ambiguity |
| Background agents both return BLOCKED | Halt Phase A, surface, do not invent design from nothing |
| Scope keeps expanding | Stop, decompose into sub-projects, brainstorm only first |
