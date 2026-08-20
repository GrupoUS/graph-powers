# Frontend Specialist On-Demand Rubric

Load only for design critique, motion/dark mode, performance budgeting, test
design, or frontend refactoring. Canonical brand rules remain in the project's design rule (`${rulesDir}/design.md`)
and `${rulesDir}/design.md`; this file is a checkpoint aid, not a duplicate.

## Interaction and state

- Clear primary action, hierarchy, labels, validation, and recovery.
- Loading, empty, partial, success, permission-denied, and error states.
- Keyboard order, visible focus, semantic HTML, accessible names, announcements.
- One mobile scroll owner, safe overflow, touch targets, and responsive density.

## Visual and motion

- Semantic tokens and verified light/dark contrast.
- Purposeful typography, spacing, alignment, and information density.
- GPU-friendly transform/opacity motion; no layout-thrashing animation.
- Respect `prefers-reduced-motion`; motion must communicate state or hierarchy.

## Performance and tests

- Measure before memoization/code splitting; avoid accidental request waterfalls.
- Test behavior and accessibility rather than implementation details.
- Refactors preserve external behavior and begin with a focused regression test.
- Use browser evidence for user-visible acceptance criteria when available.
