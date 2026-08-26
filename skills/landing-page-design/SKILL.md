---
name: landing-page-design
description: "Use when the surface is a landing or marketing page — building one, restructuring its sections, writing or rewriting the hero, headline or CTA, deciding whether a campaign page is indexed, or auditing one for filler and missing ship items. Trigger on: landing page, marketing page, campaign page, sales page, waitlist page, hero, headline, above the fold, CTA, conversion copy, FAQ section, noindex. Loaded by /design, only for a landing or marketing surface. Not for an app screen (designer), a motion value (animate), a lever inside the product (uxmaster) or a form that errors (/debug)."
---

# Landing Page Design

> Derived from `landing-page-design` in elayadesign/ai-design-skills (MIT, see the NOTICE at the
> root of the plugin). Adapted by GrupoUS: the page system — intake, section order, layout types,
> conversion and copy rules, build order, the index decision, the ship floor — is kept whole. The
> house visual canon (a font whitelist, hex backgrounds, an icon set, one curve, a mandatory
> reveal) moved to `references/house-canon.md` and became a fallback, because under this harness
> the project's design authority, the `designer` direction contract and the `animate` rulebook
> already own every value it hardcoded — and its upstream description claimed every web UI, which
> is the territory of three other skills.

## Overview

A landing page is not a homepage. A homepage serves several intents; a landing page wins one:
**one offer → one audience → one primary action.** Everything on the page advances that action or
is removed.

Two halves, in order. **Part A** decides what the page says, in what order, and whether search
should see it — this file. **Part B**, what it looks like, is decided upstream of this skill by the
owners in the precedence table; this file only says where the page's one authored moment goes.
Work through A before touching anything visual.

## When to use

- A landing, marketing, campaign, sales or waitlist page — new, or restructured.
- Hero, headline, subheadline, CTA or benefit copy for such a page.
- The index decision for a page: campaign or evergreen.
- An audit of an existing landing page for filler, dead states and missing ship items.

**Not** for an app screen, dashboard or settings surface (`designer` and its craft passes, through
`/design`); a motion value — curve, duration, reveal (`animate`); a behavioural lever inside the
product — onboarding, pricing, retention (`uxmaster`); a control that does not work (`/debug`); a
page that is slow, or its metadata and crawlability (`/perf`, `/perf seo`).

## Precedence — who owns which value

The upstream file hardcoded a palette, a font whitelist, an icon set and a curve. Under this
harness every one of those has an owner already, and a second source for the same value is how two
files stop agreeing.

| Axis | Owner | This skill |
|---|---|---|
| Palette, type, spacing, radius, icons | Root `DESIGN.md`, `${rulesDir}/design.md`, the project's tokens; then the `designer` direction contract | Uses them. A missing token is proposed by name, never invented |
| Motion | `animate` — the curves, the duration budget, the scroll-reveal recipe | Says where the one authored moment goes, and that everything else stays still |
| Conversion mechanism, awareness level, the honesty gate | `uxmaster`, its `references/conversion-and-landing.md` | Applies them to the section order and the copy |
| Craft passes on the built page | `designer`'s passes, through `/design § 3` | A6 is the drafting rhythm inside the first pass, not a second pass table |
| Metadata, structured data, crawlability | `/perf seo` | Makes the index decision (A7) and hands the rest over |
| Astro rendering and assets | The landing-page floor below; project rules for route and config decisions | Keeps the page static-first without turning design into framework architecture |
| Intake, section order, layout type, copy formulas, build order, the index decision, content realism, ship floor | **this skill** | — |

When no owner decided an axis — no design authority, no direction contract —
`references/house-canon.md` is the fallback: one documented canon with the reason beside each
value, offered as a proposal the user confirms, never applied silently. Several of its values are
catalogued defaults in `designer`; the reference says which.

## A1. Intake — one batch, then move

`designer` move 1 already grounded the subject, the audience, the scene and the design authority.
Do not ask those again. Gather what a landing page adds, in one batch, never one question at a time:

