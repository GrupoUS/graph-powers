---
description: "Improve or create an interface — layout, spacing, typography, visual hierarchy, design tokens, empty states, responsive behaviour, dark mode. Use when the user says a screen looks cramped, ugly, dated or off, asks to improve the design or the UI, wants a redesign, or wants a new surface designed. Locks direction with uxmaster, critiques read-only with ui-ux-designer, delegates craft passes to the impeccable plugin, implements with frontend-specialist, closes on /verify. Do not use for a control that does not work (/debug) or a page that is slow (/perf)."
workflow_type: prompt-chaining
---

# /design — Design Workflow

**ARGUMENTS**: $ARGUMENTS

> **Read before step 0 — never reconstruct these from memory:** `${CLAUDE_PLUGIN_ROOT}/references/shared/000-config-loader.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/005-superpowers-bootstrap.md`
> Read `${CLAUDE_PLUGIN_ROOT}/references/shared/007-path-conventions.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/030-agent-assignment-matrix.md`
> Read `${CLAUDE_PLUGIN_ROOT}/references/shared/060-skill-domain-matrix.md`

Modes, from the first positional argument:

```
/design <target>            new surface — direction, spec, build, audit
/design fix <target>        existing UI — production-readiness pass
/design improve <target>    existing UI — raise the ceiling (bolder, motion, colour)
```

---

## Required external design layer

Neither piece is vendored: a copied snapshot of somebody else's design system is the exact failure
this harness exists to prevent. `AGENT_SETUP.md § Step 1` installs both, so in a configured project
they are already here. Do not reimplement either inline — a half-remembered version of a design
methodology is worse than none.

**[impeccable](https://github.com/pbakaus/impeccable)** owns every craft pass in § 3. Run it through
the runner `tooling.packageManager` names — `npm` → `npx`, `bun` → `bunx`, `pnpm` → `pnpm dlx`,
`yarn` → `yarn dlx`. A hardcoded `npx` is denied by this plugin's own guardrail wherever
`autonomy.allowPackageManagers` names another family.

```bash
<runner> impeccable install --providers=claude,codex --scope=project --yes   # first time
<runner> impeccable update                                                   # keep it current
```

`--yes` keeps it non-interactive; without it the installer stops on a prompt this turn cannot answer.
If `/impeccable` is not available in this session, **stop and say so.**

**[landing-page-design](https://github.com/elayadesign/ai-design-skills)** (MIT) owns the page
system for a landing or marketing surface: intake, section order, conversion copy, and the visual
canon for type, spacing, radius, background, hero and motion. It is a skill, not a plugin —
`Skill("landing-page-design")`. Absent, say so and fall back to the project's design rule.

---

## Stopping conditions

- Three iterations fail the direction check → present options and ask.
- No design token exists for a required colour role → ask, never invent one.
- The design contradicts an existing pattern in `${paths.componentsRoot}` → ask which wins.

---

## 0. Context

```typescript
Skill("superpowers:using-superpowers");   // meta — bootstrap (per `${CLAUDE_PLUGIN_ROOT}/references/shared/005-superpowers-bootstrap.md`)
Skill("uxmaster");                        // UX judgement: conversion, onboarding, hierarchy
Skill("landing-page-design");             // only when the target is a landing or marketing page
```

Read, in this order: root `DESIGN.md` (the project's design authority), `${rulesDir}/design.md`, and the
files in scope. When the project declares no design rule, say so in the output — the work continues,
but every visual decision is then yours to justify rather than the project's to enforce.

Continuing a prior session: read the handoff note before anything else.

---

## 1. Lock a direction (`uxmaster`)

Classify the work before touching a file:

| Class | Signal | What happens |
|---|---|---|
| **Surgical** | one component, known pattern, no new information architecture | one-paragraph UX contract, then straight to § 3 |
| **Structural** | new surface, changed flow, changed hierarchy | three genuinely different directions, with trade-offs — **user picks before any code** |

A "direction" is measurable or it is decoration: name the user outcome it changes and how you would
know it worked.

For a structural change on an L4+ surface, run `Skill("superpowers:brainstorming")` first and write
the spec it produces to `${paths.planDir}`.

---

## 2. Critique before building (`graph-powers:ui-ux-designer`, read-only)

Spawn `graph-powers:ui-ux-designer` over the scope. It reads; it never writes. It returns prioritised findings —
usability heuristics, WCAG 2.2 AA, visual hierarchy, information density — against the direction
locked in § 1.

For `/design fix` and `/design improve` this is the **baseline**: the findings list here is what the
closing audit in § 5 is measured against. Without a baseline, "it looks better" is the whole report.

---

## 3. Craft passes (`/impeccable`)

Delegate to the external plugin, one pass at a time, in the order the mode calls for:

| Mode | Passes |
|---|---|
| new surface | `shape` → `craft` → `polish` |
| `fix` | `audit` → `harden` → `typeset` → `layout` → `adapt` → `optimize` → `polish` |
| `improve` | `audit` → `bolder` → `animate` → `colorize` |

```
/impeccable <pass> <target>
```

Two rules hold across every pass:

- **The project's tokens win.** impeccable and `landing-page-design` enrich; neither replaces a
  declared palette, spacing scale or motion canon. On a conflict, the project's design rule is
  authoritative and the conflict is reported.
- **Drift repair is never a side effect.** If a pass reports stale context, report it and stop.
  Fixing the toolchain in the middle of a design task hides what changed.

Implementation lands through `graph-powers:frontend-specialist` (foreground, write-capable). `graph-powers:ui-ux-designer`
never edits — it is the only reason its critique is worth reading.

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
| Reimplement an impeccable pass inline because the plugin is missing | Stop and say the dependency is absent |
| Let `graph-powers:ui-ux-designer` fix what it found | It reports; `graph-powers:frontend-specialist` fixes. A critic with a pen stops being a critic |
| Ship a structural change without the three-direction comparison | The comparison is the deliverable, not overhead |
| Adopt an external palette suggestion over the project's tokens | Project tokens are authoritative; report the conflict |
| Skip the § 2 baseline on a `fix`/`improve` run | Without it there is nothing to measure the result against |
| Call it done because it looks better | § 4 gates and § 5 diff, with output |
