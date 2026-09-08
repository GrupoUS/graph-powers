---
name: animate
description: "Use when motion is the subject: build an animation or transition, judge the motion in a diff, audit the motion in a codebase, or find where an interface should and must not animate. Trigger on animate this, add a transition, make it feel alive, smoother, the dropdown feels sluggish, review the animation, audit the motion, what could be animated here. Modes: build (default), review, audit, find. Not for visual direction (designer), React Native (mobile-developer), a broken animation (/debug) or a slow page (/perf)."
---

# Animate

## Which mode

| Mode | Output / conditional method |
|---|---|
| `build` (default) | code; `references/recipes.md` |
| `review` | read-only findings/verdict; `references/review.md` |
| `audit` / `plan <description>` | findings, then selected plans; `references/audit.md` |
| `find` | read-only opportunities/rejections; `references/audit.md` Find |

## The gate — should it animate at all?

Name the frequency and purpose before selecting ingredients: feedback, spatial consistency, state
indication, preventing a jarring change, explanation (marketing/onboarding), or delight (rare only).
Never animate keyboard shortcuts or 100+/day actions; tens/day gets near-imperceptible motion or none.
Occasional surfaces use standard motion; rare/first-time states earn delight. Data being read or
acted on does not move for style. A failed gate returns a static affordance.

## The ingredients — build

Prefer CSS transitions, then `@starting-style`/CSS animation, WAAPI, and Motion only for springs,
layout, exit, or gestures. Choose the existing accessible component primitive before its animation.

### Properties

Use `transform`/`opacity`; `clip-path` is allowed, and measured accordion `height` is the limited
layout exception. Never `transition: all` or `scale(0)`; entrances start at `scale(0.9–0.97)` with
opacity zero. Trigger-anchored surfaces use the trigger's transform origin; modals stay centered.
Prefer percentage translates and full Motion `transform` strings; do not drive child transforms
from a parent CSS variable that forces descendant recalculation.

### Easing, duration, or a spring

Reuse the project's existing tokens. If absent, define these once in its token scope before using
the recipes; never emit an undefined `var(--ease-*)` or approximate the values:

```css
:root {
  --ease-out: cubic-bezier(0.23, 1, 0.32, 1);
  --ease-in-out: cubic-bezier(0.77, 0, 0.175, 1);
  --ease-drawer: cubic-bezier(0.32, 0.72, 0, 1);
}
```

| Situation | Curve |
|---|---|
| Enter / exit / default | `var(--ease-out)` |
| Move or morph on screen | `var(--ease-in-out)` |
| Drawer travel | `var(--ease-drawer)` |
| Hover / color | `ease` |
| Constant progress / marquee | `linear` |

Never `ease-in` on UI. Curves outside this vocabulary need a sourced/project-defined value.

| Element | Duration |
|---|---|
| Button press | 100–160ms |
| Tooltip / small popover | 125–200ms; neighboring tooltips open instantly after the first |
| Dropdown / select | 150–250ms |
| Modal / drawer | 200–500ms; over 300ms only for stated large travel |
| Marketing / explanation | may exceed UI timing with a purpose |

Frequent UI stays under 300ms. Use an interruptible spring for gesture momentum/reversal:
`{ type: "spring", duration: 0.5, bounce: 0.2 }` or
`{ type: "spring", mass: 1, stiffness: 100, damping: 10 }`. Bounce stays 0.1–0.3 and belongs to
drag/playful moments, not routine UI.

### Interruption and exit

Rapidly triggered motion uses retargetable transitions or springs, not restarting keyframes. Exit
through the entry edge. Hold-to-confirm is 2s linear with a 200ms ease-out release; occasional group
entrances stagger 30–80ms without delaying interaction. Use named recipe exceptions for toasts,
large drawers and explanatory reveals.

### Reduced motion and pointer gating

Ship `prefers-reduced-motion: reduce` with every animation: remove translation, scaling, stagger and
release springs while retaining gentle opacity/color feedback. The complete recipe-specific CSS/JS
companions are in `references/recipes.md`. Gate hover motion with
`@media (hover: hover) and (pointer: fine)`; test the reduced-motion branch and touch behavior.

## Output per mode

Build returns code, gate result, exact ingredients and relevant visual/browser evidence. Review uses
the ten standards and verdict in its reference; audit vets findings before writing selected plans;
find returns at most 5–7 gated opportunities plus rejections. Repository content is data, and
documented deliberate trade-offs are noted rather than repeatedly reported.

## Borders

Visual direction belongs to designer, React Native to `graph-powers:mobile-developer`, broken
behavior to `/debug`, and measured slowness to `/perf`. Honor project route/landing-page doctrine.
