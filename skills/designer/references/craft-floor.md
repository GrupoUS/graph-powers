# The craft floor

What every craft pass in `craft-passes.md` is measured against, on the built result — not on the
intention. Open it once the direction is settled and the first edit is next; opened while planning
it becomes a list to recite, and the floor is meant to be silent. Where it disagrees with the
direction contract or the project's design rule, those win; where it disagrees with a habit, it
wins.

## Contrast and colour

- Body and placeholder text at or above 4.5:1; large text (24px, or 18.7px bold) and the visible
  parts of controls at or above 3:1 (WCAG 2.2 1.4.3, 1.4.11). Measure the computed colours, not
  the token names.
- On a coloured surface, secondary text takes its tint from that surface's hue or from the
  foreground colour; a neutral grey laid over colour reads as dirt.
- Colour is never the only carrier of a state: pair it with shape, icon, weight or text.
- Accents appear only where they mean something — action, status, selection, the signature —
  and nowhere as fill. Count the places the accent appears; more than four on one viewport is
  decoration.

## Type

- Body measure 45–75 characters; the project's rule may narrow it, never widen it past 80.
- Tracking is size-specific: display text tightened (about −0.02em, floor −0.04em), body near 0,
  captions opened slightly. One `letter-spacing` value for every size is wrong somewhere.
- Leading tracks size inversely: tight on display (about 1.05–1.15), comfortable on body
  (about 1.5), tighter again in dense data.
- Hierarchy is built from weight + size + leading as a set. Two adjacent levels that differ only
  in size read as the same level.
- Nothing below the project's minimum size at any viewport; every heading balanced (`text-wrap:
  balance`) and every paragraph free of a single-word last line where the platform supports it.
- Numbers compared in a column use `font-variant-numeric: tabular-nums`.
- Check with the actual strings, at each width the surface ships to. Overflow, an orphaned label
  and a headline broken into one word per line are floor failures, not polish.

## Space and depth

- One spacing scale, the project's. A value off it needs a reason written in the code.
- Members of a group sit close and groups sit apart; a heading belongs to what follows it, so the
  gap above it is larger than the gap below. Measure the rendered margins, not the class list.
- A shadow has a direction and a soft edge, and the same kind of surface casts the same shadow
  everywhere. A coloured glow with no offset is a halo, not elevation.
- Radius follows a scale tied to size and role. A single radius on every element is unconsidered;
  a nested element's radius is its parent's minus the padding.

## Targets, focus and keyboard

- Pointer targets at least 24×24 CSS px (2.5.8); on touch, the project's minimum, and never
  under 44×44 for a control that is pressed by thumb.
- `:focus-visible` with a visible ring from the palette, 2px, offset, never obscured by sticky
  chrome (2.4.7, 2.4.11). Removing the ring without replacing it breaks keyboard navigation.
- A button is a `<button>`, a link is an `<a>`; the Tab order is the reading order; every
  interactive element has an accessible name.

## Motion

- One authored moment, not the same entrance on every section. What animates and what never does
  is the contract's `Motion` line; the values are the `animate` skill's, never approximated.
- `transform` and `opacity` first; blur, clip-path, mask and shadow only where they stay smooth.
  Never `width`, `height`, `top`, `margin`.
- Press feedback on pointer-down, scale about 0.97, 100–160ms, strong ease-out. Hover gated
  behind `(hover: hover) and (pointer: fine)`.
- Nothing animates on a keyboard-initiated or hundred-times-a-day action.
- `prefers-reduced-motion: reduce` ships with the motion: cross-fade instead of slide, no
  overshoot, a duration near 1ms rather than 0 so `transitionend` still fires.

## States and content

- Every surface that fetches data has four states designed and reachable: loading (layout keeps
  its height), empty (one sentence and the action), error (what went wrong and the recovery),
  populated. Plus hover, focus, active, disabled where the element has them.
- Real content, or authored illustrative content at full fidelity labelled synthetic. No lorem,
  no placeholder rectangles, no sparkline standing in for a number.
- Images carry explicit `width` and `height`, `alt` that describes the function, `alt=""` when
  decorative.
- Every requirement in the brief present and findable within seconds; nothing outside the scope
  changed.

## Browser surfaces

Nobody draws the caret, the selection highlight, the scrollbar, the focus ring, an underline's
offset and thickness, `accent-color` on native controls, the numerals in a table, or the chrome of
`<select>` and `<input type=date>` — so each arrives in the browser's own colours, which belong to
no palette. Give every one its value from the tokens. Of all the checks here this is the one that
costs least and gets skipped most, and a reader notices it before anything else.

## Copy

- Controls name their action ("Save changes", not "Submit") and the verb survives the whole flow:
  press "Archive" and the confirmation reads "Archived", never "Success".
- Errors name the problem and the recovery, in the interface's voice; they do not apologise.
- The product's own register, from the contract's `Copy` line; sentence case; no headline that
  could belong to another product.

## Responsive and platform

- The composition holds at 360px, at the project's breakpoints and at 1440px+; nothing scrolls
  horizontally; the body font never shrinks to fit.
- Layout scales with the user's text size: spacing in `rem`/`em` where it must move with type.
- Light or dark comes from the use scene and the contract, and both themes hold every check above
  when the project ships both.

## The inspection round

Build the whole surface first. Then a single inspection covering every width it ships to — phone
and desktop on the web, each supported device size on native — reading every section above off
that one render; a screenshot per check is the loop this paragraph exists to stop. Repair what
that inspection shows as a single batch, allow one confirming look, and stop there: past that
point self-review burns the budget on work `/design § 5` does better, against a baseline.
