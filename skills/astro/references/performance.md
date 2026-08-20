# Performance Optimization

## Astro Performance Defaults

Astro achieves **40% faster load times** and **90% less JavaScript** compared to React SPAs by:
- Rendering to static HTML by default
- Zero client-side JS unless explicitly opted in
- Automatic asset optimization via Vite

## Core Web Vitals Targets

> Advisory — measure and note, do not block a merge. CLS stays hard: it is layout hygiene. The one hard floor for motion is `prefers-reduced-motion`.

| Metric | Target | How Astro Helps |
|--------|--------|----------------|
| LCP (Largest Contentful Paint) | < 2.5s | Static HTML, preloaded assets |
| CLS (Cumulative Layout Shift) | 0 | Explicit image dimensions |
| INP (Interaction to Next Paint) | ~200ms | Minimal JS, deferred hydration |
| FCP (First Contentful Paint) | < 1.8s | No JS blocking render |
| TTFB (Time to First Byte) | < 800ms | Static files from CDN |

## Image Optimization

### Astro Image Component

```astro
---
import { Image } from 'astro:assets';
import heroImage from '../assets/hero.jpg';
---

<!-- Optimized: auto-format, responsive, explicit dimensions -->
<Image
  src={heroImage}
  alt="Hero image description"
  width={1200}
  height={630}
  loading="eager"           <!-- Above fold: eager -->
  fetchpriority="high"      <!-- LCP candidate -->
  format="avif"             <!-- Modern format -->
/>

<!-- Below fold: lazy (default) -->
<Image
  src={speakerPhoto}
  alt="Speaker name"
  width={400}
  height={400}
  loading="lazy"
/>
```

### Image Rules

1. **Always set `width` and `height`** — Prevents CLS
2. **`loading="eager"` + `fetchpriority="high"`** — Only for LCP image (hero)
3. **`loading="lazy"`** — Default for below-fold images
4. **Use `astro:assets`** — Auto-optimization (format, size, quality)
5. **`public/` images** — Not optimized, use for external/dynamic URLs only

### Picture Component (Multiple Formats)

```astro
---
import { Picture } from 'astro:assets';
import hero from '../assets/hero.jpg';
---
<Picture
  src={hero}
  formats={['avif', 'webp']}
  alt="Hero"
  width={1200}
  height={630}
/>
```

### Responsive images (stable; the `layout` prop)

```astro
<Image src={hero} alt="Hero" layout="constrained" priority />
```

- `layout`: `constrained` | `full-width` | `fixed` — generates `srcset`/`sizes` automatically (global default through `image.layout` in the config).
- `priority`: shorthand for `loading="eager"` plus `fetchpriority="high"` on the LCP image.
- Astro 6 never upscales; emitted styles are CSP-safe (`data-*` plus a hash class, not inline); `getImage()` throws on the client.

## Font Optimization

### Fonts API (recommended — stable since Astro 6.0)

```js
// astro.config.mjs
import { defineConfig, fontProviders } from "astro/config";
export default defineConfig({
  fonts: [{ provider: fontProviders.google(), name: "Inter", cssVariable: "--font-inter" }],
});
```

```astro
---
import { Font } from "astro:assets";
---
<Font cssVariable="--font-inter" preload />
```

Automatic self-hosting and optimisation, with correct preloading — better LCP and CLS than a hand-written `<link>`.

### If the project still loads fonts through a `<link>`

A project loading fonts through `<link>` should at least use preconnect and `display=swap` to avoid FOIT. Moving to the Fonts API means editing `astro.config.mjs` — a recommended upgrade, with approval.

## JavaScript Budget

> Advisory. Animation libraries live inside their island — never in the page entry bundle.

| Category | Target |
|----------|--------|
| Initial JS bundle | ~< 50 KB (advisory; animation libraries inside the island) |
| Per-island JS | As small as possible |
| Total page JS | < 100KB |

### Reducing JS

1. **Default to `.astro`** — Zero JS components
2. **`client:visible`** over `client:load` — Defer hydration
3. **Avoid large libraries** in islands — Tree-shake or use lighter alternatives
4. **`client:idle`** for non-critical widgets
5. **Code splitting** — Vite auto-splits per island

## CSS Performance

1. **Inline critical CSS** — Astro auto-inlines small stylesheets
2. **Purge unused CSS** — Tailwind v4 auto-purges
3. **Avoid `@import` chains** — Use single entry point
4. **Minimize custom CSS** — Prefer Tailwind utilities

## Build Analysis

```bash
# Check bundle sizes
# Set ANALYZE=true for this run only, in the form your shell takes: `ANALYZE=true <cmd>`
# (bash), `$env:ANALYZE="true"; <cmd>` (PowerShell), `set ANALYZE=true && <cmd>` (cmd).
${tooling.commands.build}

# Lighthouse audit (with local preview running)
bunx lighthouse http://localhost:4321 --preset=desktop
```

## Preloading & Prefetching

Built-in prefetch (stable; replaced `@astrojs/prefetch`):

```js
// astro.config.mjs
export default defineConfig({ prefetch: true });
```

```astro
<a href="/about" data-astro-prefetch="viewport">About</a>
<!-- strategies: hover (default) | tap | viewport | load -->
```

Manual preloading of critical assets is still valid:

```astro
<head>
  <link rel="preload" href="/fonts/inter.woff2" as="font" type="font/woff2" crossorigin />
  <link rel="preload" href="/images/hero.avif" as="image" />
</head>
```

## Animation Performance

Motion is a first-class design tool — tilt, parallax, glow and layered depth are legitimate. Prefer `transform`/`opacity` (GPU-composited) when the effect is equivalent, for performance; layout properties, 3D and parallax are allowed when the effect genuinely needs them. The one hard floor: degrade under `prefers-reduced-motion`.

```css
/* Preferred when the effect is equivalent — GPU composited */
.animate { transition: transform 0.3s, opacity 0.3s; }

/* Fine when the effect needs it (layout/paint) — still honour prefers-reduced-motion */
.animate { transition: width 0.3s, height 0.3s, top 0.3s; }
```

### Accordion / expand panels

Disclosure patterns (FAQ and similar): native `<details>`, CSS `grid-template-rows: 0fr` ↔ `1fr`, or an animated height — all fine as long as they honour `prefers-reduced-motion`. Island guidance: `references/islands-architecture.md`.

## Checklist

- [ ] LCP image has `loading="eager"` + `fetchpriority="high"`
- [ ] All images have explicit `width` and `height`
- [ ] Below-fold images use `loading="lazy"` (default)
- [ ] Fonts use `display=swap`
- [ ] Only necessary islands use `client:load`
- [ ] Below-fold islands use `client:visible`
- [ ] Initial JS ~< 50 KB (advisory; animation libraries inside the island, not in the entry)
- [ ] Motion prefers `transform`/`opacity` where equivalent; layout/3D/parallax/`height` are fine when the effect needs them
- [ ] `prefers-reduced-motion` handled for all animations (hard floor)
