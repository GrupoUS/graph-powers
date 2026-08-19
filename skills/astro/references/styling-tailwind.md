# Styling & Tailwind CSS v4

## Scoped Styles in Astro

`<style>` tags in `.astro` files are automatically scoped:

```astro
<style>
  h1 { color: red; }  /* Only affects THIS component's h1 */
</style>
```

Astro adds unique `data-astro-cid-*` attributes to scope CSS.

### Global Styles

```astro
<!-- Method 1: is:global attribute -->
<style is:global>
  body { margin: 0; }
</style>

<!-- Method 2: :global() selector -->
<style>
  :global(.nav-link) { color: blue; }
</style>

<!-- Method 3: Import CSS file -->
---
import '../styles/global.css';
---
```

### class:list Utility

Conditionally apply classes:

```astro
---
const { isActive, size = 'md' } = Astro.props;
---
<div class:list={[
  'card',                    // Always applied
  { active: isActive },      // Applied if truthy
  `size-${size}`,            // Dynamic string
  ['extra', 'classes'],      // Array (flattened)
]}>
```

### define:vars

Pass server variables to CSS:

```astro
---
const accentColor = 'oklch(0.72 0.15 85)';
const spacing = '2rem';
---
<style define:vars={{ accentColor, spacing }}>
  .card {
    border-color: var(--accentColor);
    padding: var(--spacing);
  }
</style>
```

## Tailwind CSS v4 Integration

### Setup (Vite Plugin — Recommended)

```js
// astro.config.mjs
import { defineConfig } from "astro/config";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  vite: {
    plugins: [tailwindcss()],
  },
});
```

**No `tailwind.config.js` needed.** Tailwind v4 uses CSS-first configuration.

### CSS-First Configuration with @theme

All custom tokens go in your CSS file:

```css
/* src/styles/global.css */
@import "tailwindcss";

@theme {
  /* Colors — name tokens by role, not by hue, so a rebrand is one file */
  --color-surface: #101018;
  --color-surface-raised: #1d1d2a;
  --color-surface-overlay: #2e2e40;
  --color-accent: #4f7cff;
  --color-accent-light: #7fa0ff;
  --color-accent-dark: #2b4fb8;
  --color-text-primary: #FAFAF9;
  --color-text-muted: #94A3B8;

  /* Fonts — one display face and one body face; use whatever the project loads */
  --font-sans: 'Inter', system-ui, sans-serif;
  --font-display: 'Inter Tight', 'Inter', system-ui, sans-serif;

  /* Custom spacing, shadows, etc. */
  --shadow-accent-glow: 0 0 20px oklch(0.62 0.18 265 / 0.3);
}
```

Every key becomes a utility: `--color-accent` gives `bg-accent`/`text-accent`/`border-accent`,
`--font-display` gives `font-display`, `--shadow-accent-glow` gives `shadow-accent-glow`.

Use in templates:

```html
<div class="bg-surface text-accent font-display">
<p class="text-text-muted font-sans">
<button class="bg-accent text-surface hover:bg-accent-light">
```

### Custom Utilities via @utility

```css
@utility glass-card {
  background: color-mix(in oklab, var(--color-surface-raised) 80%, transparent);
  backdrop-filter: blur(12px);
  border: 1px solid color-mix(in oklab, var(--color-accent) 20%, transparent);
}

@utility accent-glow {
  box-shadow: var(--shadow-accent-glow);
}

@utility bg-mesh {
  background:
    radial-gradient(ellipse at 20% 50%, color-mix(in oklab, var(--color-accent) 8%, transparent) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 20%, color-mix(in oklab, var(--color-surface) 90%, transparent) 0%, transparent 50%);
}
```

### `@apply` in a scoped `<style>` requires `@reference`

Scoped styles in `.astro` (and CSS Modules / Vue SFCs) are processed in isolation — without `@reference`, `@apply`/`@variant` fail with "unknown utility class":

```astro
<style>
  @reference "tailwindcss"; /* or @reference "../styles/global.css" to see the @theme tokens */
  h1 { @apply text-2xl font-serif; }
</style>
```

Prefer utilities directly in the markup; reach for `@apply` only when unavoidable.

### Tailwind v4 Key Differences from v3

| Feature | v3 | v4 |
|---------|----|----|
| Config | `tailwind.config.js` | `@theme {}` in CSS |
| Plugin | `@astrojs/tailwind` | `@tailwindcss/vite` |
| Import | `@tailwind base/components/utilities` | `@import "tailwindcss"` |
| Custom colors | `theme.extend.colors` in JS | `--color-*` in `@theme` |
| Custom utilities | `plugin()` in JS | `@utility` in CSS |
| Arbitrary values | `bg-[#123456]` | Still works, but prefer `@theme` tokens |

### Responsive Design

```html
<!-- Mobile-first breakpoints -->
<div class="px-4 md:px-8 lg:px-16">
<h1 class="text-2xl md:text-4xl lg:text-6xl">

<!-- Container queries (v4) -->
<div class="@container">
  <div class="@md:flex @lg:grid">
```

### Dark mode

Whether a site has one theme or two is the project's decision — check its own rules in
`${rulesDir}/` before adding a toggle. A single-theme site defines every colour once in `@theme` and
is done. A site with both defines the light values in `@theme` and overrides the same token names
under `@media (prefers-color-scheme: dark)` and a `[data-theme]` selector, so components never
branch on theme themselves.

## CSS Best Practices for Astro

1. **Use `@theme` tokens** — Never hardcode hex values
2. **Prefer utility classes** — Over custom CSS when possible
3. **Scoped styles for component-specific CSS** — Astro auto-scopes
4. **Global CSS for base styles only** — `global.css` imported in layout
5. **`class:list` for conditional classes** — Cleaner than ternaries
6. **Avoid `!important`** — Use specificity or scoping instead
