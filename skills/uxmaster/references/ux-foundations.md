# UX/UI Foundations

Usability fundamentals. Each: **rule → how to apply → acceptance criterion.**

## Understand the real need before the interface

- **Rule:** no visual decision without clarity on user, context, task, and expected result.
- **Apply:** write the task in observable language ("track an order"); list constraints (device,
  connectivity, a11y, privacy, risk); do light research if there's no data.
- **Accept:** every important screen has one objective sentence + one success metric.

## Visual hierarchy — the 5-second test

- **Rule:** the most important element for the task must *look* the most important.
- **Apply:** use size, weight, contrast, color, position, space, grouping; emphasize
  **values/states/actions**, not generic labels; remove borders/shadows/icons without function;
  replace passive text ("processing") with an actionable visualization (stepper, progress, map).
- **Accept:** in a 5-second glance, users identify the screen's purpose and the primary action.

## Reduce cognitive load

- **Rule:** every step, choice, read, and click must justify itself.
- **Apply:** expose value without unnecessary intermediate clicks; recognition over recall; split
  complex decisions into semantic groups; delete redundant options.
- **Accept:** the user advances without asking "what does this mean?" / "where do I click?".

## Make status, progress, and feedback visible

- **Rule:** the system is never silent while processing, waiting, failing, or completing.
- **Apply:** progress bar/stepper/counter/skeleton/short log; state the **unit** (%, time, steps,
  items, queue position); always offer recovery (cancel, retry, undo, back, save draft); important
  status must be programmatically perceivable by screen readers.
- **Accept:** for any wait beyond a few seconds, the user knows the system is alive and what to do if
  it stalls.

## Empty states as onboarding

- **Rule:** an empty state is a functional state, not a hole.
- **Apply:** distinguish first-use vs no-results vs no-match vs error vs cleared list; specific
  microcopy ("You haven't created any projects yet" > "No data"); one relevant CTA
  (create/import/invite/clear filter/explore); illustration only if it adds context.
- **Accept:** the user understands *why* it's empty and *what* the next step is.

## Forms for real input, not symmetry

- **Rule:** a good form helps the user fill it correctly.
- **Apply:** label near its field (label–field gap < gap between groups); group by subject
  (expiry+CVC, city+state); **width matches expected input** (postcode ≠ card number); mask as a
  complement, not a label replacement; inline error next to the field; visible focus; **preview when
  the form produces a visual result**.
- **Accept:** the user knows what each field asks, why, and how to fix errors. Collect only what the
  next step needs; consent where personal data is involved.

## Mobile ergonomics — thumb, touch, motor a11y

- **Rule:** respect the hand, reach, mis-taps, and motor variation.
- **Apply:** touch target **44×44 min, 48×48/dp preferred**; tappable area larger than the visual
  icon; frequent actions in the thumb zone; separate dangerous targets (delete vs confirm); avoid
  controls in extreme corners.
- **Accept:** operable one-handed, lightly moving, without frequent accidental taps.

## Navigation & bottom bars

- **Rule:** global nav is a compact set of destinations, not a dumping ground.
- **Apply:** **3–5 destinations** of similar importance; destinations (areas), not contextual
  actions; short labels + familiar icons; active state with **≥ 2 cues** (fill/outline + color/
  weight/indicator — never color alone); badges only for meaningful signals; keep the bar stable and
  visually separated from content.
- **Accept:** users know where they are and switch areas without a secondary menu.

## Typography & reading

- **Rule:** text is interface; if reading takes effort, the UI fails.
- **Apply:** coherent scale (title/subtitle/body/caption/CTA distinct by weight/size/contrast);
  **line length 45–75ch** (max ~80) via `max-width`; **long text (>3 lines) left-aligned**; center
  only hero/headline/short phrase; never center instructional/legal/error text; comfortable
  line-height; contrast ≥ 4.5:1 (AA), higher for small/critical text.
- **Accept:** critical content readable at 100% and 200% zoom, on mobile and desktop.

## Cards, dropdowns & lists — support the decision

- **Rule:** a visual choice should reduce comparison, not add distraction.
- **Apply:** **cards** for few options with comparable attributes (price/benefit/limit/recommended/
  selected state); **lists** for many homogeneous options; dropdowns grouped by category with
  consistent icons; images only when they add meaning; preserve radio/checkbox semantics even when
  styled as cards; never bias toward the most profitable option by visual trick.
- **Accept:** the user compares quickly and can explain why they chose.

## Accessibility as a component requirement

- **Rule:** a11y is a component requirement, not a final step.
- **Apply:** color tokens with validated contrast; documented minimum target size; visible focus;
  **color is never the only indicator**; programmatic labels on inputs; status perceivable by
  assistive tech; test keyboard, screen reader, zoom, contrast, and **reduced motion**.
- **Accept:** main components pass applicable WCAG AA before production.

## Design for failure (senior maturity)

- **Rule:** maturity = framing the problem, deciding with evidence, communicating trade-offs, and
  measuring — not "making it pretty".
- **Apply:** start from the problem, not the screen; justify by impact (clarity/a11y/cost/
  maintenance/goal), not taste; think in systems (components/tokens/states/docs); design every state
  (empty/loading/error/retry/denied-permission/low-connection/invalid-input).
- **Accept:** components carry default/hover/focus/active/disabled/error/loading/success + usability
  and a11y acceptance criteria.

## Conservative numbers when sources disagree

| Topic | Recommendation |
|---|---|
| Touch target | 44×44 absolute min, 48×48/dp preferred |
| Line length | 45–75ch; avoid exceeding 80ch in body |
| Contrast | AA (4.5:1 / 3:1) min; AAA for critical/low-vision/long-read |
| Bottom nav | 3–5 primary destinations |
| Cards vs lists | Cards for few comparable options; lists for many homogeneous |
