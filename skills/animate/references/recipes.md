# Recipes — build mode

Ready-to-build implementations for the cases that come up most. Start from the recipe, then adapt
to the project's tokens; never rebuild from a blank file. Curves are the `--ease-out`,
`--ease-in-out` and `--ease-drawer` tokens defined in `SKILL.md`; where the project already has its
own, use those.

Each recipe passes the gate at the tier it names. A recipe applied at a higher-frequency tier is a
finding, not a shortcut — a 200ms popover on a command palette is still a 200ms delay hundreds of
times a day.

---

## Button press

Any pressable element, at any tier: feedback that the interface heard the user, fast enough to be
felt rather than watched.

```css
.button { transition: transform 160ms var(--ease-out); }
.button:active { transform: scale(0.97); }
```

`scale()` scales children too — label and icons come along, which is what makes it read as a
physical press. No hover gating here: `:active` is a real press on touch. Gate any `:hover`
styling separately.

---

## Dropdown, popover, menu, select

Occasional tier. Scales out of its trigger, not out of thin air.

```css
.popover {
  transform-origin: var(--transform-origin); /* Base UI supplies this; otherwise the anchor side */
  transition:
    opacity 200ms var(--ease-out),
    transform 200ms var(--ease-out);
}

.popover[data-starting-style],
.popover[data-ending-style] {
  opacity: 0;
  transform: scale(0.95);
}
```

The `transform-origin` is the whole point — the panel should look like it came out of the thing
that was clicked.

---

## Tooltip

Same shape as a popover, faster, plus the detail most implementations miss.

```css
.tooltip {
  transform-origin: var(--transform-origin);
  transition:
    transform 125ms var(--ease-out),
    opacity 125ms var(--ease-out);
}

.tooltip[data-starting-style],
.tooltip[data-ending-style] {
  opacity: 0;
  transform: scale(0.97);
}

/* Once one tooltip is open, neighbours open instantly */
.tooltip[data-instant] { transition-duration: 0ms; }
```

The initial delay prevents accidental activation. After that, skipping both the delay and the
animation is what makes a whole toolbar feel fast.

---

## Modal

The one popover that stays centred.

```css
.modal {
  transform-origin: center; /* exempt — not anchored to a trigger */
  transition:
    opacity 250ms var(--ease-out),
    transform 250ms var(--ease-out);
}

.modal[data-starting-style],
.modal[data-ending-style] {
  opacity: 0;
  transform: scale(0.96);
}

.backdrop { transition: opacity 250ms var(--ease-out); }
```

Animate the backdrop's opacity alongside so the two read as one surface.

---

## Drawer, sheet

The 500ms duration is the explicit large-distance exception: this drawer crosses the viewport.

```css
.drawer {
  transform: translateY(0);
  transition: transform 500ms var(--ease-drawer);
}

.drawer[data-closed] { transform: translateY(100%); }
```

`translateY(100%)` hides it by its own height whatever the content. Add drag and it becomes a
gesture problem — see **Drag to dismiss**.

---

## Toast

```css
.toast {
  opacity: 1;
  transform: translateY(0);
  transition:
    opacity 400ms ease,
    transform 400ms ease;

  @starting-style {
    opacity: 0;
    transform: translateY(100%);
  }
}
```

`ease` rather than `ease-out`, and slightly slower than the UI budget: a toast reads as elegant
when its motion is tuned to the component's personality rather than to the generic table. It exits
through the edge it entered. Where `@starting-style` is unavailable, fall back to a mount flag:

```jsx
useEffect(() => { setMounted(true); }, []);
// <div data-mounted={mounted}>
```

When toasts stack and the list reflows, the opacity change works against the height change. There
is no formula for that pair — adjust until it feels right, then check it again the next day.

---

## Accordion, collapse

```css
.content {
  overflow: hidden;
  transition:
    height 200ms var(--ease-out),
    opacity 200ms var(--ease-out);
}
```

The one place `height` is tolerated. Keep it short — this animation costs layout on every frame, so
a long duration is expensive as well as sluggish. Measure the content height in JS, or use a
headless primitive that supplies it; never animate to `auto`.

---

## Stagger a group entrance