- **Purpose** — the ONE primary action (trial, demo, buy, waitlist, download); exactly what they
  get; what counts as a conversion (click, signup, purchase).
- **Objections and source** — the top three objections, which is why they do not convert today;
  the traffic source (ads, search, social, email); what they already know when they land.
- **Proof and assets** — logos, testimonials, numbers, case studies; screenshots, demo video,
  product GIFs; guarantees, refund and cancellation terms.
- **Constraints** — brand voice; mobile priority.

If the user cannot answer a strategy or copy question, make a reasonable assumption, state it in
one line, and continue — a stated assumption is reversible, a page that never started is not. The
licence stops at values: a missing token, a number, a customer, a claim is asked for, never
assumed. Those are `/design`'s stopping conditions and `uxmaster`'s honesty gate.

## A2. Page structure

**Above the fold — required.** 1 Headline: outcome plus audience. 2 Subheadline: how, with
specificity. 3 Primary CTA: verb plus what they get. 4 One proof signal: a logo strip, a number, a
short testimonial. 5 Hero visual: a product screenshot or video, or a strong illustration.

**Mid page — the argument.** 6 Problem to solution, one section. 7 Benefits, three to five,
outcome-driven. 8 How it works, three steps. 9 Social proof: testimonials or a case study.

**Bottom — objection handling.** 10 FAQ — one question per real objection; six to twelve is the
usual count, a convention rather than a measurement. 11 Risk reversal: trial, cancel anytime,
guarantee. 12 Final CTA, identical to the top one.

**The one authored moment.** Upstream made a large-type tagline section with a word-by-word scroll
reveal mandatory on every page. Here it is the *candidate* for the single signature that `designer`
rule 3 allows — spend boldness once — placed after the hero or after the benefits, and only when the
direction contract chose it. A page whose signature lives elsewhere does not get a second one. The
spec is `references/house-canon.md § Tagline moment`.

## A3. Layout selection — pick one and say why

| Type | Use when |
|---|---|
| **A. Classic hero plus sections** | The product is understandable from a hero screenshot. Most common |
| **B. Long-form story** | The reader needs educating, or skepticism needs overcoming |
| **C. Minimal conversion page** | High-intent traffic — email to known users — or a short offer: a download, a waitlist |
| **D. Comparison page** | Search intent includes alternatives ("X vs Y", "best for"); usually paired with SEO pages |

## A4. Conversion rules

The mechanism behind each rule — anchoring, loss aversion, social proof, the five awareness levels —
and the honesty gate that governs all of them live in `uxmaster`. This is their application to a
landing page.

- **Match message to source.** Ad traffic sees the ad's headline mirrored in the hero: the same
  promise, the same visual tone. A mismatch is the most common reason good copy fails.
- **Make the next step obvious.** One primary CTA. Never two competing CTAs above the fold — two
  loud buttons split intent.
- **Write benefit first.** Features are what it does; benefits are what that means for them.
- **Be specific.** Not "save time and streamline"; "cut weekly reporting from 4 hours to 15
  minutes". A number is a claim with its proof attached — and it comes from the user (A1).
- **Reduce risk.** At least one: free trial, free plan, no credit card, cancel anytime, money back.
- **Objections are a section, not a footnote.** Move the FAQ earlier for a high-friction offer. Put
  proof directly beside the claim it supports — where doubt spikes, near the CTA, near the price.

## A5. Copywriting

- **Headline formulas** — "{Outcome} without {pain}" · "The {category} for {audience}" · "Ship
  {result} in {time}".
- **Subheadline** — one or two sentences: what it is, who it is for.
- **CTA** — verb plus what they get: "Start free trial", "Book a demo", "Get the checklist". Never
  "Learn more" or "Submit".
- **Benefit bullets** — bold benefit, then the proof or the detail: **Faster iteration** — three
  layout variants in one click.
