# Metrics, Ethics & Process

How to validate a design honestly, and the guardrails that bound every tactic in this skill.

## Ethics — the hard boundary

> 🚫 **Never apply this skill to gambling, betting, casino, or real-money games-of-chance products**
> (incl. loot-box / real-money-gaming). The revenue-centric material was reused under the source
> author's condition that it never serve such work. If asked, decline and explain the exclusion.

### Honesty gate (every persuasion tactic)

Persuasion must increase clarity and control, never exploit confusion. A tactic that only works
because the user is misled is a dark pattern — cut it.

### Dark-pattern catalogue (do not ship)

| Pattern | What it looks like |
|---|---|
| Fabricated urgency/scarcity | Fake countdowns, "only 2 left" that isn't true |
| Fake progress/results/reviews | Inflated meters, invented testimonials, phantom counts |
| Hidden costs / drip pricing | Fees revealed only at the end |
| Confirmshaming | Guilt-worded opt-outs ("No, I don't want to save money") |
| Roach motel | Easy to sign up, hard to cancel |
| Preselection against interest | Pre-checked add-ons, consent, or upsells |
| Disguised ads / trick questions | Ambiguous copy that misleads the click |
| Forced continuity | Silent charge after a trial with no clear notice |

Consequences before action; control and reversibility; exit as clear as entry; consent informed and
reversible. A reasonable person should understand the choice, its cost, and its alternatives without
being tricked.

## Measure signal, not vanity

- **Vanity metrics** (pageviews, raw signups, total users) feel good and decide nothing. **Signal
  metrics** tie to the job: activation rate, task success, retention cohort curves, NRR,
  conversion *quality*.
- Pair every metric with the decision it informs; if no decision changes, drop the metric.

## A/B testing rigor

- Decide the primary metric and minimum detectable effect *before* running; compute sample size.
- Don't peek-and-stop; run to the pre-set sample/duration to avoid false positives.
- One change per test when you need causality; ship only on a real, powered lift.
- Beware local maxima: some wins need a redesign, not a button-color test.

## Churn → LTV math (why retention dominates)

- LTV scales roughly with 1 / churn: dropping monthly churn from 5% to 3% lifts average lifetime
  from ~20 to ~33 months — a larger lever than most acquisition wins.
- Model retention before spending on acquisition; a leaky bucket makes paid growth unprofitable.

## Decision template (use for any meaningful design decision)

```md
## Decision: [name]
### Problem     — [user/business problem]
### Evidence    — research / analytics / support / benchmark
### Hypothesis  — If [change], then [impact], because [UX rationale + named mechanism]
### Alternatives— 1... 2... 3...
### Decision    — [what ships]
### Criteria    — [ ] usability [ ] a11y [ ] content [ ] responsiveness [ ] metric
### Validation  — success rate / time-on-task / error rate / churn / satisfaction
```

## Product audit checklist (by dimension)

- **Context:** objective sentence + success metric per key screen; ICP documented; evidence exists.
- **Hierarchy:** most-important element dominant; passes the 5-second test; one clear primary action.
- **Cognitive load:** no redundant steps/choices; recognition over recall.
- **States & feedback:** loading/empty/error/success/recovery all designed; progress shows real unit.
- **Forms:** labels near fields; width matches input; inline errors; visible focus; consent; minimal.
- **Mobile & touch:** targets ≥ 44×44 (pref. 48); thumb-zone CTAs; dangerous targets separated.
- **Typography:** long text left-aligned; 45–75ch; distinct weights; contrast ≥ AA; works at 200%.
- **Ethics:** zero fabricated urgency/scarcity/progress/results/reviews; exit clear; consent
  reversible; no confirmshaming or hidden cost.
- **Conversion:** message matches awareness level; proof sized to promise; one obvious next action.

## Recommended metrics

| Metric | Measures | When |
|---|---|---|
| Activation rate | Reached the aha moment | Onboarding |
| Task success rate | Completion | Any critical flow |
| Time-on-task | Efficiency | Before/after |
| Error rate | Clarity/tolerance | Forms, checkout |
| Retention / cohort curve | Stickiness | Ongoing |
| NRR | Expansion net of churn | Monetization |
| Trial→paid quality | Fit, not just rate | Trials |
| CSAT / post-task ease | Perceived ease | Surveys |
