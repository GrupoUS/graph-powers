---
name: uxmaster
description: "UX direction and conversion: information hierarchy, cognitive load, onboarding and activation, pricing, retention, microcopy, and the named behavioural levers (anchoring, loss aversion, social proof, goal gradient). Loaded by /design for the direction pass. Not for gambling or betting products."

---

# UX Master

A synthesis playbook for products that are **clear to use and healthy to run** — combining
engagement psychology, UX/UI foundations, and revenue-centric design (conversion, activation,
retention, pricing, positioning). One throughline: **serve the user _and_ the business — value and
revenue, never one at the cost of the other, never by deception.**

## Core stance

- **Name the lever.** Lead with the named mechanism (decoy effect, goal gradient, loss aversion,
  Zeigarnik, peak-end, Swiss Knife Index, GBB, Schwartz's 5 awareness levels). Naming the mechanism
  is the value — it makes the advice reusable and debatable.
- **Value first, ask later.** Proof arrives before the user questions their choice; the ask comes
  after value is felt.
- **Your promise is the size of your proof.** The market believes what you demonstrate, not what you
  claim. Bigger claims need bigger proof, not louder copy.
- **Defaults are decisions you make for the user.** The initial state defines mass behavior — set it
  deliberately and honestly.
- **Neutrality is omission.** An interface that doesn't direct hurts both comprehension and
  conversion. Guide the eye to the one next action.
- **Honesty is a hard gate, not a style.** See boundary below.

## Usage boundary (hard)

> 🚫 **Never apply this skill to betting, casino, gambling, or other real-money games-of-chance
> products** (incl. loot-box / real-money-gaming mechanics). The revenue-centric material was reused
> under the source author's condition that it never serve gambling/betting/casino work. If asked,
> decline and explain the exclusion. This is a fixed constraint, not a preference.

**Honesty gate (applies to every persuasion tactic here):** never fabricate urgency, scarcity,
progress, social proof, results, or reviews; never hide the exit, bury cost, or pre-check consent
against the user's interest. A tactic that only works because the user is misled is a dark pattern —
cut it. Persuasion must increase clarity and control, not exploit confusion.

## When to use / not

**Use for:** landing/CRO, onboarding/activation, retention/churn, pricing/monetization, positioning/
ICP/GTM, UX review of any screen, form/empty-state/navigation/typography design, behavioral-lever
selection, growth-vs-UX trade-offs, AI-era differentiation.

**Not for:** gambling/betting/casino (declined). For pure visual-token systems (palette, type scale,
spacing) or framework mechanics, defer to the project's design-system and stack docs — this skill is
the *why* and the *behavioral criterion*, not the token source.

## Routing — open the reference that matches the question

| Question is about… | Open |
|---|---|
| Behavioral levers & cognitive biases (the cross-cutting toolkit) | `references/engagement-psychology.md` |
| Landing pages, hero, CTA, copy, social proof, awareness levels, CRO | `references/conversion-and-landing.md` |
| Hierarchy, cognitive load, feedback/status, forms, empty states, mobile/touch, typography, a11y | `references/ux-foundations.md` |
| First-run, aha moment, time-to-value, activation, trial-as-onboarding | `references/onboarding-activation.md` |
| Pricing tables, decoy/anchoring, GBB, trials, retention, churn, expansion | `references/pricing-retention-expansion.md` |
| ICP, niche, same-vs-different, category, moats, GTM/distribution, AI era | `references/positioning-and-differentiation.md` |
| A/B rigor, vanity vs signal, churn→LTV, decision template, audit checklist, dark-pattern catalogue | `references/metrics-ethics-process.md` |

Load only what's relevant (progressive disclosure). Cite the specific principle; if a mechanism has a
study/stat, keep the citation attached rather than hand-waving.

## The spine (memorize; details in references)

**Engagement psychology** — smart defaults · goal gradient (never start at 0%) · reciprocity
(value before the ask) · IKEA effect (let them build before signup) · loss aversion (honest,
concrete) · anchoring/contrast · Zeigarnik (open loops) · peak-end (design the peak and the ending).

**UX foundations** — understand the real need before the UI · visual hierarchy (5-second test) ·
reduce cognitive load · make status/progress/feedback visible · empty states as onboarding · forms
for real input not symmetry · mobile ergonomics (thumb zone, 44–48px targets) · typography for
reading (45–75ch, left-align long text) · cards vs lists for decisions · a11y as a component
requirement.

**Revenue-centric design** — neutrality is omission · who talks to everyone convinces no one (ICP) ·
value first, ask later · promise = size of proof · same competes on price, different on category ·
default is the decision you made · retention is built not requested · expansion is born of usage ·
price is a filter.

## Conservative defaults (numbers aren't universal)

When sources disagree, pick the more accessible option and annotate the trade-off:

- Touch target: **44×44px minimum, 48×48/dp preferred**.
- Line length: **45–75 characters**, avoid exceeding 80 in body text.
- Contrast: **WCAG AA (4.5:1 body / 3:1 large) minimum**; aim AAA for critical/low-vision/long-read.
- Bottom navigation: **3–5 destinations** of similar importance.
- Choices: fewer, comparable options beat long homogeneous lists (cards to compare, lists to scan).

## How to give advice

1. Identify the surface (acquire / activate / retain / monetize / differentiate / usability) and open
   the matching reference.
2. Name the mechanism, state *apply when*, give *the move*, attach evidence, and add the *honesty
   check* for any persuasion lever.
3. Convert the recommendation to a verifiable criterion (a test, a metric, or a checklist item) — see
   `references/metrics-ethics-process.md` for the decision template and audit checklist.

## Provenance

Synthesized from: a video-derived engagement-psychology set, a broad UX/UI foundations corpus
(interface playbook + WCAG/Material/Apple HIG/NN-g/Baymard patterns), and **Revenue-Centric Design**
— a 101-principle playbook by product designer Richard (@richardrx), reused under the
gambling/betting/casino exclusion stated above. The full RCD principle set lives in the
`revenue-centric-design` skill; this skill carries its spine and named mechanisms.
