# Journeys, Flows & Information

The unit of UX work is the user's progress through a task, not the isolated screen.

## Start with the journey

Map the step before and after the requested surface:

```text
trigger → expectation → entry → orientation → task steps → decision/action
        → feedback → outcome → follow-up, support, or return
```

For each step, record the user's goal, information needed, action, system response, uncertainty,
handoff, and recovery path. Include web, app, email, notification, human support, and operational
channels when the experience crosses them. A polished screen cannot repair a broken handoff or an
unexplained wait elsewhere in the journey.

## Model information architecture

- Name areas by the user's language and mental model.
- Separate destinations from contextual actions.
- Expose information needed for the next decision; do not hide consequential facts behind extra taps.
- Use search, categories, filters, lists, or comparison cards according to the information shape:
  recognition and scanning for many homogeneous items; structured comparison for a small set of
  meaningful alternatives.
- Preserve location, selected filters, entered data, and return path when moving between steps.
- Treat labels, content, empty states, permissions, and errors as part of the information architecture.

Do not infer that a shorter path is better if it removes explanation, control, or recoverability.

## Design the flow before the screen

Specify:

1. entry conditions and prior knowledge;
2. the primary task and acceptable alternatives;
3. required versus optional information;
4. branches, dependencies, and irreversible actions;
5. visible feedback and system status;
6. interruption, save-and-return, back, cancel, undo, retry, and support;
7. completion evidence and the next meaningful step.

For new, returning, and expert users, adapt guidance and density only when the difference is supported
by context or evidence. Do not personalize consequential choices invisibly.

## States and recovery

Specify the state machine in plain language. At minimum ask whether the task needs:

- first use, existing content, no result, filtered-empty, loading, slow, offline, stale, permission
  denied, invalid input, unavailable item, partial success, success, cancellation, and failure;
- a clear message about what happened, what remains true, and what the user can do next;
- preservation of work and focus position after an error or return;
- a safe alternative when the preferred input or channel is unavailable.

An error is part of the flow, not a red paragraph added at the end. A recovery action must not erase
work or create a duplicate transaction without explanation.

## Mobile context

Check one-handed reach, accidental taps, input precision, keyboard and assistive technology, dynamic
type, rotation, safe areas, interruptions, and variable connectivity. A bottom action, sticky action,
slider, wheel, preset, search suggestion, order timeline, or category card is a candidate pattern,
not a requirement. Test whether it preserves content, focus, comparison, and exit on the actual
viewport and input method.

Choose input by task characteristics: selection can accelerate common, low-risk choices; manual input
is necessary for uncommon, precise, or unrepresented values. Always provide a comprehensible fallback.

## Acceptance questions

- Can a first-time user state the purpose and next step?
- Can a returning user resume without reconstructing context?
- Can a person see where they are, what changed, and what happens next?
- Can they recover from error, interruption, denial, and low connectivity?
- Does the flow preserve control, data, privacy, and an understandable exit?
- Are the critical tasks testable with representative users, including disabled users?

## Sources

- [GOV.UK whole-problem mapping](https://www.gov.uk/service-manual/design/map-a-users-whole-problem)
  and [experience mapping](https://www.gov.uk/service-manual/user-research/creating-an-experience-map)
  support looking beyond a single transaction or screen.
- [GOV.UK Service Standard](https://www.gov.uk/service-manual/service-standard) emphasizes user
  needs, joined-up channels, simplicity, accessibility, iteration, and measurable success.
