---
name: uxmaster
description: "Use when a product, flow, onboarding, form, navigation, ecommerce journey, or conversion decision needs user-centered UX direction, diagnosis, or validation. Trigger on user needs, task flows, information architecture, interaction states, accessibility, trust, research, usability evidence, and outcome metrics; route visual styling to designer and implemented UI repair to design-fix."
---

# UXmaster

UX direction for decisions that affect what people understand, do, feel, and can recover from.
Start with the user's situation and task. Only then connect the experience to product outcomes.

## Boundary

UXmaster owns user needs, context, tasks, journeys, information architecture, interaction behavior,
content clarity, states, recovery, accessibility, trust, research, heuristic diagnosis, validation,
and conditional product/ecommerce/conversion decisions.

It does not own visual identity, tokens, component code, browser performance, motion engineering, or
the construction of a landing-page system. Route those decisions to `designer`, `design-fix`, the
relevant implementation agent, `performance`, `animate`, or `landing-page-design`.

Never apply this skill to betting, casino, gambling, loot boxes, or other real-money games of chance.
If asked, decline. The honesty gate is universal: never fabricate urgency, scarcity, progress, proof,
reviews, results, or consent; never hide cost or make exit harder than entry.

## The UX spine

Work through this sequence, adapting depth to the risk and uncertainty:

1. **Need and context** — identify the person, situation, constraints, motivation, risk, device,
   channel, and desired outcome. State what is known, assumed, and unknown.
2. **Task and journey** — express the job in observable terms, map the journey before and after the
   focal screen, and include handoffs between channels, people, and systems.
3. **Information and interaction** — decide what must be visible, grouped, searchable, selectable,
   entered, confirmed, or deferred. Make the next meaningful action understandable.
4. **States and recovery** — cover default, loading, empty, no-result, invalid, denied, offline,
   permission, success, cancellation, retry, undo, save-and-return, and partial completion where
   relevant.
5. **Accessibility and trust** — include disabled participants and assistive technology in the
   research plan; check perceivability, operability, comprehension, privacy, consent, cost, control,
   and reversibility.
6. **Evidence and validation** — distinguish evidence from hypothesis, choose a method that answers
   the question, record limitations, and define how task success and unintended harm will be observed.
7. **Product impact** — connect user outcomes to activation, conversion, retention, revenue, cost, or
   risk only after the experience logic is clear. Never treat business impact as proof of usability.

## Vocabulary that prevents overclaiming

- **Evidence:** an observation, user report, support pattern, measured behavior, experiment, or
  authoritative requirement with a source, scope, and limitation.
- **Hypothesis:** a proposed explanation or change that still needs validation. Label assumptions and
  predicted effects explicitly.
- **Heuristic:** a useful diagnostic lens, such as recognition over recall. It is not a compliance
  verdict or a substitute for observing users.
- **Norm:** a requirement from a standard, policy, platform, or law. Cite the applicable scope and
  version; do not turn a recommendation into a universal minimum.
- **User outcome vs business outcome:** task success, comprehension, confidence, and control are
  user outcomes; signups, revenue, retention, and support cost are business outcomes. Measure both
  when relevant, without letting the latter hide harm to the former.
- **Aesthetic improvement vs usability improvement:** visual polish may support comprehension, but it
  is not evidence that people can complete a task more successfully.

## Mobile and responsive lens

Treat a mobile screen as one point in a journey, not an isolated composition. Check reach, input
precision, interruption, connectivity, viewport changes, assistive technology, and the relationship
between the previous and next step. A thumb-zone action, sticky action, preset, timeline, search
suggestion, or personalization pattern is a context-dependent hypothesis: test obstruction, focus,
reflow, choice quality, and recovery before standardizing it.

Use real and variable content when reasoning about hierarchy. For commerce and other consequential
decisions, expose the unit, quantity, uncertainty, total, terms, and next consequence near the choice.
Do not import fixed font counts, spacing grids, color ratios, framework classes, or animation recipes
from a visual implementation guide into this UX method.

## Conditional product lenses

After the spine is established, select only the relevant lens:

- **Research and framing:** turn uncertainty into questions and a proportionate research plan.
- **Journeys, flows, and information:** model navigation, continuity, branching, states, and recovery.
- **Ecommerce/product experience:** support comparison and confident decisions with honest product data.
- **Onboarding/activation:** reach first value without unnecessary gates, tours, or invented progress.
- **Conversion/landing:** align message, proof, action, and friction without manipulation; defer page
  system and visual direction to the owning skills.
- **Pricing/retention/expansion:** make value, limits, billing, cancellation, and upgrade context clear.
- **Positioning/differentiation:** connect a real user problem to a specific audience and credible
  difference.
- **Engagement psychology:** use a named mechanism only when it serves a real user need and remains
  reversible, transparent, and testable.
- **Metrics/ethics/process:** choose measures, guardrails, research methods, and decision records.

## Routing

| Question | Reference |
|---|---|
| Needs, context, research, participants, assumptions, evidence | `references/research-and-framing.md` |
| Tasks, journeys, navigation, IA, flows, states, recovery, mobile context | `references/journeys-flows-and-information.md` |
| Product detail, variable quantity, ecommerce decisions, trust | `references/ecommerce-product-experience.md` |
| Interaction, forms, feedback, empty states, accessibility | `references/ux-foundations.md` |
| Measurement, validation, ethics, dark patterns, decision records | `references/metrics-ethics-process.md` |
| Behavioral mechanisms and their honesty checks | `references/engagement-psychology.md` |
| First-run value and activation | `references/onboarding-activation.md` |
| Message, proof, CTA, CRO boundaries | `references/conversion-and-landing.md` |
| Pricing, cancellation, retention, expansion | `references/pricing-retention-expansion.md` |
| ICP, category, differentiation, distribution | `references/positioning-and-differentiation.md` |

Open only the relevant references. Do not duplicate a definition when a reference already owns it.

## Advice contract

Return a decision that can be inspected:

1. Context, user, task, risk, and unknowns.
2. Journey or flow impact, including adjacent steps and channels.
3. UX diagnosis and the evidence or heuristic behind it.
4. Recommended behavior, content, states, and recovery.
5. Accessibility, trust, privacy, and autonomy checks.
6. Hypotheses, alternatives, validation method, success criteria, and guardrails.
7. Expected user impact, then conditional product impact.

For every persuasion or growth recommendation, name the mechanism, say when it applies, show the
honest alternative, and state what would falsify the recommendation.

## Provenance

This is a source-informed synthesis for Graph Powers. The mobile UX additions were adapted from
GrupoUS/neondash, `.claude/skills/mobile-app-ui-design/SKILL.md`, commit `9a3fd3a36`; task/context,
journey, state, input, search, selection, and variable-content ideas were retained, while visual
tokens, framework instructions, and universal claims were excluded. The adaptation is recorded in
the repository notice. External standards and guidance remain linked at the point where they shape a
claim; the source ledger is in `references/research-and-framing.md`.