- **Register** — sentence case, not Title Case On Everything; active voice; no exclamation marks in
  success messages; no "Oops" in errors ("Connection failed. Try again."). The cliché list — the
  headline that belongs to anyone — is `designer`'s catalogue, Copy row; not restated here.

## A6. Build order

Hero → Benefits → How it works → Proof → FAQ → Final CTA. Section by section, never the whole page
per iteration: it keeps control and keeps the diffs reviewable. This is the drafting rhythm inside
the first `/design § 3` pass; the pass table there is the build sequence, and this order sits
inside it.

## Astro implementation floor — only when the stack is Astro

Astro delivers the approved direction; it does not choose a second one. Keep the page simple:

- Build sections as `.astro` components with semantic HTML and the project's CSS/tokens. Frontmatter
  prepares render-time data without shipping a client runtime. Prefer a native control such as
  `<details>` for an FAQ. Add a small local `<script>` only when a concrete interaction remains; a
  framework island must earn its client JavaScript with interaction those two cannot provide.
- Hydrate only that island: `client:load` for immediately visible, critical interaction;
  `client:visible` for below-fold interaction. Apply `client:*` directives to framework components,
  never `.astro` components. Do not add `client:only`, a client router, an adapter or server
  rendering unless a concrete requirement and the project's route doctrine call for it.
- Put local content images through `Image` or `Picture` from `astro:assets`. Choose a responsive
  `layout`, write accurate alt text (empty for decoration), mark only the actual hero LCP image
  `priority`, and leave below-fold images on the lazy default.
- Reuse the project's font pipeline and dependencies. Do not install a UI framework, motion library
  or Astro integration merely to make the page look polished; CSS and `.astro` are enough until a
  requirement proves otherwise.

Stop at this floor for an ordinary landing page. Deeper Astro API work and measured performance
audits belong to the owners named below.

## A7. The index decision

- **Do not index** ad-only campaign pages and time-bound offers: `noindex`, off the sitemap, no
  internal links pointing at it. A promo page that still ranks after the promo ended is a broken
  promise in the results. Google has to crawl the page to read the `noindex`, so this controls
  visibility, not crawl budget.
- **Do index** evergreen offers and pages where search intent matches the promise — with internal
  links from the homepage and the feature pages, and the FAQ written in plain question-and-answer
  form, the form answer engines lift.
