---
paths:
  - "${rulesDir}/ux.md"
---

# UX — behaviour, not appearance

> Graph Powers template. The self-referencing `paths:` is deliberate: this rule loads when someone
> cites it, not on every interface edit. It is about flow and decisions, not pixels.

## The honesty gate `[HARD]`

Canonical in root `PRODUCT.md § The honesty gate`; repeated here because this is the rule that loads
when someone is about to ship a flow. If the two ever disagree, `PRODUCT.md` wins.

These do not bend, and they come before any conversion target:

- **No false urgency.** A counter that resets, "only 2 left" that is not true, "offer ends today"
  that does not end.
- **Consent is not pre-checked.** Opt-in is the user's action.
- **The exit is visible.** Cancel, close and back exist and are findable.
- **The total cost appears before the commitment**, not at the last step.
- **No pattern that depends on the user not noticing** in order to work.

If a conversion technique needs the person not to notice, it does not go in. This is not abstract
ethics: it is what separates a metric that holds from one that collapses when the user works it out.

## Flow

- **First use shows value before asking for data.** Every field before the first benefit costs
  people.
- **The empty state teaches.** It is the new user's first screen and the most neglected one.
- **A long form is split, with visible progress** and goes back without losing what was typed.
- **A destructive action confirms; a reversible one does not.** Confirming everything trains people
  to click without reading.
- **An error says what to do**, not what happened. "Validation failed" helps nobody.

## Cognitive load

- One decision per screen when the decision matters.
- A smart default beats one more option.
- What the person already answered is not asked again.

## Review

Before shipping a flow change, answer: **what does this screen ask for, what does it give back, and
what happens if the person abandons it halfway?** All three need an answer.

{{UX_PROJECT_NOTES}}
