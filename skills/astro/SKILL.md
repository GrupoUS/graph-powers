---
name: astro
description: Use when implementing, debugging, or reviewing Astro components, pages, Content Collections, islands architecture, client directives, astro.config.mjs, Tailwind v4 integration, static generation, hydration, build errors, performance optimization, API routes, endpoints, middleware, Astro.locals, prerender, adapters, Actions, Sessions, astro:env, server islands, and CSP.
---

# Astro Framework Reference

Astro renders static HTML by default and hydrates interactive islands only when explicitly requested through `client:*` directives. Base version documented here: **Astro 6** (Vite 7, Node 22.12+, Zod 4, Content Layer only). Astro 7 exists — see the watchlist at the end; do not migrate.

## The project's own doctrine comes first

Astro projects split along one axis more than any other: **which routes are static and which are
server-rendered.** That split is the project's decision, not this skill's, and it is frequently
asymmetric — some route groups must stay static while others cannot be.

Before writing anything, read the project's own route doctrine in `${rulesDir}/` for:

- which route groups are static and which declare `export const prerender = false`;
- whether an adapter exists at all, and which routes justify it;
- whether client-side routing (`ClientRouter`) is allowed;
- where product copy lives, if it is not in the components;
- what a new server route obliges you to update in the same change — typically the sitemap filter
  and the robots policy.

**If the generic Astro guidance below conflicts with the project's rules, the project wins.** This
file describes the framework; the project describes itself.

## When to use

- New or changed `.astro` pages/components/layouts.
- `src/content.config.ts` or Content Collections (Content Layer + loaders).
- React islands and hydration directives.
- API routes and endpoints, middleware, `Astro.locals`, `prerender = false` patterns.
- `astro.config.mjs` changes.
- Tailwind v4 `@theme` integration.
- Build, type or hydration errors.
- SEO/canonical/JSON-LD changes in Astro files.

## Quick reference

### Component anatomy

```astro
---
import Component from "../components/Component.astro";
interface Props { title: string }
const { title } = Astro.props;
---

<section>
  <h1>{title}</h1>
  <Component />
</section>
```

### Client directives

A React island is justified when it adds real interaction or expressiveness. The guardrail is performance — `client:visible`/`client:idle` by default, animation libraries inside the island rather than in the page entry — plus `prefers-reduced-motion`.

| Directive | Usage |
|---|---|
| none | default for static `.astro` |
| `client:load` | interactivity that *is* the page (forms, persistent critical UI) |
| `client:idle` | a non-critical above-the-fold island |
| `client:visible` | an interactive or expressive island below the fold (the usual default) |
| `client:only="react"` | last resort when SSR is impossible (a browser API at module scope) |
| `server:defer` | Server Island — dynamic content rendered on the server without SSR-ing the whole page |

### Content Collections (Content Layer)

```ts
// src/content.config.ts — Astro 6: Content Layer is the only path
import { defineCollection } from "astro:content";
import { glob } from "astro/loaders";
import { z } from "astro/zod"; // Zod 4 — never from astro:content/astro:schema

const products = defineCollection({
  loader: glob({ pattern: "*.json", base: "./src/content/products" }),
  schema: z.object({ slug: z.string(), canonicalUrl: z.url() }), // Zod 4: top-level formats
});
```

```astro
---
import { getCollection } from "astro:content";
const products = await getCollection("products");
const slug = Astro.params.slug;
const product = products.find((p) => p.data.slug === slug);
if (!product) throw new Error("Missing product entry: " + slug);
const { data } = product;
---
```

Map data before passing to framework islands; do not pass collection entries directly.

### Project structure

```text
src/
  pages/            # static pages, server routes (prerender = false), api/
  components/
  layouts/
  content/          # collection sources (JSON/MD/YAML) read by loaders
  content.config.ts
  lib/              # shared server and client helpers
  middleware.ts
  styles/global.css
astro.config.mjs
```

## Detailed references

| Reference | Content |
|---|---|
| `references/core-concepts.md` | Components, pages, layouts, slots, props, endpoints, middleware |
| `references/content-collections.md` | Content Layer, loaders, Zod 4, JSON data, SSOT |
| `references/islands-architecture.md` | Hydration, React islands, LazyMotion, server islands |
| `references/styling-tailwind.md` | Scoped CSS, Tailwind v4, `@theme`, `@reference` |
| `references/configuration.md` | `astro.config.mjs`, adapter, integrations, astro:env, CSP |
| `references/performance.md` | LCP, CLS, INP, images, Fonts API, prefetch, bundle |
| `references/server-features.md` | Endpoints, middleware, Actions, Sessions, adapters |
| `references/view-transitions.md` | The transition router, and when a project allows it |
| `references/troubleshooting.md` | Build/hydration/content errors, compiler gotchas |

## Common mistakes

| Mistake | Fix |
|---|---|
| Hardcoding product copy in components | Move it into a content collection |
| Adding `client:*` to `.astro` components | Client directives apply to framework islands only |
| Passing full collection entries to React | Pass plain `.data` |
| Adding `ClientRouter` without checking | A static MPA forbids it — read the project's own route doctrine in `${rulesDir}/` first |
| Setting `prerender = false` on a route the project declared static | Read the project's route doctrine before changing which side a route is on |
| Importing `z` from `astro:content`/`astro:schema` | Deprecated in 6 — import from `astro/zod` (Zod 4; top-level `z.url()`/`z.email()`) |
| `@astrojs/tailwind` integration with Tailwind v4 | Deprecated — use the `@tailwindcss/vite` plugin under `vite.plugins` |
| `@apply` in a scoped `<style>` with no `@reference` | Add `@reference "tailwindcss"` at the top of the block |
| `import vercel from "@astrojs/vercel/serverless"` | v10 removed the subpaths — import from the root `@astrojs/vercel` |
| `Astro.glob()` | Removed in 6 — use `import.meta.glob()` |
| Mixing package managers | Use the one the project declares (`${tooling.packageManager}`) |
| Hardcoding hex in components | Add or reuse a token in the project's stylesheet (`${paths.stylesRoot}`) |
| Animating layout properties | Fine when the effect needs it; prefer `transform`/`opacity` for performance; always honour `prefers-reduced-motion` |

## Astro 7 — watchlist, not a migration

Stable since 2026-06-22. This file documents 6; a project moves to 7 as a deliberate, approved decision, never as a side effect of another task.

- Vite 8 plus **Rolldown** (a Rust bundler) replace esbuild and Rollup; builds 15-61% faster.
- The Rust `.astro` compiler is stable; the Rust markdown/MDX pipeline becomes the default in place of unified/remark/rehype.
- Advanced routing (`src/fetch.ts`) becomes the default; `logger`, `queuedRendering`, `cache`/`routeRules` stabilised.
- The main breaking change: no HTML correction — JSX-style strictness (closed tags, whitespace).
- The ecosystem is moving quickly; expect adapters to need a new major before you can follow.
- Before migrating: run the official codemods, review `.astro` templates for the new strictness, and check any custom remark/rehype plugins.
