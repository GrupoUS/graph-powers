---
name: designer
description: "Use when a surface needs a distinctive visual direction before code. Trigger on design this, redesign, look and feel, bolder, creative, generic, template-like or AI-looking. Used by /design; design-fix loads it only for structural repair. Not for in-place cleanup, motion alone, broken behavior or slowness."
---

# Designer

## Overview

A default is a decision nobody made. Left to habit, a model draws the same three or four looks for
every brief, and the reader recognises them before reading a word. This skill spends the freedom
the brief leaves open on a choice made for *this* subject, and holds the quality floor without
announcing it. Freedom is the deliverable; the floor is the price of admission.

It picks the direction, and it carries the craft passes that build to it —
`references/craft-passes.md`, measured against `references/craft-floor.md`. It does not tune
motion — that is `animate`, with `emil-design-eng` and `apple-design` when they are installed.

## When to use

- A new surface, screen or component that has no direction yet.
- A redesign, or a surface the user calls generic, bland, dated, template-like, "like every other
  site", or AI-generated.
- The user asks for bolder, more creative, more distinctive, less default — or the brief leaves a
  visual axis open and somebody has to decide what fills it.

**Not** when the brief pins the look. A pinned aesthetic, era, palette or font is followed exactly,
including when it asks for one of the defaults below — the brief's own words always win. A craft pass on a
direction already locked (`polish`, `typeset`, `layout`) runs from `references/craft-passes.md`
against the contract and never reopens move 3. Not for conversion levers (`uxmaster`), not for a
control that does not work (`/debug`).

## The stance

Six rules. Each carries its reason, because the reason is what covers the case the rule did not
anticipate.

1. **The brief wins; then the subject.** Where the brief leaves an axis free, spend it on the
   subject's own world — never on the category habit. The category habit is what every other
   result in the category already looks like.
2. **Derive, do not decorate.** Every distinctive choice traces to something real about the
   subject: its materials, instruments, artefacts, notation, publications, screen traditions. A
   palette the subject cannot explain is a template with a hex code.
3. **Spend boldness once.** One signature carries the memory, and the rest of the surface stays
   still so it can. Two signatures cancel each other, and five are noise. Before handing off,
   remove one accessory.
4. **Structure encodes truth.** Numbering, eyebrows, dividers, cards, columns — each says
   something true about the content or is deleted. Section numbers on content that is not a
   sequence are decoration wearing the costume of order.
5. **Cohesion over features.** Type, colour, motion and copy share one personality — crisp,
   calm, playful, editorial. Motion inherits the mood, not the library's default. A page whose
   parts were each "improved" separately reads as assembled.
6. **The floor is silent.** Contrast, targets, focus, reduced motion, the four data states, the
   project's tokens — built to, without commentary. A distinctive surface that fails AA is a
   defect with a nice palette.

## The method — five moves, before any code

Structural work (a new surface, a changed flow, a replaced identity) runs all five. Surgical work
(one component inside an established surface) inherits that surface's world and runs only moves 1
and 5: a local addition is never an identity exercise.

1. **Ground.** One line each: the subject; the audience and the scene they use it in (device,
   light, hurry); the surface's single job; what the project already decided — root `DESIGN.md`,
   tokens, incumbent components. When a design authority exists, the world is settled and the
   moves below shape composition, not identity. Say which case this is.
2. **Mine the world.** List five to seven things the audience knows by heart from the subject's
   own world — objects, places, rituals, notation, publications, interfaces — across at least
   three material families. Strike the category's stock artefact and its obvious inversion — two
   lanes of the same rut. When more than three candidates come from one family, the digging
   stopped at the first thing the subject brought to mind.
3. **Diverge.** Three directions that differ in kind, not in accent colour. Each carries a
   thesis, a palette with the subject-reason for every value, a type pair with the reason for the
   pairing, the first viewport, the signature, and its honest risk. The category standard is
   offered beside them as the explicit exit — named, never recommended, never silently the
   default.
4. **Commit.** The user picks, or the brief already did. Write the direction contract below.
   Every downstream decision — every colour, size, duration, string — derives from it.
5. **Mirror.** Run the two tests in `references/mirror-test.md`: the any-brief test (would this
   plan come out of a different brief in the same category? then that part is a default — rewrite
   it, do not soften it) and remove-one-accessory. Say what changed.

## The defaults reflex

The looks a model reaches for when it is not deciding. Legitimate when the brief asks for one;
a failure when the axis was free. Four or more of them on one surface and the surface is the
template, whatever else it does well. Typography is the highest-leverage axis — change the face
before touching colour or layout. The full catalogue, with the rewrite for each, is
`references/defaults-catalogue.md` — read it during move 5, not before move 2, or it becomes a
menu.

- The three AI looks: warm cream with a high-contrast serif and a terracotta accent; near-black
  with one acid-green or vermilion accent; a broadsheet of hairline rules, zero radius and dense
  columns.