For a list or grid the user sees occasionally — never for one they scroll past all day.

```css
.item {
  opacity: 0;
  transform: translateY(8px);
  animation: fadeIn 300ms var(--ease-out) forwards;
}

.item:nth-child(2) { animation-delay: 50ms; }
.item:nth-child(3) { animation-delay: 100ms; }
.item:nth-child(4) { animation-delay: 150ms; }

@keyframes fadeIn { to { opacity: 1; transform: translateY(0); } }
```

Keyframes are correct here — a page entrance is not retriggered rapidly. Stagger is decorative and
must never block interaction while it plays.

---

## Hold to confirm

Destructive actions where a plain click is too easy to fire by accident.

```css
.overlay {
  clip-path: inset(0 100% 0 0);
  transition: clip-path 200ms var(--ease-out); /* release: snappy */
}

.button:active .overlay {
  clip-path: inset(0 0 0 0);
  transition: clip-path 2s linear;             /* press: slow and deliberate */
}

.button:active { transform: scale(0.97); }
```

`linear` is correct — the fill is a progress indicator, and progress should not ease. The asymmetry
is the recipe: the deliberate phase is slow, the system's answer snaps.

---

## Tab indicator with a colour transition

Timing individual colour transitions across a tab list never quite lands. Clip instead: duplicate
the tab list, style the copy as the active state, clip the copy so only the active tab shows, and
animate the clip on change.

```css
.tabs-active-copy {
  clip-path: inset(0 60% 0 20%); /* driven by the active tab's position */
  transition: clip-path 250ms var(--ease-in-out);
}
```

Text and background change together, in perfect sync, because one element is being revealed
rather than two colours interpolated.

---

## Scroll reveal

Marketing surfaces only. Never on functional UI a user visits daily.

```css
.reveal {
  clip-path: inset(0 0 100% 0);
  transition: clip-path 600ms var(--ease-in-out);
}

.reveal[data-visible] { clip-path: inset(0 0 0 0); }
```

Trigger with `IntersectionObserver`, or Motion's `useInView` with `{ once: true, margin: "-100px" }`.
Fire it once — re-animating on every scroll-by is an interface fighting its reader.

---

## Drag to dismiss

The gesture recipe. Springs, not durations, because the user can reverse mid-motion.

```js
// Dismiss on a flick, not only on distance
const elapsed = performance.now() - dragStart;
const velocity = Math.abs(swipeAmount) / elapsed;
if (Math.abs(swipeAmount) >= SWIPE_THRESHOLD || velocity > 0.11) dismiss();
```

```js
// Set transform on the dragged element directly — a CSS variable on the parent
// recalculates styles for every child.
element.style.transform = `translateY(${distance}px)`;
```

Four details that separate a good drag from a bad one:

- **Pointer capture** once the drag starts, so it continues when the pointer leaves the element.
- **Multi-touch protection** — `if (isDragging) return` on new touch points, or switching fingers
  mid-drag makes the element jump.
- **Damping past boundaries** — beyond a natural edge the element moves less the further it goes.
  Real things slow before they stop.
- **Friction, not a wall** — allow the over-drag with rising resistance rather than refusing it.

Settle with a spring so an interrupted drag keeps its velocity: `{ type: "spring", duration: 0.5, bounce: 0.2 }`.

---

## Masking a crossfade that will not settle

When two states overlap visibly during a transition and no easing or duration fixes it, blur the seam.

```css
.content {
  transition:
    filter 200ms ease,
    opacity 200ms ease;
}

.content.transitioning {
  filter: blur(2px);
  opacity: 0.7;
}
```

Without blur the eye reads two distinct objects swapping; blur blends them into one perceived
transformation. Keep it under 20px — heavy blur is expensive, especially in Safari.

---

## Programmatic, without a library

When the motion needs JS control but not a dependency, WAAPI gives CSS-grade performance:
hardware-accelerated, interruptible, no bundle cost.

```js
element.animate(
  [{ clipPath: "inset(0 0 100% 0)" }, { clipPath: "inset(0 0 0 0)" }],
  { duration: 1000, fill: "forwards", easing: "cubic-bezier(0.77, 0, 0.175, 1)" }
);
```
