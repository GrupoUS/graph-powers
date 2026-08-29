# Metrics, Ethics & Process

Use evidence to make a decision, not to manufacture certainty after the decision. Pair user outcomes
with product outcomes and record the trade-offs.

## Ethics is a hard gate

Never apply this skill to betting, casino, gambling, loot boxes, or other real-money games of chance.
For all other products, persuasion must increase clarity and control.

Do not ship:

| Pattern | Diagnostic |
|---|---|
| Fabricated urgency or scarcity | Countdown, stock, or deadline is not real or is unverifiable |
| Fabricated proof | Reviews, results, user counts, logos, or progress are invented or inflated |
| Hidden cost | Fees, billing, limits, or consequences appear only after commitment |
| Confirmshaming | Opt-out is framed as guilt, insult, or fear |
| Roach motel | Entry is easy but cancellation, export, or exit is obstructed |
| Preselection against interest | Add-on, consent, upsell, or data sharing is selected by default without informed agreement |
| Disguised choice | Copy or layout makes one option look like something it is not |
| Forced continuity | Trial becomes a charge without clear terms, notice, and control |

Make consequences visible before action, keep consent informed and reversible, and make exit at least
as understandable as entry. See [OECD dark commercial patterns](https://www.oecd.org/en/publications/dark-commercial-patterns_44f5e846-en.html)
for a cross-market research reference; it is not legal advice.

## Evidence before recommendation

For each meaningful decision, record:

1. user outcome and business/system outcome;
2. source, scope, freshness, confidence, and limitation;
3. observed behavior versus reported opinion;
4. hypothesis and competing explanations;
5. segments or contexts that may differ;
6. validation method and the result that would change the decision.

An analytics number can reveal where behavior changes, not why. A heuristic can identify a risk, not
prove task success. An experiment can estimate an effect in its tested context, not guarantee transfer.

## Choose the validation method

- Use observation or usability research for comprehension, discoverability, error, recovery, and
  confidence.
- Use support, search, funnel, and event data to locate behavior, then investigate its cause.
- Use surveys for stated attitudes or prevalence with a declared population and limitation.
- Use benchmarks or experiments when the task, comparison, primary outcome, guardrails, sample,
  exposure, and stopping rule are defined before the run.
- Repeat comparable tasks when measuring change. Separate learning effects, seasonality, traffic mix,
  implementation changes, and other explanations from the intervention itself.

## Metrics that protect the user

Choose measures that can change a decision:

| User or system signal | Useful question |
|---|---|
| Task success | Can people complete the critical job? |
| Comprehension and confidence | Do they understand the choice and its consequence? |
| Time, hesitation, and error | Where does effort or recovery fail? |
| Abandonment and support need | Which step creates an avoidable dead end? |
| Accessibility outcomes | Can relevant users operate and understand the path? |
| Trust, cancellation, refund, complaint | Did the change create downstream surprise or harm? |
| Activation, retention, conversion, revenue, cost | Did the product outcome change without degrading user outcomes? |

Do not treat raw pageviews, signups, or conversion as proof of usability. A metric without a decision,
segment, window, and guardrail is a dashboard decoration.

## Decision record

```md
## Decision: [name]
### User task and context — [who, situation, risk, desired outcome]
### Evidence — [source, scope, limitation]
### Hypothesis — If [change], then [user outcome], because [reason]
### Business/system impact — [conditional outcome and trade-off]
### Alternatives — [options and rejected assumptions]
### Decision — [behavior or content that changes]
### Guardrails — [a11y, trust, privacy, error, exit, harm]
### Validation — [method, success criteria, segment, window]
```

## Audit checklist

- [ ] User, task, context, risk, and unknowns are explicit.
- [ ] Journey, adjacent steps, channels, and recovery are covered.
- [ ] Evidence, hypothesis, heuristic, and norm are labeled correctly.
- [ ] User outcomes are not hidden behind business metrics.
- [ ] Accessibility, privacy, consent, cost, reversibility, and exit are checked.
- [ ] The method fits the question and claims do not exceed the evidence.
- [ ] No fabricated proof, pressure, preselection, hidden cost, or cancellation maze exists.

## Sources

- [GOV.UK usability benchmarking](https://www.gov.uk/service-manual/measuring-success/usability-benchmarking-a-website-or-whole-service)
  recommends measuring task performance and repeating comparable tests.
- [GOV.UK measuring service success](https://www.gov.uk/service-manual/measuring-success/measuring-the-success-of-your-service)
  warns against relying on analytics alone and emphasizes end-to-end measurement.
- [W3C testing and evaluation](https://www.w3.org/WAI/test-evaluate/) separates evaluation activities
  and supports iterative evidence gathering.
