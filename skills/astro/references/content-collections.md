# Astro Content Collections — Content Layer (Astro 6)

In Astro 6 the legacy Collections API was **removed** — Content Layer (loaders) is the only path.

## Definition

```ts
// src/content.config.ts
import { defineCollection } from "astro:content";
import { glob } from "astro/loaders";
import { z } from "astro/zod"; // Zod 4 — NEVER from astro:content/astro:schema (deprecated)

const productsCollection = defineCollection({
  loader: glob({ pattern: "*.json", base: "./src/content/products" }),
  schema: z.object({
    slug: z.string(),
    canonicalUrl: z.url(), // Zod 4: top-level formats (z.url, z.email), not z.string().url()
    // ...
  }),
});

export const collections = { products: productsCollection };
```

Built-in loaders: `glob()` (one entry per file) and `file()` (many entries in one file). A custom loader is an object with a `load()` method. Live collections (runtime) → `references/server-features.md`.

## Zod 4 — migration gotchas

- Import `z` from `astro/zod`.
- `z.string().email()/.url()` → `z.email()`/`z.url()`.
- `.default()` now applies through transforms — review schemas that combined `.default()` with `.transform()`.

## Query

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

Pass `data` or nested data objects to components. Do not pass the collection entry itself to React islands.

## Never hardcode product copy

Anti-pattern:

```astro
<h1>Acme Widgets</h1>
<p>Marketing copy written straight into the component.</p>
```

Preferred:

```astro
<h1>{hero.headline}</h1>
<p>{hero.subheadline}</p>
```

## Schema changes

When adding fields:

1. Update `content.config.ts`.
2. Update every JSON/MD source file the collection loads.
3. Update components that read the field.
4. Run `${tooling.commands.typeCheck}` and `${tooling.commands.build}`.

## Destinations belong in the data, not the markup

Call-to-action labels and destinations belong in the collection and are validated by its schema.
Components read them from the entry data — never hardcode a `mailto:`, a phone link or an external
URL into an `.astro`/`.tsx` file, where nothing validates it and nobody finds it again.

## Versioned content

Versioned JSON content is a collection like any other: when changing an id, a type or an option
would break existing references, bump a version field in the same change and say so in the project's
own rules (`${rulesDir}/`).
