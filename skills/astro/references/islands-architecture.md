# Astro Islands Architecture

## Doctrine

Plain Astro first, but **an island is welcome when it adds real expressiveness** — motion, interaction, depth. The limit is not aesthetic, it is performance and accessibility:

- `client:visible`/`client:idle` by default; `client:load` when the interaction *is* the page.
- Animation libraries **inside the island**, never in the page entry bundle.
- `prefers-reduced-motion` honoured by every animation (hard floor).
- Full motion guidance: `references/performance.md § Animation Performance` — single source, not duplicated here.

## Directive guidance

| Directive | Use |
|---|---|
| none | the default for static sections |
| `client:load` | interactivity that *is* the page (a sign-in form, an editor, an admin surface) |
| `client:idle` | a non-critical above-the-fold island |
| `client:visible` | an expressive or interactive island below the fold (the usual default) |
| `client:only="react"` | last resort — a browser API at module scope prevents SSR |
| `server:defer` | Server Island: dynamic server-rendered content without SSR-ing the page (see `server-features.md`) |

## Choosing a directive in practice

- Below-fold marketing or presentational islands: `client:visible` — the hydration cost is paid only
  if the visitor ever reaches them.
- A form the visitor came to the page to submit: `client:load` — deferring it means a visible dead
  period on the control that matters most.

## The framer-motion pattern

```tsx
import { LazyMotion, domAnimation, m } from "framer-motion";

export function Island() {
  return (
    <LazyMotion features={domAnimation}>
      <m.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} />
    </LazyMotion>
  );
}
```

`LazyMotion + m.*` (not `motion.*` directly) — it cuts the animation runtime bundle. Honour `useReducedMotion()`.

## Hydration budget

- Keep initial JS small (advisory ~50 KB in the page entry; islands carry their own weight).
- Do not import motion or icon bundles into page-level static components.
- Import icons through the project's existing wrapper rather than one by one.

## Validation

```bash
# Grep tool (not a shell `grep`, which Windows does not have): grep -rn "client:load" src
```

Each hit needs a clear reason — a form that is the point of the page counts as one. Swap the path
for the project's own frontend root (`${paths.frontendRoot}`) when it is not `src`.
