# Troubleshooting

## Build Errors

### "Unexpected export" in frontmatter (a compiler gotcha)

A template literal in the frontmatter with a `/` immediately after `}` — the compiler reads it as a regex and the parse breaks:

```astro
---
// BROKEN: a `}` followed directly by `/` inside a template literal
const url = `${base}/route`;

// WORKS: split it or join it
const url = [base, "route"].join("/");
---
```

This holds for any `}/` sequence in a frontmatter template literal, not just URLs.

### Zod 4 (Astro 6) — schema errors

- `z.string().email()` / `.url()` → **`z.email()`** / **`z.url()`** (top-level formats).
- Import `z` from **`astro/zod`** — `astro:content`/`astro:schema` are deprecated.
- `.default()` changed for transforms — review `.default()` + `.transform()` combinations.

### "Missing export" when importing an adapter

Adapter majors drop subpath entry points. `@astrojs/vercel` v10 is the worked example: `import vercel from "@astrojs/vercel"`, never `/serverless` or `/static`.

### "Cannot find module" / Import Errors

```
Cannot find module './Component.astro'
```

**Causes & Fixes:**
- Wrong file path → Check case sensitivity (Linux is case-sensitive)
- Missing file extension → Always include `.astro`, `.tsx`, `.ts`
- Missing dependency → Run `bun install`

### Content Collection Errors

```
[content] Unable to find collection "speakers"
```

**Fixes:**
- Ensure directory exists: `src/content/speakers/`
- At least one file must exist in the directory
- File must be valid JSON/YAML/MD
- Restart dev server after adding new collections

### TypeScript Errors

```bash
# Check for type errors
bun run check
```

Common fixes:
- Add `interface Props` for component props
- Use `unknown` instead of `any`
- Import types with `import type {}`
- Check `tsconfig.json` extends correct base

### Vite/Build Errors

```
[vite] Pre-transform error: Failed to resolve import
```

**Fixes:**
- Clear cache: `rm -rf node_modules/.vite`
- Reinstall: `rm -rf node_modules && bun install`
- Check import paths are correct

## Hydration Errors

### "Hydration mismatch"

React expects server HTML to match client render.

**Common causes:**
1. **Date/time rendering** — Server and client in different timezones
   ```tsx
   // ❌ Renders different on server vs client
   <p>{new Date().toLocaleString()}</p>

   // ✅ Use client:only or suppressHydrationWarning
   <DateDisplay client:only="react" />
   ```

2. **Random values**
   ```tsx
   // ❌ Different on server and client
   <div id={`el-${Math.random()}`}>

   // ✅ Use deterministic IDs
   <div id={`el-${props.index}`}>
   ```

3. **Browser-only APIs**
   ```tsx
   // ❌ window undefined on server
   const width = window.innerWidth;

   // ✅ Guard with typeof check
   const width = typeof window !== 'undefined' ? window.innerWidth : 1024;
   ```

4. **Conditional rendering based on client state**
   ```tsx
   // ❌ Differs between server/client
   {localStorage.getItem('theme') === 'dark' && <DarkMode />}

   // ✅ Use useEffect for client-only state
   const [theme, setTheme] = useState('light');
   useEffect(() => {
     setTheme(localStorage.getItem('theme') || 'light');
   }, []);
   ```

### "client:* directive on .astro component"

**Fix:** Client directives only work on framework components (React/Vue/Svelte), not `.astro` files.

## Styling Issues

### Tailwind Classes Not Working

1. **Check `@import "tailwindcss"`** in global.css
2. **Check the Vite plugin** in astro.config.mjs (under `vite.plugins`, NOT under `integrations`):
   ```js
   vite: { plugins: [tailwindcss()] }
   ```
3. **Check `@theme` tokens** — Custom colors need `--color-` prefix
4. **Clear cache**: `rm -rf node_modules/.vite && bun run dev`

### "Unknown utility class" from `@apply` in a scoped style

The `<style>` block is missing `@reference "tailwindcss"` (or `@reference` pointing at the CSS file that holds `@theme`) at the top — see `references/styling-tailwind.md`.

### Scoped Styles Not Applying

- Styles in `.astro` files only target elements in THAT component
- Child component elements need `:global()` or `is:global`
- Tailwind utility classes are always global

### CLS (Layout Shift)

- Set `width` and `height` on all `<img>` and `<Image>` elements
- Use `aspect-ratio` for responsive containers
- Avoid dynamic content that changes layout after load

## Dev Server Issues

### Port Already in Use

```powershell
# Windows (PowerShell)
Get-NetTCPConnection -LocalPort 4321 | Select-Object OwningProcess
Stop-Process -Id <PID>
```

```bash
# Git Bash / Linux
netstat -ano | grep 4321   # Windows: PID in the last column -> taskkill //PID <PID> //F
lsof -i :4321 && kill -9 <PID>   # Linux/macOS
```

### HMR Not Working

- Check file is in `src/` directory
- Restart dev server
- Clear Vite cache: `rm -rf node_modules/.vite`

### Slow Development Build

- Large `public/` images slow dev server → Optimize images
- Too many Content Collection entries → Use filtering
- Heavy dependencies → Consider lighter alternatives

## Deployment Issues

### Build Works Locally But Fails on CI

- Check Node.js version matches
- Ensure `bun.lockb` is committed
- Check environment variables are set
- Verify build command is correct: `bun run build`

### Missing Assets in Production

- Files in `src/` → Processed by Vite (hashed filenames)
- Files in `public/` → Copied as-is (original filenames)
- Check base path in `astro.config.mjs`

## Performance Debugging

```bash
# Build analysis
bun run build 2>&1 | grep -E "\.js|\.css|total"

# Type check
bun run check

# Lighthouse
bunx lighthouse http://localhost:4321 --preset=desktop
```

## Quick Diagnostic Commands

```bash
# Full health check
bun run check && bun run build

# Clear all caches
rm -rf node_modules/.vite dist .astro

# Fresh start
rm -rf node_modules && bun install && bun run dev
```
