# View Transitions — the client-side router

> Astro 6: the `<ViewTransitions />` component was **removed**; the transition router is `<ClientRouter />` (from `astro:transitions`).

Whether client-side routing is allowed at all is the project's call, not the framework's. **Read the
project's own route doctrine in `${rulesDir}/` before adding or removing it.** A project that
declares itself a static MPA has already answered the question: no transition router.

## What the router changes

`ClientRouter` intercepts same-origin navigation and swaps the document instead of reloading it.
That has consequences the rest of the code has to absorb:

- Scripts no longer re-run on navigation. Anything that ran once on `DOMContentLoaded` — reveal
  animations, observers, third-party widgets — has to move to the router lifecycle events
  (`astro:page-load`, `astro:after-swap`) or it silently stops working after the first page.
- Module-scope state survives navigation, so anything cached at import time outlives the page it
  belonged to.
- Elements you want animated across pages need a matching `transition:name`; everything else is a
  cross-fade.

## When a project forbids it

The static-MPA contract means:

- Do not import `ClientRouter` from `astro:transitions`.
- Do not add transition-router components to the shared layout.
- Do not reach for SPA-style navigation to solve an animation or routing problem — that is a
  redesign of the site's delivery model dressed up as a bug fix.

Instead:

- Use normal document navigation between pages.
- Use CSS/JS micro-interactions scoped to the current page.
- Keep motion on `transform` and `opacity`, and honour `prefers-reduced-motion`.
- Run reveal/interaction scripts on ordinary page load; no router lifecycle hooks needed.

## Recovery note

If a transition-related error appears in a project that does not use the router, remove the
transition-router usage rather than upgrading it — replacing an old `ViewTransitions` snippet with
`ClientRouter` adopts the router by accident.