- A neutral grotesk on a purple-to-blue gradient with glass cards, soft glow and a dark hero.
- The hero-metric template, three same-size icon cards, a kicker above every heading, `01 / 02 /
  03` on content that is not a sequence.
- Gradient text, glass as decoration, a thick coloured `border-left`, a hard offset shadow outside
  a world that chose neobrutalism.
- Emoji standing in for icons, monospace worn as a "technical" costume, the platform's default
  sans doing display work.
- The same fade-up on every section, scattered hover effects, a page that moves everywhere and
  therefore nowhere.
- Copy that could headline any product: elevate, seamless, unlock, supercharge, the feature triad.

## Direction contract

What move 4 writes and what `/design § 3` builds from. Every field is a decision, not a placeholder.

```
DIRECTION — <name>
Ground     subject · audience · scene · single job · authority (settled | incomplete | none)
World      the source in the subject's world, one line
Thesis     one sentence a reader could disagree with
Palette    token → value → why the subject explains it   (4–6 values)
Type       display / body (/ utility) → why this pair, and what it costs
Layout     one-sentence concept; ASCII wireframe when structural
Signature  the one element this surface is remembered by
Motion     mood (crisp | calm | playful | editorial) → what animates, what never does
Copy       register, plus three real strings in the product's voice
Floor      AA contrast · targets · visible focus · reduced motion · four states — held
Risk       the one bet, and why it is worth it
Mirror     what the any-brief test changed
```

## Craft — after the contract

The contract is what the passes build to; a pass without one polishes whatever it finds.
`references/craft-passes.md` defines the passes `/design` runs after it — `shape`, `build`, `audit`,
`harden`, `typeset`, `layout`, `adapt`, `optimize`, `bolder`, `quieter`, `colorize`, `polish`, and
`animate`, which is the `animate` skill in build mode — with who runs each and when it is done.
`references/craft-floor.md` is what every pass is measured against. Read the floor immediately
before editing UI, not while planning: loaded early it becomes a checklist to announce, and the
floor is silent. Build the whole thing, inspect it once across every width, repair what that
inspection shows as a single batch, allow one confirming look, and stop.

## Freedom has a floor

What "more creative" never buys back:

- **WCAG 2.2.** At AA: 4.5:1 on body text, 3:1 on large text and on the visible parts of
  controls (1.4.3, 1.4.11); targets at least 24×24 CSS px (2.5.8), or the larger minimum the
  project's design rule sets; focus visible and never obscured (2.4.7, 2.4.11). Held above AA
  because the project's design rule requires it: motion from interaction can be turned off
  (2.3.3) — under `prefers-reduced-motion`, cross-fade, never slide.
- **The project's tokens and `DESIGN.md` win** over any direction. A missing token is proposed in
  the contract and asked about — never invented silently. This is `/design`'s stopping condition,
  restated because a direction pass is where the temptation is strongest.
- **No invented claims.** Prices, customers, numbers, logos, capabilities. Illustrative content is
  authored at full fidelity and labelled synthetic.
- **Distinct is not loud.** A calm, precise, minimal direction is distinctive when every value in
  it can be defended. A maximal direction has to be executed in full; a minimal one has nothing to
  hide behind, so its spacing and type have to be exact. Either way the elegance is in the
  execution of the choice, not in the choice.

## Rationalisations

The thoughts that precede a default. Each has been observed; each is answered.

| Thought | Reality |
|---|---|
| "The brief said modern and clean" | Modern is not a direction; it is the absence of one. Ask the subject. |
| "Users expect the standard look" | Offer the category standard as the explicit exit. Never as the silent default. |
| "`polish` will fix it later" | Passes polish a direction. They do not pick one. |
| "Safe is faster" | Safe costs the same tokens, and the reader stops at the first cream hero. |
| "It needs more effects to feel designed" | More effects is the tell. One authored moment. |
| "The system font is always fine" | Fine on an Operate surface. A Persuade or Experience surface needs a face with a reason. |
| "This one detail nobody will notice" | Unseen details compound. That is the whole mechanism. |

## Where the depth lives

Do not restate these here; open them when the move calls for them.

- `references/defaults-catalogue.md` — every default with its tell and its rewrite; the sources
  each one was measured against.
- `references/mirror-test.md` — the any-brief test and remove-one-accessory, with one worked
  contract.
- `references/craft-passes.md` — the passes `/design` runs after the contract, who runs each, when
  each is done.
- `references/craft-floor.md` — the checks every pass is measured against, on the built result.
- `animate`, shipped with the plugin — the motion bar: the gate, the three curves, the budgets.
- `landing-page-design`, shipped with the plugin — the page system for a landing or marketing
  surface, loaded by `/design` after this skill; its canon yields to the contract above.
- Installed alongside, when present: `emil-design-eng` (the invisible details),
  `apple-design` (fluid interfaces, materials, the eight principles). Absent, say so; the contract
  above still holds.