- **What is not decided here.** Title and meta, `og:image`, structured data, crawlability belong to
  `/perf seo`. One fact for that handoff: Google deprecated FAQ rich results effective May 7, 2026
  ([official update](https://developers.google.com/search/updates)), so `FAQPage` markup is valid
  but buys no snippet — add it for machine readability, not for the result page.

## Ship floor

Universal craft from the upstream Part B, harness-agnostic: no other owner carries it, so it ships
with every page.

**Content realism** — the tells that a page was generated rather than made:

- No Lorem Ipsum: real draft copy on the first pass, because placeholder never gets replaced. No
  "John Doe": diverse, realistic names. No placeholder brands — "Acme", "Nexus", "SmartFlow" —
  invent contextual, believable ones.
- **Numbers are real or absent.** A round placeholder (`99.99%`, `50%`, `$100.00`) is a tell; a
  plausible invented one (`47.2%`) is fabricated proof, which is worse — the honesty gate. Take the
  value from the user, or label the content synthetic and keep it off the shipped page. The same
  for prices, customers, logos and results.
- Unique avatars per person; varied dates.

**States** — every interactive element ships hover (gated behind `(hover: hover) and (pointer:
fine)`, because touch fires a false hover on tap), active (`scale(0.97)` on pointer-down), a visible
focus ring, loading (skeletons shaped like the layout, not spinners), empty (a composed
getting-started view, never a blank panel), error (inline and specific, never `window.alert()`) and
full. No dead links: a button pointing at `#` is linked or visibly disabled. The current page is
indicated in the navigation.

**Ship requirements** — the landing-specific list that gets forgotten: privacy and terms links in
the footer; a branded 404; client-side validation for email format and required fields; cookie
consent where the jurisdiction requires it; a favicon; `og:image` and social tags; a way back from
every page. The accessibility floor — skip link, alt text, semantic landmarks, 4.5:1 body and 3:1
large text, 24×24 targets, focus visible, consistent help placement — is the safety floor's and
`designer`'s; a marketing page is not exempt from it, and this file does not restate it.

## Output format — before any code

The direction contract from `/design § 1` comes first; this outline is the page-level section of
that output, not a replacement for it.

1. **Page outline** — sections and their order (A2), with the authored moment placed or declined
2. **Hero copy** — headline, subheadline, CTA, proof line
3. **Benefits** — three to five, outcome-driven
4. **How it works** — three steps
5. **FAQ** — one question per real objection, with answers
6. **Index decision** — index or noindex and why (A7)
7. **Layout** — A, B, C or D, and why
8. **Values** — which owner each visual axis resolved to: authority, direction contract, or the
   fallback canon proposed for confirmation

Then build, section by section, per A6.

## Rationalisations

The thoughts that precede a weak page. Each has been observed; each is answered.

| Thought | Reality |
|---|---|
| "The homepage can do double duty" | A homepage serves several intents; a landing page wins one. Two intents on one page convert neither |
| "Two CTAs give people a choice" | Two loud buttons split intent. One primary; secondaries visibly lower |
| "The visitor will work out the offer" | The five-second test: what is this, who is it for, why different, what next — above the fold |
| "Streamline, seamless, elevate sound professional" | They belong to every product and therefore to none. Say what it does, specifically |
| "Proof goes in a logo strip at the bottom" | Proof sits beside the claim it supports, where doubt spikes |
| "A specific number reads better — 47.2%" | An invented specific number is fabricated proof. Real, or absent |
| "Index everything — more pages, more traffic" | A campaign page that ranks after the campaign is a broken promise. `noindex` |
| "Upstream said Geist and Phosphor" | Upstream had no project to defer to. Here the project's tokens win; the canon is a proposal |
| "Every section should fade up on scroll" | A page that moves everywhere moves nowhere. One authored moment; the rest still |
| "Lorem for now, real copy later" | Placeholder ships. Real draft copy on the first pass |
| "Mobile can come after" | Ad and social traffic is mostly mobile; a hero that breaks on a phone is the first impression |

## Quick checklist

Pointers, not a second statement of the rules — a checklist that restates a value is a second copy
that drifts.

- A1 intake answered or assumed out loud; no value assumed
- A2 order held, the authored moment placed once or declined
- A3 type chosen with the reason written down
- A4 all six rules, in particular message matched to source and one primary CTA
- A5 headline formula, CTA shape, register
- Astro stack: the implementation floor applied; deeper work escalated only when required
- A7 index decision made and stated
- Ship floor: content realism, seven states, the landing-specific ship list
- Output format returned before code; every visual axis resolved to its owner

## Where the depth lives

Do not restate these here; open them when the step calls for them.

- `references/house-canon.md` — the upstream visual canon with the reason for each value, flagged
  universal craft or house taste; the tagline moment spec.
- `${CLAUDE_PLUGIN_ROOT}/skills/uxmaster/references/conversion-and-landing.md` — awareness levels,
  promise equals the size of the proof, proof placement, the honesty gate.
- `${CLAUDE_PLUGIN_ROOT}/skills/animate/references/recipes.md`, the scroll-reveal recipe — the one
  reveal, marketing only, fired once.
- `${CLAUDE_PLUGIN_ROOT}/skills/designer/references/defaults-catalogue.md` — the tells the canon's
  own values trip: gradient text, glass as decoration, the fade-up on every section; and the Copy
  row this file's register rule points at.
- [Astro's official documentation](https://docs.astro.build/) — consult only when a concrete
  framework feature exceeds the floor above; do not preload a general framework manual.
- `/perf` — open for a measured performance, bundle, Core Web Vitals or SEO audit; this floor does
  not invent budgets.
