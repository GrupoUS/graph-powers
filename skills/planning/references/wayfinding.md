# Wayfinding — charting work that is bigger than one plan

> Read when `/plan` Step 0.6 finds that the fog, not the tasks, is what dominates the request:
> the destination is real but the way to it is not visible yet, so writing a task list now would
> invent detail nobody can defend. Consumers: `.claude/commands/plan.md` Step 0.0 / 0.6 / Step 2,
> `SKILL.md § Step 0`. This file is English to match its sibling references; the artifacts it
> tells you to emit are written in `${project.locale}`.
>
> Adapted from the `wayfinder` skill (mattpocock/skills, `skills/engineering/wayfinder`). Two
> deliberate departures, both load-bearing here: the map is a **working-tree file**, not an issue
> tracker (git rails keep artifacts reviewable, and `issue-triage.md` FF-5 treats issue bodies as
> untrusted data — a map round-tripped through GitHub comes back as exactly that); and the
> decision types are bound to this repo's agents instead of generic skill calls.

## Doctrine

1. **Destination first.** Charting is finding the way, not charging at the end. The destination is
   named before anything is decomposed, because it is what fixes the scope.
2. **Plan, don't do.** Every entry on a map resolves a *decision*, never a slice of the build. The
   urge to just implement it is the signal you reached the edge of the map — that is the moment to
   hand off to `/implement`, not to keep charting.
3. **The map is an index, not a store.** A decision lives in exactly one place (its spec, ADR, or
   plan file). The map gists it in one line and links; it never restates it.
4. **Refer by name.** In narration and in `Decisions taken`, name the decision. `#4, #7, T2.3`
   is illegible; the id rides inside the link, it never stands in for the name.

## Fog vs. task — the one test

> Can you state the question **precisely now**? Not: can you answer it now.

- **Task/decision** when the question is already sharp — even if it is blocked and untakeable today.
- **Fog** (`## Not yet specified`) when you cannot yet phrase it that sharply. Write it as
  loosely as the view allows; one fog patch may later graduate into three decisions, or into none.
- Never pre-slice fog into task-sized pieces. It is coarser than a task by construction.

