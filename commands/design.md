---
description: "Use when creating or improving UI layout, type, hierarchy, tokens, states, responsiveness or direction. Routes new work to designer and existing repair to design-fix. Not for broken behavior (/debug) or speed (/perf)."
workflow_type: prompt-chaining
---

# /design — Design Workflow

**ARGUMENTS**: $ARGUMENTS

> **Read before step 0 — never reconstruct these from memory:** `${CLAUDE_PLUGIN_ROOT}/references/shared/000-config-loader.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/005-superpowers-bootstrap.md`
> Read `${CLAUDE_PLUGIN_ROOT}/references/shared/007-path-conventions.md`. Read
> `${CLAUDE_PLUGIN_ROOT}/references/shared/030-agent-assignment-matrix.md` only when the scope needs an
> agent that § 2, § 3 and § 5 do not already name.
> Read `${CLAUDE_PLUGIN_ROOT}/references/shared/060-skill-domain-matrix.md`

Modes, from the first positional argument:

```
/design <target>            new surface — direction, spec, build, audit
/design fix <target>        existing UI — production-readiness pass
/design improve <target>    existing UI — raise the ceiling (bolder, motion, colour)
```

---

## The design layer

The direction and the craft passes are this plugin's own: `designer` (`skills/designer/`) carries
the method, the direction contract, the passes and the floor. Nothing in § 3 needs a package
runner or an external plugin.

`design-fix` owns the evidence baseline, surgical/structural classification and repair contract for
an implemented interface. It reuses `designer`'s floor and passes; it does not copy their checks.

`Skill("landing-page-design")` — loaded only when the target is a landing or marketing page — owns
the page system for that surface: intake, section order, layout type, conversion copy, the index
decision and the ship floor. It ships with the plugin as an adapted copy of elayadesign's skill;
its visual canon is a fallback behind the project's tokens and the direction contract, and every
value in it is proposed, never applied silently. Do not reimplement it inline — a half-remembered
version of a page methodology is worse than none.

---

## Stopping conditions

- Three iterations fail the direction check → present options and ask.
- No design token exists for a required colour role → ask, never invent one.
- The design contradicts an existing pattern in `${paths.componentsRoot}` → ask which wins.

---

## 0. Context

```typescript
Skill("superpowers:using-superpowers");   // meta — bootstrap (per `${CLAUDE_PLUGIN_ROOT}/references/shared/005-superpowers-bootstrap.md`)
Skill("design-fix");                      // fix only — baseline, classification, locked repair contract
Skill("designer");                        // new/improve, and structural fix after design-fix reopens direction
Skill("uxmaster");                        // UX judgement: conversion, onboarding, hierarchy
Skill("landing-page-design");             // only when the target is a landing or marketing page
Skill("animate");                         // only on improve — the motion bar § 5 judges against
```

