# The house canon — upstream Part B, as a fallback

The visual system that `landing-page-design` shipped upstream, kept here with the reason beside
each value. It applies **only when no owner decided the axis**: the project declares no design
authority, and no `designer` direction contract exists. Even then each value is a proposal the
user confirms, never a rule applied silently — a canon that arrived in a plugin is still somebody
else's palette until the project adopts it.

Every rule carries one of two tags:

- **[craft]** — universal, harness-agnostic, holds in any project. Apply it.
- **[house]** — the upstream author's taste. Legitimate, opinionated, and a *fallback*. Where it
  coincides with a default in `designer`'s catalogue, the entry says so; the `designer` rewrite wins
  when the axis is free.

Read this after `SKILL.md § Precedence`, not before it.

## Typography

- **[house] Faces.** Geist, Manrope, Poppins; Geist Mono beside the primary face only for code, data
  and numeric UI where a monospace is functionally required. Upstream also banned Inter, Roboto,
  Arial, Open Sans and Helvetica. *Under this harness:* the project's face wins whatever it is —
  Inter included; the ban is a signal that no typographic decision was made, never a refusal of a
  declared token. When the axis is free, `designer` derives the face from the subject's world; its
  catalogue lists "Inter, Geist or the platform sans as the only face" as a tell, so this list is
  what to fall back on, not a decision.
- **[house] One typeface per site.** A second face needs a reason the subject supplies — the
  catalogue's "three families: the third always reads as an accident".
- **[house] No italic as emphasis; no 900 weights on body and UI text.** Emphasis from weight or
  size, capped at semibold or bold. Italic stays where the copy is genuinely a quotation, a title or
  a term — `<cite>`, `<em>` and a taxonomic name keep their meaning. A display face whose intended
  optical weight is heavier is the direction contract's call, not this rule's.