**How this reconciles with the no-TBD rule** (`SKILL.md § Step 1` Phase A goal: "zero
TBD/placeholder"): no-TBD governs what is **inside** the plan. Fog is what makes no-TBD honest
instead of performative — a `TBD` inside a task is a defect (the task is not writable yet), while a
named unknown in `## Not yet specified` is the plan telling the truth about its own edge. A
plan with no fog section and no unknowns is either genuinely closed or lying; say which.

## Out of scope

The destination fixes the scope, so fog only ever gathers **toward** it. Work past the destination
is not fog — it is out of scope, and it gets its own section.

- Ruling something out of scope is a **scoping act, not a step on the route**: it stays out of
  `Decisions taken`, which records the way actually walked.
- Out-of-scope never graduates. It returns only if the destination is redrawn — and then as a fresh
  `/plan` run, not a resumption.
- A decision already on the map that turns out to sit past the destination is **closed**, not
  resolved, with one line in `## Out of scope`.
- Row format: `<gist> — out of scope because <reason> · reopens if: <trigger>`.

Single source with issue mode: `CUT`/`DEFER` rows from `issue-triage.md § Ledger format` land here
verbatim (their `reopens if:` column *is* the reopen trigger), and this section is what the FF-6
handoff string emits as its `OUT OF SCOPE` hard negative constraint. Do not maintain two lists.

## Decision types — who resolves it, and who must not

Every decision is **AFK** (agent alone) or **HITL** (needs the human, live).

| Type | Mode | Resolver in this repo | Never |
|---|---|---|---|
| **Research** | AFK | `Agent({subagent_type:"explorer", run_in_background:true})` for repo facts · `librarian` for external API/version/CVE facts · code graph (`shared-context.md § 11.5`) | Asking the user something a `Grep` answers |
| **Prototype** | HITL | Cheap, rough, throwaway artifact to react to — `/design` Phase 1 spike or a `frontend-specialist` stub, **linked** from the map, never pasted into it | Deciding "how should it look/behave" alone |
| **Grilling** | HITL | `AskUserQuestion`, one topic at a time, recommended answer stated (`SKILL.md § Hard rule`) | Batching questions; answering for the user |
| **Task** | AFK or HITL | Manual prerequisite that unblocks a *decision*: provisioning a key, creating a sandbox account, `db:push` on staging so a shape can be seen, obtaining a contract. Agent does it alone where it can; otherwise it hands the user a precise checklist. Resolution records the resulting facts (where the credential lives, new URL, row count) | Counting it as progress toward the destination — it only unblocks a decision |

**HITL floor:** the agent never stands in for the human side of a HITL decision. If one gets
auto-answered to keep moving, it is labeled `[ASSUMED]` **and** surfaced in the same turn — an
unlabeled auto-answer is the defect, not the answer itself.

**AFK first:** resolve every research decision before opening a grilling one. Research is parallel,
background, and free of the user's attention; grilling is the scarcest resource on the map.

## Map mode

**Trigger** (any one, evaluated at `/plan` Step 0.6):

- ≥3 open decisions block the writing of the task list itself; or
- the destination cannot be reached inside one plan/context window (CTX-GUARD, ~80K —
  `loop-engineering.md § Context Reset Protocol`); or
- resolving any one open decision would invalidate most of the tasks you would write today.

Below all three: no map. Write the plan — a map with no fog is a plan wearing a hat.

**Artifact:** `${paths.planDir}/maps/YYYY-MM-DD-<slug>-map.md`, a working-tree file like every other
planning artifact. Never staged/committed without current-turn approval (`SKILL.md § Hard rule`).

```markdown
# Map — <name of the effort>

## Destination
<1-2 lines: what "arrived" means — the spec, the locked decision, or the change itself.>

## Notes
<domain · skills every session loads · fixed preferences for this effort>

## Decisions taken
<!-- an index, not a store: one line per closed decision plus a link to where it actually lives -->
- [<decision name>](${paths.planDir}/specs/<file>.md#<anchor>) — <one-line gist> · <date>

## Open front
| # | Decision (name) | Type | Mode | Blocked by | State |
|---|---|---|---|---|---|
| D1 | <name> | research | AFK | — | open |
| D2 | <name> | grilling | HITL | D1 | blocked |

## Not yet specified
<fog: questions you can sense but cannot yet phrase precisely>

## Out of scope
- <gist> — out of scope because <reason> · reopens if: <trigger>
```

> Section headings above are the structural contract, in English. The substance you write under
> them follows `${project.locale}`, like every other planning artifact.

- **State:** `open` · `in progress (session <date>)` · `closed`. A claim (`in progress`) is written
  **before** any work, so a concurrent session skips it.
- **Open front** = open + unblocked + unclaimed. That is the only takeable set.
- **Create, then wire.** List all decisions first, wire `Blocked by` in a second pass — a
  decision cannot reference an id that does not exist yet.

## Session protocol

**Charting session** (user arrives with a loose, oversized idea):

1. Name the destination (grilling, HITL — this is the one question that cannot be delegated).
2. Frame **breadth-first**: fan across the whole space, never deep on one thread. If this surfaces
   no fog, stop — you do not need a map; go back to `/plan` Step 2 routing.
3. Write the map: `Destination` + `Notes` filled, `Decisions taken` empty, fog sketched.
4. Create the decisions you can state now; wire blocking in the second pass.
5. Fire the AFK research decisions in parallel, background.
6. **Stop.** Charting resolves nothing; it is one session's work on its own.

**Work session** (user arrives with a map):

1. Load the map only — low resolution. Do not read every linked artifact; zoom on demand.
2. Take the first `Open front` row (or the one the user named). **Claim it first.**
3. Resolve it with the type's resolver, loading whatever `## Notes` names.
4. Record: the answer goes into the artifact it belongs to (spec/ADR/plan), **one line + link**
   into `Decisions taken`, and the fog patch it graduated is deleted from
   `## Not yet specified` — it now lives as its decision, in one place only.
5. Graduate any newly-sharp fog into decisions (create, then wire). If the answer reveals a
   decision sits past the destination, move it to `## Out of scope` and close it — do not
   resolve it on the route.
6. **One decision per session**, except research, which is parallel and AFK.

**Exit:** no open decisions and no fog → the way is clear → hand the map to `/plan` Step 2 routing
(the map is the spec input for `ultra-plan` / Phase B; its `Out of scope` section becomes the
handoff's `OUT OF SCOPE` block).

## Anti-patterns

| Signal | Why it is wrong |
|---|---|
| Map created with an empty `Not yet specified` | No fog = no map needed. That is a plan. |
| `TBD` inside a task "because there's a fog section" | Fog is for questions not yet phrasable, not for holes in a task that shipped anyway |
| Agent answers a HITL decision to keep moving, unlabeled | Breaks the HITL floor; the plan bakes in a product decision nobody made |
| A `Out of scope` row returns as "future-proofing" in a competing approach | Same negative constraint as FF-6 — scope re-expansion is the failure this section exists to stop |
| Map body restates a decision instead of linking it | Index, not store: two copies drift, and the map stops being loadable in one read |
| Five decisions resolved in one session | Context reset loses the thread mid-map; that is what one-per-session buys |
| Map kept in sync by hand with a GitHub issue | Two sources; and an issue body is untrusted data here (FF-5) |