Read, in this order: root `DESIGN.md` (the project's design authority), `${rulesDir}/design.md`, and the
files in scope. When the project declares no design rule, say so in the output — the work continues,
but every visual decision is then yours to justify rather than the project's to enforce.

Continuing a prior session: read the handoff note before anything else.

---

## 1. Lock the repair and direction (`design-fix`, then `designer`, then `uxmaster`)

Classify the work before touching a file:

| Class | Signal | What happens |
|---|---|---|
| **Surgical** | existing component, known pattern, no new information architecture | `design-fix` locks the smallest repair and preserved behavior; no artificial alternatives, then straight to § 3 |
| **Structural** | new surface, or an existing surface with changed flow or hierarchy | New work starts in `designer`; existing work first gets the `design-fix` baseline. All five `designer` moves produce three directions that differ in kind — **user picks before any code** |

A "direction" is measurable or it is decoration: name the user outcome it changes and how you would
know it worked. `uxmaster` supplies that outcome and the lever behind it; `designer` supplies the
visual world it lives in. Where the brief pins a look, the brief wins over both.

The output of this section is the **direction contract** `designer` defines. It leaves this section
only after the any-brief test in `designer` move 5; § 3 builds from it and § 5 measures against it.
A contract whose palette or type could serve any other product in the category has not run the test.

For a structural change on an L4+ surface, run `Skill("graph-powers:planning")` through Phase A and
write its approved spec to `${paths.planDir}`. Do not start a second brainstorming method.

---

## 2. Critique before building (`graph-powers:ui-ux-designer`, read-only)

Spawn `graph-powers:ui-ux-designer` over the scope. It reads; it never writes. It returns prioritised findings —
usability heuristics, WCAG 2.2 AA, visual hierarchy, information density — against the direction
locked in § 1.

For `/design fix` and `/design improve` this is the **baseline**: the findings list here is what the
closing audit in § 5 is measured against. Without a baseline, "it looks better" is the whole report.
For `fix`, its fields and evidence rules are the output contract in `design-fix`; this command owns
only the orchestration.

The critic has no browser. Before spawning it — here, and again in § 5 — capture the render: one
screenshot per width the surface ships to, of the files in scope, taken by `graph-powers:verification`
(it drives the browser through the `webapp-testing` skill) and saved under the project's log path.
Hand the paths to the critic with the direction. Findings then carry measured values, not
impressions, and the § 3 `audit` pass reuses the same renders.

---

## 3. Craft passes (`designer`, run by `graph-powers:frontend-specialist`)

The passes are `designer`'s own, and the specialist that runs a pass is the one who opens its
definition — this command routes, it does not read the method into its own context. One pass per
delegation, in the order the mode calls for. Every delegation carries the § 1 contract, the § 2
baseline and this handoff:

```
PASS: <name>  TARGET: <files>  MODE: <new surface | fix | improve>
Read ${CLAUDE_PLUGIN_ROOT}/skills/designer/references/craft-passes.md — your pass's entry: what it
asks, reads, changes, and when it is done. Read
${CLAUDE_PLUGIN_ROOT}/skills/designer/references/craft-floor.md immediately before your first edit,
not earlier. For animate, also read ${CLAUDE_PLUGIN_ROOT}/skills/animate/SKILL.md — build mode; its
tables are the only source of values. The direction contract below is what you build to; the project's tokens and design
rule win over it. Return: what changed, the floor checks you ran with their measured values, and
what you left for the next pass.
<contract from § 1>  <baseline findings from § 2, for fix/improve>
```

| Mode | Passes |
|---|---|
| new surface | `shape` → `build` → `polish` |
| `fix` | `audit` → `harden` → `typeset` → `layout` → `adapt` → `optimize` → `polish` |
| `improve` | `audit` → `bolder` → `animate` → `colorize` → `polish` |

`audit` is § 2's critique scoped to the floor and runs read-only inside `graph-powers:ui-ux-designer`;
every writing pass runs inside `graph-powers:frontend-specialist`, foreground. The `animate` pass
(`improve` only) is the `animate` skill in build mode, opened by path in the handoff — gate, curves,
budgets, block list — tuned to the contract's motion mood; `Skill("emil-design-eng")` and `Skill("apple-design")` when installed add
the invisible details and gesture materials, and their absence changes nothing.

Two rules hold across every pass:

- **The project's tokens win.** The contract and `landing-page-design` enrich; neither replaces a
  declared palette, spacing scale or motion canon. On a conflict, the project's design rule is
  authoritative and the conflict is reported.
- **Drift repair is never a side effect.** If a pass finds the toolchain broken, report it and stop.
  Fixing the toolchain in the middle of a design task hides what changed.

`graph-powers:ui-ux-designer` never edits — it is the only reason its critique is worth reading.

---

## 4. Gates

Run `/verify quick`. A design change that breaks the type check is not a design change, it is a
broken build with better spacing.

---

## 5. Closing audit (`graph-powers:ui-ux-designer`, read-only)

Re-run the § 2 critique against the implemented files and diff the findings:

- which baseline findings are resolved,
- which remain, and why they were accepted,
- what the change introduced that was not there before.

Then the verdict, in the `/verify` vocabulary: `VERIFIED`, `VERIFIED-WITH-NOTES`, `NEEDS-WORK`.

---

## Anti-patterns

| Don't | Do |
|---|---|
| Run a craft pass without the § 1 contract in the delegation | The contract is what the pass is measured against; without it a pass polishes whatever it finds |
| Loop the inspection round | One batched round, one fix batch, at most one confirmation — then § 4 and § 5 |
| Let `graph-powers:ui-ux-designer` fix what it found | It reports; `graph-powers:frontend-specialist` fixes. A critic with a pen stops being a critic |
| Ship a structural change without the three-direction comparison | The comparison is the deliverable, not overhead |
| Adopt an external palette suggestion over the project's tokens | Project tokens are authoritative; report the conflict |
| Fill a free axis with the category default — cream and serif, near-black and acid green, three icon cards | `designer` move 2: derive it from the subject's world; the standard is the explicit exit, never the silent default |
| Soften a default when the mirror test catches it | Rewrite it from the subject. A slightly different cream is the same default with less confidence |
| Skip the § 2 baseline on a `fix`/`improve` run | Without it there is nothing to measure the result against |
| Call it done because it looks better | § 4 gates and § 5 diff, with output |
