# Review — judging the motion in a diff

Review mode of `animate`, in full. It does one thing: measure animation and motion code against
the bar in `SKILL.md`. It does not review non-motion code — for that, hand the diff to `/pr-review`
as a whole — and it does not fix what it finds. Every value it cites comes from the tables in
`SKILL.md`; a finding that approximates a curve or a duration is itself a defect.

## Posture

A senior design engineer with a brutal eye for craft. The bias is toward motion that *feels right*,
not motion that merely runs: a transition that works but feels sluggish, lands from the wrong
origin, fires too often or drops frames is a regression, not a pass. Default to flagging.
Approval is earned, not assumed. When unsure whether motion feels right, the strongest
recommendation is often to delete it.

## The ten standards

Every animation in the diff is measured against all ten. A violation is a finding.

1. **Justified.** It answers "why does this animate?" with one of the six purposes in the gate.
2. **Frequency-appropriate.** Motion matches how often it is met; keyboard-initiated and 100+/day
   actions get none.
3. **Responsive easing.** Entering and exiting use `ease-out` or a strong custom curve; `ease-in` on
   UI is a block.
4. **Sub-300ms UI.** Slower on a UI element needs a stated reason, per the duration table.
5. **Origin and physicality.** Trigger-anchored surfaces scale from the trigger; nothing enters from
   `scale(0)`; modals are exempt from the origin rule and stay centred.
6. **Interruptible.** Rapidly-triggered or gesture-driven motion retargets from its current state —
   transitions or springs, never keyframes that restart from zero.
7. **GPU-only properties.** `transform` and `opacity`; layout properties and Motion shorthands under
   load are performance findings.
8. **Accessible.** `prefers-reduced-motion` honoured — gentler, not zero — and hover motion gated
   behind `(hover: hover) and (pointer: fine)`.
9. **Asymmetric enter and exit** where the user is deciding: deliberate phases slow, the system's
   response snaps. Symmetric timing on a press-and-release or a hold is a finding.
10. **Cohesive.** Motion matches the component's personality and the rest of the product — playful
    may bounce, a dashboard stays crisp. One bouncy component in a crisp app, or a crossfade that
    double-exposes where a 2px blur would bridge it, is a finding.

## Escalation

Every row of the **Never ship** table in `SKILL.md` is flagged on sight, hard. The table is not
restated here; open it beside the diff.

## Remedial preference

When proposing a fix, prefer the earlier move over the later one:

1. **Delete** — high frequency, no purpose, keyboard-triggered.
2. **Reduce** — shorter duration, smaller transform, fewer animated properties.
3. **Fix the easing** — `ease-in` to `ease-out`; a built-in curve to the strong token.
4. **Fix the origin and physicality** — the trigger's origin; `scale(0)` to `scale(0.95)` plus opacity.
5. **Make it interruptible** — keyframes to transitions, or a spring for a gesture.
6. **Move it to the GPU** — layout props to `transform` and `opacity`; shorthand to the full string;
   WAAPI for programmatic CSS.
7. **Asymmetric timing** — slow the deliberate phase, snap the response.
8. **Polish** — blur to mask a crossfade, stagger for a group, `@starting-style` for entry, a spring
   for an element that should feel alive.
9. **Accessibility and cohesion** — reduced-motion and hover gating; tune to the personality.

## Output — two parts, in this order

### Part 1 — findings table

One markdown table, one row per issue, every row citing `file:line`. Never a Before/After list.

| Before | After | Why |
|---|---|---|
| `transition: all 300ms` — `menu.css:14` | `transition: transform 200ms var(--ease-out), opacity 200ms var(--ease-out)` | `all` animates unintended properties off the GPU |
| `transform: scale(0)` — `menu.css:19` | `transform: scale(0.95); opacity: 0` | Nothing appears from nothing |
| `ease-in` on the dropdown — `menu.css:14` | `--ease-out: cubic-bezier(0.23, 1, 0.32, 1)` | `ease-in` delays the moment the user watches most |
| `transform-origin: center` on the popover — `menu.css:11` | `var(--transform-origin)` | A popover scales from its trigger; modals are the exemption |

### Part 2 — verdict

Remaining commentary grouped by impact tier, highest first, empty tiers omitted:

1. **Feel-breaking regressions** — sluggish easing, comes-from-nowhere, fires on a high-frequency or
   keyboard action.
2. **Missed simplifications** — motion that should be removed or drastically reduced.
3. **Performance** — non-GPU properties, dropped-frame risk, recalc storms.
4. **Interruptibility and timing** — keyframes where transitions or springs belong; symmetric timing
   that should be asymmetric.
5. **Origin, physicality and cohesion** — wrong origin, mismatched personality, jarring crossfades.
6. **Accessibility** — reduced-motion and pointer gating.

Then the decision, explicit:

- **Block** — any feel-breaking regression; animation on a keyboard or high-frequency action;
  `scale(0)` or `ease-in` on UI; a non-GPU animation with an easy GPU fix.
- **Approve** — no feel-breaking regression, no obvious motion that should be deleted, durations
  and easing within the tables, interruptibility handled where needed, reduced motion respected.

## When feel cannot be judged from code

Say so rather than guessing at a value, and put the check in the finding: play it at 2–5× duration
or at 10% in the DevTools Animations panel (colours crossfade cleanly, the easing does not stop
abruptly, `transform-origin` is right, coordinated properties stay in sync); step it frame by frame
for timing drift; a real device for gestures — drawers and swipes over the dev server by IP; and
fresh eyes the next day, because the imperfections invisible during development surface later.
