# SEO / GEO Playbook

Scoped to a client-rendered SPA (Vite) deployed behind Vercel; most checks carry over to any
stack. Extends the `seo-geo-baseline` pack in SKILL.md.

## 1. Indexability

```bash
# robots.txt body, and the status of sitemap.xml, for each environment given.
# One Python line, not curl: in PowerShell `curl` is an alias of Invoke-WebRequest and rejects `-s`.
python -X utf8 -c "import sys,urllib.request as u;[ (print('==',b),print(u.urlopen(b+'/robots.txt',timeout=15).read().decode('utf-8','replace')),print('sitemap.xml ->',u.urlopen(b+'/sitemap.xml',timeout=15).status)) for b in sys.argv[1:] ]" ${project.stagingUrl} ${project.productionUrl}
```

If the project generates its sitemap at build time (e.g. `vite-plugin-sitemap`), a missing route usually means the generator's dynamic-route list is incomplete — check the plugin config in `vite.config.ts` before hand-editing `dist/sitemap.xml`.

`robots.txt` policy for AI crawlers — a sane default: allow GPTBot, ClaudeBot, PerplexityBot and Google-Extended on public marketing pages; deny them on authenticated app routes.

## 2. Per-page metadata

Metadata needs a single injection point. Find the project's head-management layer (`react-helmet-async`, a framework `<Head>`, or similar) and its shared SEO component — grep `${paths.componentsRoot}` for `canonical` — then extend that component instead of scattering `<meta>` tags per route.

Per route: title (≤ 60 chars), meta description (≤ 160 chars), canonical, Open Graph image, Twitter card.

```tsx
// shape of that shared component, whatever the project calls it
<Seo
  title="…"
  description="…"
  canonical="${project.productionUrl}/…"
  ogImage="${project.productionUrl}/og/….png"
/>
```

## 3. Structured data (JSON-LD)

For AI / GEO citation readiness. Inject `<script type="application/ld+json">…</script>` via Helmet on relevant pages.

Schemas to consider:
- `Organization` — homepage
- `WebSite` + `SearchAction` — homepage (Sitelinks Search Box)
- `BreadcrumbList` — every nested page
- `FAQPage` — FAQ sections
- `Product` / `Service` — pricing or service pages
- `Article` — blog/changelog entries

Source data: extract to pure data modules with no component imports, so the JSON-LD stays single-source-of-truth without dragging render code into the chunk that emits it.

## 4. PSI SEO score

```bash
python -X utf8 -c "import json,sys,urllib.request;c=json.load(urllib.request.urlopen(sys.argv[1],timeout=120))['lighthouseResult']['categories'];print({k:round(v['score']*100) for k,v in c.items()})" "https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=${project.productionUrl}&strategy=mobile&category=seo&category=accessibility&locale=${project.locale}"
```

Pass: the value configured at `.graph-powers/config.json::gates.lighthouse.seo`. Full invocation,
including the 429 fallback: `psi-api.md`.

## 5. Crawl-readiness checks

| Check | Command / Pattern |
|---|---|
| All public routes return 200 | `python -X utf8 -c "import urllib.request as u,sys;[print(u.urlopen(sys.argv[1]+r,timeout=10).status, r) for r in ('/','/pricing','/about')]" ${project.productionUrl}` |
| `<title>` populated server-side | `python -X utf8 -c "import re,sys,urllib.request;h=urllib.request.urlopen(sys.argv[1],timeout=15).read().decode('utf-8','replace');print(re.findall(r'<title[^>]*>([^<]*)',h) or 'NO TITLE IN FIRST BYTE')" ${project.productionUrl}` (Vite SPA: empty until JS hydrates — relies on Vercel's bot rendering or a pre-render plugin) |
| Open Graph absolute URLs | `grep -rn 'property="og:image"' ${paths.frontendRoot}` — confirm absolute URLs, not relative |
| H1 per page | Every route has exactly one `<h1>` |
| Internal links use real `<a>` not `onClick` divs | `grep -rn 'onClick.*history\.\|onClick.*navigate' ${paths.frontendRoot}` |

## 6. AI / GEO specifics

- `llms.txt` at root — concise project description for LLM context. See `concepts/seo-geo-vite-spa`.
- AI crawler-allow in `robots.txt` (see § 1).
- Structured data on every page (`§ 3`).
- Avoid client-only content for SEO-critical pages — use Vite SSR plugin or Vercel's edge rendering for landing pages.

## 7. Vite SPA-specific gotchas

| Gotcha | Mitigation |
|---|---|
| `<title>` empty on first byte (no SSR) | Add per-route Helmet; Vercel bot detection serves rendered HTML |
| `sitemap.xml` missing dynamic routes | Configure `dynamicRoutes` in `vite-plugin-sitemap` |
| Hash-based routing | Switch to a path-based router — crawlers need real paths, not `#/fragments` |
| Lazy chunks 404 after deploy | Listen for `vite:preloadError` at the app entry point and reload once |
