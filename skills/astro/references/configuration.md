# Astro configuration

## `astro.config.mjs`

- `site`: the canonical origin (`${project.productionUrl}`) — required for correct canonical URLs and sitemap output.
- Integrations are per project. A common set is `@astrojs/react` plus `@astrojs/sitemap`; where only part of the site should be indexed, `sitemap` takes a `filter` that excludes the rest.
- `adapter`: only needed if at least one route opts out of prerendering. Which routes those are is the project's decision — read its own route doctrine in `${rulesDir}/` before adding or removing one.
- Vite plugin: `@tailwindcss/vite` under `vite.plugins` (never the `@astrojs/tailwind` integration, deprecated for v4).
- Fonts: whatever the project's layout loads. Where they come in through a `<link>`, the recommended upgrade — with approval — is the native **Fonts API** (stable in 6.0): automatic self-hosting and optimisation, which helps LCP and CLS.
- Output: static by default; `output: "hybrid"` no longer exists as of 5.

## Astro 6 requirements

- Node **22.12+** — declare it in `engines.node` so a mismatched CI fails loudly.
- Config is **ESM only** (`.mjs`/`.ts`); `.cjs`/`.cts` is not supported.
- Vite 7; official adapters on the matching major (for example `@astrojs/vercel` v10 — import from the root, no subpaths).

## Options worth knowing (stable)

| Option | What it does |
|---|---|
| `env: { schema: {...} }` | `astro:env` — typed client/server envs, secret/public |
| `csp: true` | CSP with hashes for inline scripts and styles (stable in 6.0) |
| `prefetch: true` | Built-in link prefetch (replaced `@astrojs/prefetch`) |
| `image.layout` | Responsive images default (`constrained`/`full-width`/`fixed`) |
| `sessionDrivers: {...}` | Sessions (an object; the string driver is deprecated) |

Experimental flags that stabilised in 6.0 and **must not** appear under `experimental{}` any more: `csp`, `fonts`, `liveContentCollections`, `preserveScriptOrder`, `staticImportMetaEnv`, `headingIdCompat`, `failOnPrerenderConflict`.

## Changes that need a decision, not a commit

- `output: "server"` — it flips the whole site off static. Where a project wants only some routes on-demand, that is `prerender = false` per route, not a global switch.
- Flipping a route the project declared static to server-rendered, or the reverse, without approval.
- Adding `ClientRouter` / SPA routing where the project's rules call for a static MPA.
- Editing `astro.config.mjs` with no stated reason — projects commonly list it in `protectedFiles`.

## Build

```bash
${tooling.commands.build}    # static output in dist/, plus adapter functions for any server routes
${tooling.commands.typeCheck}
```
