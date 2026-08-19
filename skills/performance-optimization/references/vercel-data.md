# Vercel Web Analytics + Speed Insights — Data Access

Reference for `Skill("performance-optimization")` pack `vercel-rum` and `/perf vercel`.

## TL;DR

Vercel public CLI / REST API (verified against `bunx vercel api list` on CLI v53, May 2026) **does not expose** Web Analytics or Speed Insights query endpoints. The `@vercel/analytics` + `@vercel/speed-insights` packages POST to same-origin intake routes (`/_vercel/insights/*`, `/_vercel/speed-insights/*`); only the Vercel dashboard reads the aggregated data.

Programmatic-data options (in priority order):

| Path | Plan | Effort |
|---|---|---|
| 1. Dashboard manual review | All | Low |
| 2. Dashboard CSV export | All | Low |
| 3. Vercel Drains (real-time event export) | Pro / Enterprise | Medium |
| 4. Self-instrument with `web-vitals` package | All | Medium |

`/perf vercel` defaults to **Path 1** (dashboard URLs) + cross-check with PSI lab data. Path 3 / 4 documented for teams that need programmatic CWV.

---

## 1. Pre-flight

```bash
bunx vercel --version          # require >= 53
bunx vercel whoami             # confirms auth; else: bunx vercel login
```

