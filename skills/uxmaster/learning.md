# UXmaster Learning

## Authoring contract

UXmaster must begin with need, context, task, and journey. Commercial and psychological mechanisms
are conditional lenses, not the spine. Every recommendation labels its evidence, hypothesis,
heuristic, or norm and states how it can be validated.

## Baseline RED

The representative mobile ecommerce case was run against the previous skill before the rewrite:

- 3/6 assertions passed;
- 3 critical assertions failed;
- missing behavior: context/task framing, distinction between unit price and total, and
  uncertainty/state/recovery coverage.

The baseline response was temporary and was not retained as a shipped artifact.

## GREEN result

The rewritten skill was checked with 11 cases and 39 objective assertions at threshold `1.0`:

- 4 positive behavior cases passed;
- 7 routing-boundary cases passed;
- 39/39 assertions passed with zero critical failures.

The 20 mixed trigger queries are retained in `evals/evals.json` as a calibration corpus because the
repository runner evaluates response assertions, not description classification directly.

## Changes made

- Added canonical references for research/framing, journeys/flows/information, and ecommerce/product
  experience.
- Refactored the existing references to remove unsupported universal numbers and visual-system rules.
- Corrected the WCAG target-size distinction: 24×24 CSS pixels for the AA minimum criterion with
  exceptions, versus 44×44 CSS pixels for the AAA enhanced criterion.
- Added explicit boundaries between UX direction, visual direction, implemented UI repair,
  implementation, debugging, performance, motion, and landing-page systems.
- Added behavior and trigger evaluations, with negative cases at the routing borders.

## Future calibration

After each material change, run the behavior suite at threshold `1.0`, review the 20 mixed trigger
queries, and record false positives, false negatives, evidence changes, and any new duplicated rule
in this file. Do not preserve a rule merely because it sounds senior or improves a business metric.
