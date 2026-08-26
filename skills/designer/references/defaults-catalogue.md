# The defaults catalogue

What a model draws when it is not deciding, axis by axis, with the tell a reader uses to spot it
and the rewrite that replaces it. Open this during move 5 of `designer` (the mirror), not before
move 2 — read first, it turns into a menu of things to avoid, and avoiding is not deciding.

Two measured facts frame the whole list:

- **Four or more of these on one surface and the surface is the template**, whatever else it does
  well. One is a choice; four is a distribution.
- **Typography is the highest-leverage axis.** Changing the face is an hour of work and the single
  move that shifts a surface furthest from the mode. Do it before touching colour or layout.

Every default here is legitimate when the brief asks for it. The failure is reaching for one when
the axis was free — and the fix is a rewrite from the subject's world, never a softened version of
the same default.

## Typography

| Default | The tell | The rewrite |
|---|---|---|
| Inter, Geist, or the platform sans as the only face | No typographic decision was made | One display face with a reason from the subject's world, one body face that reads at text size; source and self-host it |
| The recurring pairs: Space Grotesk + Instrument Serif, Playfair Display + any grotesk | The pair is recognised before the headline is read | Pair by the same designer or foundry (the most reliable heuristic), or by the same family at two optical sizes |
| Serif italic on one accent word per headline | A rhetorical tic, not a hierarchy | Emphasis from weight or size; italic only where the copy is actually a quotation, a title, or a term |
| One `letter-spacing` value for every size | Display too loose, small text too tight | Tracking is size-specific: tighten large text (to about −0.02em, floor −0.04em), leave body near 0, open captions slightly |
| A uniform type scale with no weight steps | Hierarchy carried by size alone, so every level looks like a bigger version of the last | Hierarchy comes from weight, size and leading moving together; an emphasised style is heavier and tighter, not only larger |
| Three families | The third always reads as an accident | Two at most; one when the subject's own artefacts use one |

Pairing heuristics that hold (Butterick, Google Fonts Knowledge): each face keeps one consistent
role; one face per paragraph; a lower contrast between the two faces is often stronger than a
serif-versus-sans split; faces with optical sizes cover display and text without a second family.

## Colour

| Default | The tell | The rewrite |
|---|---|---|
| Indigo-to-violet gradient on the hero, the primary button and the icons | The single most reliable tell — it propagates from the most-trained-on utility palettes | A palette derived from the subject: name the material, the place, the printed artefact, and take the values from it |
| Lavender or purple accent with no semantic role | Decoration standing in for a colour system | Accents used only where they mean something — action, status, progress, selection — never as fill |
| Tokens named `gradient-start` / `gradient-end` | The name records the decoration, not the intent | Semantic names: `--action`, `--surface-raised`, `--text-muted`; the value can be bold, the name says what it does |
| Near-black with grey body text under 4.5:1 | Dark mode chosen by category, legibility paid for it | Light or dark decided by where the surface is actually used — by whom, in what room, in what light — with secondary text tinted from the hue, never flat grey |
| Warm cream, high-contrast serif, terracotta button | The "editorial" AI look; fits any brief and therefore none | If the subject really is paper and ink, take the actual paper and the actual inks; if not, leave the axis to what the subject is made of |
| One flat brand colour with no scale | Every state improvised | A 5–10 step scale per hue from base, darkest and lightest anchors (Refactoring UI); generate it in OKLCH for perceptual consistency, then adjust by eye — the formula starts it, the eye finishes it |

Where the project already declares tokens, the palette question is closed: the direction assigns
roles to existing tokens and proposes any missing one by name. It never invents a value.

## Layout and structure

| Default | The tell | The rewrite |
|---|---|---|
| Centred hero: badge above H1, subtitle, two buttons, gradient glow | The layout every generator produces first | Lead with whatever is most itself about the subject — a headline, an image, a live demo, an artefact — in the form that thing naturally takes |
| The hero-metric block: big number, small label, three supporting stats | Numbers as decoration | A number only where the number is the claim, sized to what it proves, with the proof beside it |
| Three (or six) same-size cards: icon, heading, two lines | Cards are the lazy container; equal cards say every item is equally important, which is never true | Structure that encodes the content's real shape — a list when items are scanned, a comparison when they compete, prose when they are argued |
| A kicker or eyebrow above every heading, in all caps | Labels labelling labels | Delete it. The heading carries its own weight |
| `01 / 02 / 03` on content that is not a sequence | Order as costume | Number only a real process or timeline; otherwise the structure is a list, a grid, or a map |
| A 3–4px coloured `border-left` on cards, quotes, callouts | "As reliable a sign as em-dashes in text" | Separate with space, a change of surface, or a 1px rule from the palette |
| One radius for everything | Uniformity reads as unconsidered | Radius as a scale tied to size and role — or as a shape language, where the subject has one |
| Uniform padding and gaps on a 16px baseline everywhere | Same rhythm at every level, so no level reads as grouped | Members of a group sit close, groups sit apart, and a heading sits nearer to what it introduces than to what precedes it |
| Sidebar with emoji as icons | Glyphs standing in for a drawn system | Icons from one library or authored SVG, one stroke weight |

## Surface effects

