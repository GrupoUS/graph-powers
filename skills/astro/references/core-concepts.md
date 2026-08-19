# Astro Core Concepts

> Baseline: **Astro 6** — ESM-only config, Node 22.12+, Vite 7, Zod 4 (`astro/zod`), `Astro.glob()` removed (use `import.meta.glob()`), `import.meta.env` inlined with no type coercion.

## Components (.astro files)

Every `.astro` file has two sections separated by `---` code fences:

1. **Frontmatter (Component Script)** — Runs on server only. Import components, fetch data, define props.
2. **Template** — HTML with JSX-like expressions. No client-side runtime.

### Props

```astro
---
interface Props {
  title: string;
  subtitle?: string;
  count?: number;
}
const { title, subtitle = "Default", count = 0 } = Astro.props;
---
<h1>{title}</h1>
{subtitle && <h2>{subtitle}</h2>}
```

### Expressions in Templates

```astro
---
const items = ['Alpha', 'Beta', 'Gamma'];
const visible = true;
---
<!-- Variables -->
<h1>{title}</h1>

<!-- Conditionals -->
{visible && <p>Shown</p>}
{visible ? <p>Yes</p> : <p>No</p>}

<!-- Iteration -->
<ul>
  {items.map(item => <li>{item}</li>)}
</ul>

<!-- Dynamic attributes -->
<div class={`card ${isActive ? 'active' : ''}`}>
<div class:list={['card', { active: isActive }, extraClasses]}>

<!-- Raw HTML (use sparingly, XSS risk) -->
<div set:html={htmlString} />
```

### Slots

Default slot:
```astro
<!-- Wrapper.astro -->
<div class="wrapper">
  <slot />  <!-- Children inserted here -->
</div>

<!-- Usage -->
<Wrapper>
  <p>This goes in the slot</p>
</Wrapper>
```

Named slots:
```astro
<!-- Layout.astro -->
<header><slot name="header" /></header>
<main><slot /></main>
<footer><slot name="footer" /></footer>

<!-- Usage -->
<Layout>
  <h1 slot="header">Title</h1>
  <p>Main content (default slot)</p>
  <span slot="footer">Copyright</span>
</Layout>
```

Fallback content:
```astro
<slot name="sidebar">
  <p>Default sidebar content</p>
</slot>
```

### Accessing Slot Content Programmatically

```astro
---
const hasHeader = Astro.slots.has('header');
---
{hasHeader && <div class="header-wrapper"><slot name="header" /></div>}
```

## Pages

Files in `src/pages/` become routes via file-based routing:

| File | Route |
|------|-------|
| `src/pages/index.astro` | `/` |
| `src/pages/about.astro` | `/about` |
| `src/pages/blog/post-1.astro` | `/blog/post-1` |
| `src/pages/[slug].astro` | Dynamic route |
| `src/pages/404.astro` | Custom 404 page |

Pages MUST return full HTML documents (or use layouts):

```astro
---
import Layout from '../layouts/Layout.astro';
---
<Layout title="About">
  <h1>About Us</h1>
</Layout>
```

## Layouts

Reusable page shells. Convention: `src/layouts/`.

```astro
---
// src/layouts/BaseLayout.astro
interface Props { title: string; description?: string; }
const { title, description = "Default description" } = Astro.props;
---
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="description" content={description} />
    <title>{title}</title>
  </head>
  <body>
    <slot />
  </body>
</html>
```

Nesting layouts:
```astro
---
// src/layouts/BlogLayout.astro
import BaseLayout from './BaseLayout.astro';
const { frontmatter } = Astro.props;
---
<BaseLayout title={frontmatter.title}>
  <article>
    <h1>{frontmatter.title}</h1>
    <slot />
  </article>
</BaseLayout>
```

## Data Fetching in Frontmatter

```astro
---
// Fetch at build time (SSG) or request time (SSR)
const response = await fetch('https://api.example.com/data');
const data = await response.json();

// Use Content Collections
import { getCollection } from 'astro:content';
const posts = await getCollection('blog');
---
```

## API Endpoints (server routes)

A `.ts` file under the pages directory exporting typed HTTP handlers:

```ts
import type { APIRoute } from "astro";
export const prerender = false; // on-demand route (requires an adapter)

export const POST: APIRoute = async ({ request, locals }) => {
  return new Response(JSON.stringify({ ok: true }), { status: 200 });
};
```

On a static route, `GET` runs at build time and produces a file. Details, middleware, Actions and Sessions → `references/server-features.md`.

## Middleware + `Astro.locals`

`<src>/middleware.ts` with `defineMiddleware` from `astro:middleware` runs on every served request and exposes typed state through `context.locals` (typed in `App.Locals`). User identity comes **only** from `locals`, never from the body or the query string.

## Typed env — `astro:env`

Schema in `env: {}` in the config; import from `astro:env/server` / `astro:env/client`. Validates at build time and separates secret from public. Prefer it over raw `import.meta.env` — in Astro 6 that is inlined with no type coercion.

## Script Handling

```astro
<!-- Bundled & optimized (default) -->
<script>
  console.log('Bundled by Vite, deduped, optimized');
</script>

<!-- Inline (not processed) -->
<script is:inline>
  console.log('Inserted as-is, not bundled');
</script>

<!-- Pass server vars to client -->
<script define:vars={{ serverValue: 'hello' }}>
  // serverValue available here (implies is:inline)
  console.log(serverValue);
</script>
```

## TypeScript

Astro has built-in TypeScript support. Use `tsconfig.json`:

```json
{
  "extends": "astro/tsconfigs/strict"
}
```

Options: `base` (minimal), `strict` (recommended), `strictest` (maximum)

Import types:
```astro
---
import type { CollectionEntry } from 'astro:content';
import type { HTMLAttributes } from 'astro/types';
---
```
