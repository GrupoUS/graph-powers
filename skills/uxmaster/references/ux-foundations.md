# UX Foundations

Usability foundations expressed as **criterion → application → acceptance evidence**. This reference
owns interaction behavior and accessibility, not visual identity or implementation tokens.

## Understand the task

- **Criterion:** the interface serves a real user, context, task, and expected result.
- **Apply:** write one observable task; list risk, device, connectivity, privacy, language, input,
  and accessibility constraints; research when the context is uncertain.
- **Accept:** a representative person can state what the surface is for, what to do next, and what
  success means.

## Make hierarchy serve comprehension

- **Criterion:** importance is understandable without decoration doing all the work.
- **Apply:** group related information, expose values and states, use meaningful labels, remove
  redundant choices, and keep one understandable next action where the task needs one.
- **Accept:** in a short glance or task attempt, users can identify purpose, current state, and next
  step; verify this with observation rather than a purely visual opinion.

## Reduce cognitive load

- **Criterion:** every step, choice, read, and click earns its place.
- **Apply:** prefer recognition over recall, split complex decisions by meaning, preserve context,
  expose consequential information, and remove steps that do not advance the user's job.
- **Accept:** users complete the task without needing to decode unexplained labels or reconstruct
  information from a previous step.

## Status, feedback, and control

- **Criterion:** the system is not silent while processing, waiting, failing, or completing.
- **Apply:** communicate status in plain language; expose real progress and units; provide cancel,
  back, retry, undo, save-and-return, or support where appropriate; make important status available
  to assistive technology.
- **Accept:** users know whether the system is alive, what changed, and what they can do next.

## Forms and input

- **Criterion:** a form helps people provide the smallest necessary information correctly.
- **Apply:** label fields programmatically and visibly, group by meaning, match input to expected
  precision, explain why sensitive data is needed, preserve entered values, and place correction
  guidance next to the relevant field and in a usable summary.
- **Accept:** users know what each field asks, why it is needed, how to correct it, and whether their
  previous work is safe.

## Mobile and touch

- **Criterion:** the task remains operable across hands, reach, precision, viewport, and input
  variation.
- **Apply:** test accidental taps, one-handed reach, keyboard, dynamic type, zoom, rotation, safe
  areas, interruptions, low connectivity, and assistive technology. Separate dangerous actions and
  preserve focus and context.
- **Accept:** representative users can operate the critical path without obstructive sticky controls,
  accidental destructive actions, or an inaccessible alternative.

Do not turn a platform recommendation into a universal accessibility norm. WCAG 2.2 Target Size
(Minimum) defines a 24×24 CSS pixel AA criterion with exceptions; Target Size (Enhanced) defines
44×44 CSS pixels at AAA. A product may choose 44 or 48 as a conservative design recommendation, but
the choice must be documented and tested for the actual control and context:

- [WCAG 2.2](https://www.w3.org/TR/WCAG22/)
- [Target Size (Minimum)](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum)
- [Target Size (Enhanced)](https://www.w3.org/WAI/WCAG22/Understanding/target-size-enhanced)

## Navigation and content

- **Criterion:** people know where they are and can move between meaningful areas.
- **Apply:** name destinations in user language, distinguish them from contextual actions, preserve
  location and filters, expose active state with more than color, and choose navigation density from
  the information architecture rather than a fixed destination count.
- **Accept:** users can enter, switch, return, and resume without a secondary memory task.

Content is behavior. Test headings, labels, instructions, legal text, error messages, and empty states
at realistic length, zoom, language, and device conditions. Do not prescribe a universal font count,
line length, color ratio, spacing grid, shadow, radius, or component library here; route those choices
to the project's design authority.

## Empty and failure states

Distinguish first use, no results, filtered-empty, unavailable, permission denied, offline, loading,
invalid, partial success, and system failure. Explain what happened, what remains true, and the safest
next action. Never erase work or create duplicate side effects during recovery.

## Accessibility is part of the component

Check the applicable standard and context for:

- semantic structure, names, roles, values, and status announcements;
- keyboard and alternative input, visible focus, target operability, and error recovery;
- contrast and non-color cues, zoom/reflow, text resizing, captions or alternatives;
- reduced motion and interruption tolerance;
- privacy, consent, language, cognitive load, and comprehension.

Include disabled people in research and evaluation where their needs are relevant. A checklist or
automated scan is evidence of some conditions, not proof that the task is usable.

## Sources

- [W3C Involving Users](https://www.w3.org/WAI/planning/involving-users/) supports involving people
  with disabilities in design and evaluation.
- [GOV.UK form structure](https://www.gov.uk/service-manual/design/form-structure) and the
  [validation pattern](https://design-system.service.gov.uk/patterns/validation/) illustrate clear
  labels, error recovery, preserved input, and separation of validation from eligibility.
