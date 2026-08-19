---
paths:
  - "{{UI_PATHS_GLOB}}"
---

# Design — what is not preference

> Graph Powers template. What is here holds in any product. This project's visual identity — palette,
> fonts, tone, named rules — is not this: it lives in `DESIGN.md` at the root (built per the plugin's
> `DESIGN.md` spec). **This rule points at it; it never restates it**, because two copies diverge.

## Colour

- Semantic tokens, always. A colour literal in a component is a decision nobody can change later
  without hunting occurrences.
- WCAG AA contrast on text and on interactive elements. AAA where the text is long.
- Colour is never the only carrier of information — pair it with shape, icon or text.

## Typography

- Two families at most. The third always looks like an accident.
- Nothing below {{MIN_FONT_SIZE}} at any viewport.
- Numbers compared in a column use `tabular-nums`.

## Space and targets

- A {{SPACING_GRID}} grid. A value off the grid needs a reason written in the code.
- Minimum touch target {{TOUCH_TARGET_MIN}} on touch screens.

## Motion

- `prefers-reduced-motion` is required, not optional. Whoever asked for less motion has a medical
  reason more often than people assume.
- Animate `transform` and `opacity` only — everything else forces relayout.
- An interface transition answers within 200 ms. Above that it stops being a response and becomes a
  wait.

## Focus and keyboard

- `:focus-visible` with a visible {{FOCUS_RING}} ring. Removing the ring without replacing it breaks
  keyboard navigation.
- A button is a `<button>`, a link is an `<a>`. Swapping them breaks keyboard and screen reader at
  the same time.

## Images

- Explicit `width` and `height`, always — without them the page jumps when the image arrives.
- `alt` that describes the function, not the file. A decorative image takes `alt=""`.

## States

Every screen that fetches data has four states designed: loading, empty, error and full. The empty
state is the most forgotten and the first one a new user sees.

## Where this project's identity lives

Root `DESIGN.md` — tokens, named rules, hierarchy, component authority, refused patterns.

{{DESIGN_POINTERS}}
