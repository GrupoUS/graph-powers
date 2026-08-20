# SEO / GEO Playbook

Scoped to a client-rendered SPA (Vite) deployed behind Vercel; most checks carry over to any
stack. Extends the `seo-geo-baseline` pack in SKILL.md.

## 1. Indexability

```bash
# robots.txt allows crawl
curl -s ${project.stagingUrl}/robots.txt
curl -s ${project.productionUrl}/robots.txt

# sitemap exists + reachable
curl -I ${project.stagingUrl}/sitemap.xml
curl -I ${project.productionUrl}/sitemap.xml
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
curl -s "https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=${project.productionUrl}&strategy=mobile&category=seo&category=accessibility&locale=${project.locale}" | jq '{
      seo: (.lighthouseResult.categories.seo.score * 100 | round),
      a11y: (.lighthouseResult.categories.accessibility.score * 100 | round)
    }'
```

Pass: the value configured at `.graph-powers/config.json::gates.lighthouse.seo`.

## 5. Crawl-readiness checks

| Check | Command / Pattern |
|---|---|
| All public routes return 200 | `python -X utf8 -c "import urllib.request as u,sys;[print(u.urlopen(sys.argv[1]+r,timeout=10).status, r) for r in ('/','/pricing','/about')]" ${project.productionUrl}` |
| `<title>` populated server-side | `curl -s ${project.productionUrl}/ \| grep -oP '<title>\K[^<]+'` (Vite SPA: empty until JS hydrates — relies on Vercel's bot rendering or pre-render plugin) |
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