- **[craft] No orphaned words.** A single word never sits alone on the last line: `text-wrap:
  balance` on headings, `text-wrap: pretty` on body copy. Both are progressive enhancement:
  unsupported values fall back to normal wrapping. Chromium shipped `pretty` in Chrome 117
  ([Chrome](https://developer.chrome.com/blog/css-text-wrap-pretty)); Safari 26 ships its own
  implementation ([WebKit](https://webkit.org/blog/17333/webkit-features-in-safari-26-0/)).
- **[house] No hyphen as a dash.** Rewrite the phrase instead of reaching for `-` as punctuation in
  headings and labels. A compound word or a hyphenated product name keeps its hyphen — "read-only",
  "opt-in" — and a locale that hyphenates grammatically is not rewritten to satisfy an English
  copy-desk rule; orthography is the project's `project.locale`.
- **[craft] Every size lands on the project's type scale.** Never an arbitrary `text-[19px]`,
  `font-size: 22px` or `1.4rem`. When an existing size misses a step, snap to the **closest step
  below**, taking that step's paired line height with it. Tracking and leading then follow the
  catalogue's size-specific rule — tighten large text to about −0.02em, leave body near 0 — rather
  than freezing to the step; the freeze exists to guard against ad-hoc values, not against
  typography. The table below is Tailwind's default, which is the project's scale only when the
  project uses Tailwind without overriding `--text-*` (v4 writes the line heights as `calc()`
  expressions; the values are the same):

  | Class | Size | Line height |
  |---|---|---|
  | `text-xs` | 12px | 16px |
  | `text-sm` | 14px | 20px |
  | `text-base` | 16px | 24px |
  | `text-lg` | 18px | 28px |
  | `text-xl` | 20px | 28px |
  | `text-2xl` | 24px | 32px |
  | `text-3xl` | 30px | 36px |
  | `text-4xl` | 36px | 40px |
  | `text-5xl` | 48px | 1 |
  | `text-6xl` | 60px | 1 |
  | `text-7xl` | 72px | 1 |
  | `text-8xl` | 96px | 1 |
  | `text-9xl` | 128px | 1 |

  Line height 1 above `text-4xl` is for a one-line display; a two-line hero needs 1.05–1.15 or it
  collides with itself.

- **[house] Buttons.** Main buttons `text-base` semibold; smaller header buttons `text-sm`
  semibold, which yields to a project minimum font size when one is declared. Upstream's 8px
  vertical and 12px horizontal padding gives a 40px primary button — under the 44×44 touch target
  `uxmaster` holds and under most projects' declared minimum. Set `min-height` to the project's
  target, 44px when it declares none, and let the padding follow.

## Spacing

- **[craft] Only values from the scale.** Nothing between them, nothing outside them — an
  off-scale value is a rhythm nobody chose. A value off the grid needs its reason written beside it.
- **[house] The scale itself**, when the project declares none: 0 · 2 · 4 · 8 · 12 · 16 · 24 · 32
  · 40 · 48 · 64 · 80 · 96 px. Tailwind's 4px scale already contains every step.

## Corner radius

- **[craft] Nested radius formula.** When a shape sits inside another and the gap between them is
  under 32px: `inner radius = outer radius − gap`, applied only when the result is greater than 2;
  below that the inner shape stays square or unchanged. An outer card at 16px (`rounded-2xl`) with
  8px of padding gives the inner element 8px (`rounded-lg`). Concentric corners are what make
  nesting read as one object.
- **[house] Only the framework's radius steps** — the project's radius tokens when it has them.

## Borders and backgrounds

- **[craft] No coloured accent border on one side of a card, quote or callout.** The 3–4px
  `border-left` is the catalogue's most reliable code-side tell. A 1px hairline rule between
  sections, or under a sticky header, is a divider and stays legal — the catalogue's own rewrite
  prescribes it.
- **[house] Flat backgrounds, no gradients** — the default for a free axis, matching the catalogue's
  gradient row. A declared gradient surface token or a brief that pins one wins over it.
- **[house] Dark-mode backgrounds**, when the project has no dark tokens: `#000000` · `#181818` ·
  `#1F1F1F` · `#272727` · `#313131` · `#131209`. Propose, then tokenise as surface roles; a hex
  value pasted into a component is a token nobody can find later, and `#131209` is a warm
  near-black that will not sit in a neutral scale without being chosen.

## Hero

- **[craft] Measure.** Heading and subheading hold the 45–75 character measure `uxmaster` keeps for
  reading; wider lines lose the reader on the way back. Express it in `ch` against the project's
  scale. Upstream's 680px is that measure at the display step and at its face — 680px of 18px
  subheading already runs to about 80 characters, past the edge.
- **[craft] Line breaks at meaningful points.** Read the copy and break where the thought breaks;
  never mid-phrase. `text-wrap: balance` handles the even distribution; a manual break handles the
  meaning.
- **[house, catalogued default] Gradient on the heading text.** Dark theme `#FFFFFF → #9B9B9B`,
  light theme `#000000 → #666666`, left to right, text only. `designer` lists gradient text as
  "emphasis outsourced to a fill" and rewrites it as weight or size. It is allowed here only as the
  signature a direction contract chose on purpose, built from the project's text tokens rather than
  these two hexes; on a free axis it is not proposed.

## Icons

- **[craft] One library, one stroke weight.** Mixing grammars is what makes an icon set look
  assembled; Material Icons and Material Symbols mixed into any other set is the common case. The
  project's incumbent set stays unless the direction replaces it — a shadcn project carries lucide
  in every generated component, and swapping it rewrites every import for no gain a reader sees.
- **[house] Phosphor, Solar or Iconamoon**, when the project declares none.

## Motion — defer to `animate`

`animate` owns the curves, the duration budget and the recipes; nothing here overrides it. What
upstream specified, translated:

- **The curve.** Upstream's `cubic-bezier(0.32, 0.72, 0, 1)` is `animate`'s `--ease-drawer` token —
  one of three, assigned by situation: enter and exit take `--ease-out`, on-screen movement takes
  `--ease-in-out`. One curve for everything forks the project's `--ease-*` tokens, which `animate`
  calls a defect. Use the token name; a raw curve typed into a component is the "five hand-typed
  near-identical curves" consolidation finding waiting to happen.
- **`transition-all duration-700`** trips two rows of `animate`'s never-ship table: `transition:
  all` (name the properties), and UI over 300ms with no stated reason. Section-entry motion on a
  marketing page may run long; press and hover feedback take `animate`'s 100–160ms.
- **[craft] Scroll reveals** trigger with `IntersectionObserver` or Motion's `useInView` with
  `{ once: true }`, never an unthrottled `window.addEventListener('scroll')` — continuous reflow, and
  mobile pays for it. Fire once; re-animating on every scroll-by is a page fighting its reader.
  CSS scroll-driven animations (`animation-timeline: view()`) run on the compositor and ship in
  Chromium and Safari 26 — the observer stays the cross-browser baseline and the timeline is the
  progressive enhancement.
- **[house, catalogued default] The fade-up on every element** — `translate-y-16 blur-md opacity-0`
  resolving over 800ms as each element enters the viewport — is the catalogue's "same fade-up on
  every section: a page that moves everywhere moves nowhere", and `filter: blur` on every entering
  element is paint-heavy on the mid-range phones ad traffic arrives on. Replaced by one authored
  moment; the other sections are still on arrival, and the copy is readable at first paint.
- **[house, catalogued default] The fluid island nav.** A floating glass pill (`mt-6 mx-auto w-max
  rounded-full`), a hamburger whose lines rotate into an X (`rotate-45` / `-rotate-45`, absolutely
  positioned, never merely hidden — the morph is legible, a swap is a state change with no
  explanation), a screen-filling overlay (`backdrop-blur-3xl` over the project's overlay token,
  upstream's `bg-black/80` or `bg-white/80`), and links revealed from `translate-y-12 opacity-0` to
  `translate-y-0 opacity-100` staggered per item. Glass is the catalogue's "2022 effect that became
  the default material": translucency only where a layer really floats over scrolling content.
  Build it when the direction contract chose it, with the stagger at `animate`'s 30–80ms, and under
  `prefers-reduced-motion` the overlay cross-fades and the links appear in place — never slide.

## Tagline moment

Upstream section B11, mandatory there; here the candidate for the one signature `designer` allows,
placed after the hero or after the benefits as its own moment, never stacked directly under the
hero. Build it only when the direction contract named it.

- **Copy.** Minimum two lines. A benefit statement or tagline in the voice of `SKILL.md § A5`, not
  a section heading.
- **Type.** `text-4xl` to `text-6xl` by line count, on the project's scale; the same measure and
  meaningful breaks as the hero.
- **Reveal.** Words start muted and each transitions to the full text colour in reading order as it
  crosses a trigger line — one at a time, never the whole block at once. The resting state is the
  project's muted text token at **AA contrast for large text, 3:1 or better**, not upstream's 25–35%
  opacity: a word at 25% opacity sits near 1.5:1 and fails 1.4.3 for as long as it rests there,
  which is forever for a reader whose no-JS or reduced-motion path never activates it. Animate the
  delta from muted to full, or weight, never from invisible. `IntersectionObserver` per word, or one
  scroll handler throttled through `requestAnimationFrame`; the curve is `animate`'s `--ease-out`,
  never linear. Under `prefers-reduced-motion`, every word renders at full colour with no
  transition — the copy is the point, the reveal is the accent.

## The visual checklist, for a page with no design authority

- Single approved typeface; italic only where the copy is a quotation, title or term
- No orphaned words; sizes and spacing on the scale; buttons at the touch-target minimum
- Nested radii follow the formula
- No coloured one-sided accent borders, no background gradients on a free axis
- Hero heading and subheading inside the reading measure, broken where the thought breaks
- Icons from one library — the project's incumbent unless the direction replaced it
- Every transition names its properties and its curve token; reveals fire once, through the observer;
  reduced motion cross-fades
- One authored moment — the tagline reveal at AA-contrast rest, or something the subject supplied —
  or none