CI / non-interactive: set `VERCEL_TOKEN` (create at https://vercel.com/account/tokens). All `vercel` calls auto-pick it up.

## 1.5 Speed Insights wiring + official thresholds

A project on Vercel may already mount `<SpeedInsights>` + `<Analytics>` somewhere in its root layout or a telemetry module — grep `${paths.frontendRoot}` for `SpeedInsights` first and audit what is there rather than re-adding it. Official `@vercel/speed-insights/react` props worth knowing:

| Prop | Use |
|---|---|
| `route` | Route **template** (e.g. `/app/orders/$id`), not the resolved URL — groups RUM per-route. Wrong value → all routes collapse to one dashboard row. |
| `sampleRate` (0–1) | Send only a fraction of events. Default = all. Lower it only if you hit the Hobby 50k events/month cap (Pro/Ent billed by usage). |
| `beforeSend(event)` | Mutate/redact/drop events before send (PII). Strip URL search params and hashes here; never ship query strings / hashes to Vercel. |
| `endpoint` / `scriptSrc` | Override the intake URL / script URL. Leave default (same-origin `/_vercel/speed-insights/*`). |

**Metrics reported:** LCP, INP, CLS, FCP, TTFB (+ legacy FID), rolled into a **Real Experience Score (RES)**. Official "Good" thresholds (RUM p75): LCP ≤ 2500ms · INP ≤ 200ms · CLS ≤ 0.1 · FCP ≤ 1800ms · TTFB ≤ 800ms. Score bands: 0–49 poor · 50–89 needs-improvement · 90–100 good.

> **The gate is `.graph-powers/config.json::gates`**, not the web.dev line above — a project commonly configures thresholds stricter than "Good". Use the official thresholds only as context.

## 2. Project / team IDs

For a repo not yet linked:

```bash
cd <repo>
bunx vercel link --yes --project <name> --scope <team-or-user>
cat .vercel/project.json    # { "orgId": "team_xxx", "projectId": "prj_xxx", "projectName": "..." }
```

Then persist into `.graph-powers/config.json::vercel`:

```json
"vercel": {
  "projectId": "prj_xxx",
  "teamId": "team_xxx",
  "scope": "<team-slug-or-username>"
}
```

`scope` is the URL slug used in dashboard URLs (`https://vercel.com/<scope>/<project>/...`). For personal accounts the slug is `<username>s-projects`.

## 3. Dashboard URLs (Path 1 — primary)

Build directly from config:

```bash
SCOPE="$(jq -r '.vercel.scope' .graph-powers/config.json)"
PROJECT_NAME=<project>-web    # from .vercel/project.json::projectName

echo "Speed Insights: https://vercel.com/${SCOPE}/${PROJECT_NAME}/speed-insights"
echo "Web Analytics:  https://vercel.com/${SCOPE}/${PROJECT_NAME}/analytics"
```

Open in browser. Read p75 LCP/INP/CLS per route, top pages, traffic shape. Copy numbers into `/perf vercel` output table manually.

## 4. CSV export (Path 2)

Dashboard → Speed Insights → "Export" button (top-right). CSV includes per-route p75 LCP/INP/CLS + sample count. Save to `/tmp/vercel-cwv.csv`, parse:

```bash
# example, schema may evolve
awk -F',' 'NR>1 { printf "%-40s LCP=%s INP=%s CLS=%s n=%s\n", $1, $2, $3, $4, $5 }' \
  /tmp/vercel-cwv.csv
```

Web Analytics dashboard also exports CSV (top pages, referrers, devices, countries).

## 5. Vercel Drains (Path 3 — programmatic, Pro/Ent only)

Drains pipe raw analytics events to your HTTP endpoint in real time. Cost: ~$0.50 / GB.

```bash
# Available API
bunx vercel api "/v1/drains" -X GET --scope=<team>
# create / update / delete via PATCH/POST/DELETE on same path
```

Configure a drain to deliver Speed Insights events to a custom endpoint (e.g., a tiny serverless function that writes to your own database). Then `/perf vercel` queries your DB instead of Vercel.

Out of scope for free tier — skip unless team upgrades.

## 6. Self-instrument with `web-vitals` (Path 4 — DIY)

If programmatic data needed without Drains:

```bash
cd ${paths.frontendRoot} && bun add web-vitals
```

```tsx
// ${paths.frontendRoot}/telemetry/cwv-self.tsx
import { onCLS, onINP, onLCP, onFCP, onTTFB } from "web-vitals";

const send = (m: { name: string; value: number; id: string; rating: string }) => {
  navigator.sendBeacon("/api/cwv", JSON.stringify({ ...m, route: location.pathname, ts: Date.now() }));
};

if (typeof window !== "undefined") {
  onCLS(send); onINP(send); onLCP(send); onFCP(send); onTTFB(send);
}
```

Add a route under `${paths.backendRoot}` that exposes `POST /api/cwv` and writes to its own table; `/perf vercel` then queries that table via a project script. Trade-off: you own all the storage / aggregation / privacy compliance.

## 7. CSP

Endpoints same-origin: `/_vercel/insights/view`, `/_vercel/insights/event`, `/_vercel/speed-insights/vitals`. No external `connect-src` needed. If a CSP is added later: include `'self'` in `connect-src`, `script-src` (script auto-injected by Vercel from same origin).

## 8. Verify after deploy

1. Open production URL → DevTools → Network.
2. Confirm 200 for `/_vercel/insights/script.js`.
3. Confirm 1× POST `/_vercel/insights/view` per route navigation.
4. Confirm POST `/_vercel/speed-insights/vitals` after first interaction (LCP/INP).
5. Wait 24–48h for dashboard aggregation; first manual readout may show empty.

## 9. Common errors

| Error | Cause | Fix |
|---|---|---|
| `vercel: command not found` | CLI missing | `bun add -d vercel` at repo root |
| HTTP 401 on `vercel api` | Token invalid / expired | `bunx vercel login` again or rotate `VERCEL_TOKEN` |
| Dashboard shows "No data yet" | Speed Insights toggle off, or < 24h since enable, or no traffic | Vercel dashboard → project → Speed Insights → Enable; wait + drive traffic |
| All routes show same URL | `<SpeedInsights route={...}>` not wired correctly | Confirm `useMatches()[-1]?.routeId` returns route template, not full URL |
| 404 on `/v1/speed-insights/...` | Path doesn't exist in public API | Use Path 1/2/3/4 instead — public REST API has no read endpoint |