| Default | The tell | The rewrite |
|---|---|---|
| Gradient text | Emphasis outsourced to a fill | Weight or size |
| Glass and blur as decoration | A 2022 effect that became the default material | Translucency only where a layer really floats over scrolling content, with the legibility rules that go with it |
| Soft coloured glow behind the hero | A halo with no light source | A shadow with an offset and a soft blur, or nothing |
| Hard offset shadow (`4px 4px 0`) | A neobrutalist costume on a world that did not choose it | Depth from the world the direction committed to |
| Monospace as the "technical" voice | A costume for code | Monospace for code, data and measurement only |
| Sparklines, progress rings, rounded rectangles as placeholder content | Chart-shaped decoration | Real content, or authored illustrative material labelled synthetic |
| Noise, grain, dither, "intentional imperfection" | The 2026 counter-default — as much a costume as glass when the world did not choose it | Earned only by a world that is actually printed, photographed, or hand-made |

## Motion

| Default | The tell | The rewrite |
|---|---|---|
| The same fade-up on every section | A page that moves everywhere moves nowhere; extra motion is itself a generated-feeling signal | One authored moment where the subject's meaning lives; sections otherwise still |
| Bounce or scale on every hover | Indiscriminate feedback trains people to ignore it | Feedback on press (scale about 0.97, on pointer-down), hover reserved for what is interactive, gated behind `(hover: hover) and (pointer: fine)` |
| Built-in `ease` / `ease-in` at 300–500ms | Sluggish; `ease-in` delays the frame the user watches most | Custom curves — strong ease-out `cubic-bezier(0.23, 1, 0.32, 1)`, ease-in-out `cubic-bezier(0.77, 0, 0.175, 1)` — and durations under 300ms for UI |
| Animating `width`, `height`, `background-color`, `box-shadow` | Jank under load | `transform` and `opacity`; blur, clip-path and mask when they stay smooth |
| Keyboard-initiated actions animated | Hundreds of times a day, each one slower | No animation on frequent, low-novelty actions |
| No `prefers-reduced-motion` branch | Vestibular harm, and a floor failure | Cross-fade instead of slide; keep opacity and colour changes that aid comprehension |

The depth for this axis is `emil-design-eng` (durations, easing, springs, the invisible details)
and `apple-design` (fluid, interruptible, velocity-aware motion; materials), when either is
installed. This table is the floor, not the craft.

## Copy

| Default | The tell | The rewrite |
|---|---|---|
| "Build the future", "Scale without limits", "Elevate your workflow", "Seamlessly", "Unlock" | A headline that could belong to anyone belongs to no one | Say what the product does, specifically enough that the reader knows what it is not |
| Feature triads with parallel verbs | The shape of copy, without the content | One claim per section, with its proof beside it |
| Marketing register on an Operate surface | A control that sells instead of naming its action | Controls say exactly what happens: "Save changes", not "Submit"; the same verb through the whole flow |
| Errors that apologise or stay vague | Mood instead of direction | Name the failure and the way out of it, in the product's voice, without apology |
| No voice | Averaged language | The founder test: would the person behind this product say the line out loud? If not, keep going |

## Imagery

| Default | The tell | The rewrite |
|---|---|---|
| Generated illustration with plastic sheen, perfect symmetry, uncanny lighting | Gradients that do not occur in real materials | Real photography of the real subject, or authored illustration in the direction's own grammar, labelled where synthetic |
| A geometric mask approximating a photographic edge | The cheap version of a cut-out | A real matte cut from the photograph itself, or no cut-out at all |
| Stock-photo people at laptops | Any product, any decade | The subject's own artefacts, instruments and places |

## The code-side tells

These are not aesthetics, and a reader still sees them: missing focus states, an empty state and an
error state that were never designed, dead utility classes, low-contrast placeholder text, a
hover effect on a card that is not a link. A surface with a distinctive direction and these gaps
reads as a costume on a skeleton. `/design § 4` and `§ 5` catch them; the direction pass names
the four states up front so they are designed, not patched.

## Sources measured against

- anthropics/skills `frontend-design` — the three AI looks, the two-pass plan, the signature,
  "remove one accessory"
- pbakaus/impeccable — its Refuse list, as one of the sources the tells were checked against
- emilkowalski/skills `emil-design-eng` and `apple-design` — motion values, typography by size,
  the eight principles
- Kosta Canatselis, *Spot the slop* — typography first; colour semantic, not decorative; the
  founder test
- Developers Digest, *16 patterns that out your app* — the coloured left border; the four-pattern
  threshold
- 925 Studios and SmoothUI on AI design slop — distributional convergence; one-shot generation as
  the root cause; iterate-until-pass
- Butterick, *Practical Typography — mixing fonts*; Google Fonts Knowledge — pairing heuristics,
  optical sizes
- Refactoring UI — palette from three anchors; Evil Martians — OKLCH; Radix Colors — the
  12-step semantic scale
- Linear brand guidelines — accents functional only; weight-forward type
- Material Design 3 Expressive — shape and motion physics as branding levers; emphasised type
- WCAG 2.2 — 1.4.3, 1.4.11, 2.5.8, 2.4.7, 2.4.11 at AA; 2.3.3 and 2.4.13 at AAA
- web.dev — compositor-only properties; `prefers-reduced-motion` with a 1ms duration, not zero,
  so `transitionend` still fires
