# The craft passes

What `/design § 3` runs after the direction contract exists. Each pass is one bounded delegation
with one question; it carries the contract from `§ 1`, the baseline from `§ 2`, this file's entry
for the pass, and `craft-floor.md`. A pass without a contract polishes whatever it finds — that is
how a surface gets better spacing on a look nobody chose.

## Routing is not here

Which passes a mode runs, in what order, and in which agent each one runs is `/design § 3`'s table
— the command routes; this file is what the agent running a pass reads. Every pass except `audit`
writes, and runs in `graph-powers:frontend-specialist`; `audit` reports only. One pass per
delegation, one writer per file. A pass the target does not need is skipped and the skip is said,
with the reason; `quieter` is the inverse of `bolder` and replaces it when the baseline says the
surface is loud. A pass that finds the toolchain broken — stale types, a failing build, a missing
token file — reports it and stops; repairing the toolchain inside a design pass hides what the pass
changed.

## The passes

Each one: what it asks, what it reads, what it changes, when it is done. The checks it is measured
against are in `craft-floor.md` and are not repeated here.

### `shape` — from contract to buildable spec

Asks: what exactly gets built, and in what states. Reads the contract, the project's components,
tokens and design rule. Produces — without writing UI code — the component inventory (what exists
and is reused, what is new), the four data states and the interaction states per component, the
copy strings in the contract's register, the responsive behaviour at each breakpoint, and an ASCII
wireframe per viewport that a reader could build from. Names every token the build needs and
flags any the project does not have. Done when the spec could be handed to someone who has not
read the conversation.

### `build` — the first complete implementation

Asks: does the built surface match the contract and the `shape` spec. Reads both plus the incumbent
code. Writes the surface end to end — every state, every breakpoint, real or labelled-synthetic
content, tokens only, no colour literal — and runs the inspection round from the floor once. Done
when the surface is complete rather than promising: nothing left as a TODO, every state reachable.

### `audit` — findings against the floor and the contract

Asks: where does the existing surface fail the floor, and where does it drift from the contract.
Read-only, and without a browser: the render — one screenshot per width the surface ships to, of
the scope — is captured before the delegation, as `/design § 2` directs, and its paths travel in
the handoff. Reads the target, its token source and those renders. Returns a prioritised findings
list — floor failures first, contract drift second, defaults from
`defaults-catalogue.md` third — each with the location, the measured value and the fix. This is the
baseline `/design § 5` diffs against; the writing passes consume it in order. Done when every
finding has a location and a number.

### `harden` — production-ready

Asks: what breaks under real content and real conditions. Reads the audit's findings tagged
states, i18n, edge. Changes: the four data states designed and wired; long strings, empty strings,
zero, one, many, and the longest real value; right-to-left and a 30% longer translation; slow
network (loading keeps layout height); keyboard-only and screen-reader paths; the error copy. Done
when every state in `shape` is reachable in the browser and nothing overflows.

### `typeset` — the type system

Asks: does the type carry the hierarchy the contract set. Changes: one scale with weight steps, the
measure, size-specific tracking and leading, tabular numerals where numbers align, the display
face used with restraint and the body face doing the reading, balanced headings, the real copy
checked at every breakpoint. Never changes the faces the contract chose. Done when two adjacent
levels are distinguishable at a glance and no line overflows.

### `layout` — spacing, rhythm, hierarchy

Asks: does the eye land where the contract's thesis says it should. Changes: the spacing scale
applied — tight within, generous between, more above a heading than below — the grid and the
alignment, the visual weight of the signature against everything around it, containers replaced
by space and rules where cards were the lazy container. Done when a five-second look finds the one
next action and the signature, in that order.

### `adapt` — every viewport and input

Asks: does the composition hold at 360px, at the project's breakpoints, at 1440px+, with a larger
text size, with touch. Changes: the responsive rules, the touch targets, the thumb-reach placement
of the primary action on mobile, hover gated to fine pointers, the reading order preserved when
columns stack. Done when the same content and the same hierarchy read on every device class.

### `optimize` — the UI's own performance

Asks: what the surface costs to render and to move. Changes: animations moved to `transform` and
`opacity`; images sized, lazy where below the fold, with explicit dimensions; fonts subset,
self-hosted, `font-display` set with size-matched fallbacks so text does not reflow; layout shifts
removed; expensive filters bounded. Everything measured is the domain of `/perf` — this pass fixes
what the design itself introduced. Done when nothing the surface does drops frames or shifts
layout on a mid-range phone.

### `bolder` — amplitude, on the signature

Asks: what one thing, made bigger, makes the surface land. Reads the contract's `Signature` and
`Risk`. Changes: the signature's scale, contrast or presence raised; everything around it left
quiet or made quieter. Never adds effects, a second accent or decoration — that is the tell, not
the fix. Done when the surface is remembered by one thing and it is the thing the contract named.

### `quieter` — amplitude, down

Asks: what is competing with the signature. Changes: decoration cut, the palette's accents pulled
back to their semantic roles, motion reduced to the one authored moment, density made calm. Done
when the remove-one-accessory test (`mirror-test.md § 2`) finds nothing left to remove.

### `animate` — motion, from the contract's mood

Asks: what moves, and what never does. This pass is the `animate` skill in build mode — its gate,
its three curves, its duration and spring tables, its reduced-motion and hover rules are the
authority, and no value here is approximated from memory. The specialist opens it by path,
`${CLAUDE_PLUGIN_ROOT}/skills/animate/SKILL.md`: it carries no `Skill` tool, and a path read also
sidesteps a same-named skill installed outside the plugin. Reads the contract's `Motion` line as
the brief. Done when the one authored moment exists, every frequent action is still, and
`prefers-reduced-motion` has its branch.

### `colorize` — colour with roles

Asks: does every colour on the surface mean something. Reads the contract's `Palette` with the
reason beside each value. Changes: accents restricted to action, status, selection and the
signature; semantic scales (5–10 steps per hue, the project's or proposed by name); secondary text
tinted from the hue; both themes checked where the project ships both. Never introduces a value
the contract does not explain. Done when every accent occurrence can be named by its role.

### `polish` — the last pass before handoff

Asks: what would make a careful reader think nobody checked. Changes: the browser surfaces themed
(selection, caret, scrollbar, focus ring, underline offset, `accent-color`); alignment to the pixel;
optical adjustments (icons optically centred, hairlines on the pixel grid); consistent radius and
shadow per elevation; the last copy strings; the inspection round from the floor run once and its
findings fixed in one batch. Done when the round comes back empty or with accepted notes — then
`/design § 4` and `§ 5`.
