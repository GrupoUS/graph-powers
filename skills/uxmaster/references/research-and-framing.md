# Research & Framing

Research reduces uncertainty about people, situations, tasks, and consequences. It does not exist
to decorate a decision that has already been made.

## Frame the problem

Write the situation before the screen:

```md
User/context: [who, where, when, device, channel, constraints, risk]
Need/job: [what the person is trying to accomplish]
Current behavior: [what is observed, not what is assumed]
Desired outcome: [what success means to the person]
Business/system constraint: [what the product must also protect]
Unknowns: [questions that could change the decision]
```

Use observable tasks such as “compare two plans and understand the billing start date”, not vague
goals such as “make the experience delightful”. Include interruption, connectivity, privacy,
language, literacy, motor, sensory, cognitive, and emotional constraints when they affect the task.

## Turn uncertainty into questions

Choose the smallest method that can answer the question:

- **What happens now?** Observe the task, inspect support/contact reasons, or review existing evidence.
- **Why does it happen?** Interview, contextual inquiry, diary, or moderated usability research.
- **Can people do it?** Give representative participants a realistic task and observe success,
  hesitation, errors, workarounds, confidence, and recovery.
- **How common or different is it?** Use appropriately designed analytics, surveys, benchmarks, or
  experiments with a declared population, segment, window, and limitation.
- **Did the change cause an effect?** Define the comparison, primary metric, guardrails, and stopping
  rule before the test. Avoid claiming causality from a before/after coincidence.

Research should continue through discovery, definition, delivery, and live service. Include people
with disabilities in the relevant participant set and make the research itself accessible. Sample
size, cadence, and method are choices justified by the question, not universal rituals.

## Evidence ledger

Record each input with its source, scope, freshness, confidence, and limitation:

| Label | Meaning | Example wording |
|---|---|---|
| `observed` | Direct observation or measured behavior | “In five observed sessions…” |
| `reported` | User, support, stakeholder, or research report | “Participants described…” |
| `normative` | Standard, policy, or platform requirement | “WCAG 2.2 requires…” |
| `directional` | Relevant pattern with limited transferability | “A commercial study suggests…” |
| `hypothesis` | Proposed explanation or intervention | “We predict that…” |
| `assumption` | Needed to continue but not yet supported | “Until research confirms…” |

Never turn a directional pattern into a guarantee. Never invent users, percentages, baselines,
quotes, experiment results, or business impact. If the source is unavailable, say so and downgrade the
claim or remove it.

## Research output

End a research pass with:

1. decision-relevant findings and counterexamples;
2. unresolved questions and risks;
3. segments or contexts that may behave differently;
4. hypotheses ranked by user impact, confidence, and cost to learn;
5. the next research or validation activity;
6. what evidence would change the recommendation.

## Authorities and limits

- [ISO 9241-210:2019](https://www.iso.org/standard/77520.html) supports human-centred design
  principles and activities throughout the lifecycle. It is not a catalog of detailed methods.
- [GOV.UK user research guidance](https://www.gov.uk/service-manual/user-research/how-user-research-improves-service-design)
  emphasizes users' tasks, context, disabled users, whole journeys, and continuous research.
- [GOV.UK research planning](https://www.gov.uk/service-manual/user-research/plan-user-research-for-your-service)
  connects method choice to the question and phase; its example cadences are not universal rules.
- [W3C guidance on involving users](https://www.w3.org/WAI/planning/involving-users/) is a reminder
  that accessibility is stronger when disabled people participate in design and evaluation.
