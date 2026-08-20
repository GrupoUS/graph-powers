---
name: performance-optimization
description: "Method for runtime, build, database and bundle performance, plus the OWASP security baseline and SEO/GEO. Covers Core Web Vitals, memory and GC, heap snapshots, N+1 and index gaps, sitemaps and structured data. Loaded by /perf. Not for a wrong result, which is a defect."

---

# Performance Optimization

Single performance skill for four goals: speed, database performance, security baseline, and SEO/GEO baseline.

## Core Rules

1. Measure before changing code.
2. Change one bottleneck at a time.
3. Re-measure with the same tool and scenario.
4. Keep fixes minimal (KISS) and only for active issues (YAGNI).

## Packs

Pick one pack per run:

| Pack                    | Use When                                                                        | Minimum Output                                   |
| ----------------------- | ------------------------------------------------------------------------------- | ------------------------------------------------ |
| `performance-core`      | Slow load, sluggish interaction, high API p95, large bundle                     | before/after metrics + exact fixes               |
| `database-performance`  | Slow API p95, N+1 queries, SELECT *, missing indexes, pool exhaustion, cold starts | before/after query metrics + exact fixes       |
| `security-baseline`     | Release hardening, OWASP sanity, dependency and header checks                   | findings by severity + mitigation                |
| `seo-geo-baseline`      | Search visibility, crawlability, AI citation readiness                          | indexability/schema/CWV report + action list     |
| `vercel-rum`            | Real-user CWV per route + traffic shape + post-deploy regression catch          | per-route CWV table + flagged regressions + fixes |

## Baseline Commands

```bash
bun run type-check
bun run lint:check
bun run build
# Set ANALYZE=true for this one run, in the form your shell accepts:
#   bash/zsh   ANALYZE=true <pm> run build
#   PowerShell $env:ANALYZE="true"; <pm> run build
#   cmd        set ANALYZE=true && <pm> run build
# Inline assignment before a command is POSIX-only syntax.
```

## Live Docs Lookup (Context7)

Before applying optimizations, fetch live docs:
- `drizzle-orm` → resolve library ID, query for query optimization, prepared statements, `inArray()` batch patterns
- `@tanstack/react-query` → resolve for `staleTime`, `gcTime`, `skipToken`, polling patterns
- `recharts` → resolve for lazy loading and tree-shaking patterns

---

## Pack Commands

### `database-performance`

Use when API p95 is high, queries are slow, or the DB is a suspected bottleneck.

**Step 1: Connection Pool Audit**

Find where the project constructs its connection pool (search `${paths.backendRoot}` for `new Pool(`) and check the constructor options:

```typescript
// Every bound set explicitly — sized for a serverless/pooled Postgres
const pool = new Pool({
  connectionString,
  max: 10,                        // stay under the provider's connection ceiling; leave headroom for other services
  idleTimeoutMillis: 30_000,      // 30s — close idle connections to avoid stale sockets and idle billing
  connectionTimeoutMillis: 10_000, // 10s — fail fast on cold starts instead of hanging the request
});
```

Report as findings if any of `max`, `idleTimeoutMillis`, or `connectionTimeoutMillis` are absent.

> **Note:** serverless Postgres drivers generally accept the same constructor options as `pg.Pool`, but the `options` field for statement_timeout (`options: '-c statement_timeout=30000'`) varies by driver and version — verify against the runtime before applying.

**Step 2: Query Anti-Pattern Scan**

```bash
# SELECT * (missing column specification)
# Grep tool: pattern `db\.select\(\)\.from`, path ${paths.backendRoot}, glob *.ts

# N+1 pattern: look for await db. inside a for/while loop
# Grep tool: pattern `for \(|while \(` under ${paths.backendRoot}, glob *.ts, with -A 5,
# then look for `await db.` in the surrounding lines. A shell `grep | grep` needs a
# binary Windows does not have, and the pipe would filter an error message instead.
```

| Severity | Pattern | Fix |
|----------|---------|-----|
| High | `db.select().from(table)` with no columns | Specify `db.select({ col1, col2 })` |
| High | `await db.` inside `for` loop | Pre-fetch all IDs → single query with `inArray()` |
| Medium | List queries without `.limit()` | Add `.limit(N)` — cap at 100 for list endpoints |
| Medium | Sequential independent queries | Wrap in `Promise.all([...])` |

**Step 3: Index Audit**

For every FK column (`.references(() => table.id)`), confirm a corresponding `index("...").on(table.fkCol)` exists in the same table definition.

```bash
# Grep tool: pattern `\.references\(`, then `index\(`, path ${paths.schemaRoot}, glob *.ts
```

**Step 4: Prepared Statement Candidates**

Identify hot-path queries for Drizzle `.prepare()`:

```typescript
import { placeholder } from 'drizzle-orm';

const getUserByExternalIdStmt = db
  .select({ id: users.id, externalId: users.externalId, email: users.email, role: users.role })
  .from(users)
  .where(eq(users.externalId, placeholder('externalId')))
  .limit(1)
  .prepare('get_user_by_external_id');

const [user] = await getUserByExternalIdStmt.execute({ externalId: 'ext_xxx' });
```

Use prepared statements for: every-request queries, frequently-called service functions, and scheduler/cron hot loops.

**Step 5: Batch Operations**

```typescript
// Instead of: for (const item of items) { await db.insert(table).values(item) }
await db.insert(table).values(items); // single round-trip

// Instead of: for (const id of ids) { await db.select().from(t).where(eq(t.id, id)) }
const results = await db.select().from(t).where(inArray(t.id, ids));
const map = new Map(results.map(r => [r.id, r]));
```

**Step 6: Report**

```markdown
## Database Performance Report

Pack: database-performance

### Connection Pool
| Setting | Current | Recommended | Status |
|---------|---------|-------------|--------|
| max | unset | 10 | FAIL |
| idleTimeoutMillis | unset | 30000 | FAIL |
| connectionTimeoutMillis | unset | 10000 | FAIL |

### Query Anti-Patterns
| # | File | Line | Issue | Severity |
|---|------|------|-------|----------|

### Index Gaps
| Table | FK Column | Has Index? |
|-------|-----------|------------|

### Changes
1. [change] -> [impact]

### Risks / Follow-up
- [remaining risk]
```

**Bottleneck Routing (DB-specific)**

```
API p95 > 140ms  → run Step 1 (pool) + Step 2 (query scan)
Cold start delay → check pool.connectionTimeoutMillis + database region latency
N+1 detected     → batch with inArray() or join
SELECT * detected → specify needed columns in db.select({ col1, col2 })
Pool exhaustion  → lower max or add idleTimeoutMillis
Sequential queries → wrap independent queries in Promise.all
```

---

### `performance-core`

> Full PSI API reference: `references/psi-api.md`
> Full Unlighthouse reference: `references/unlighthouse.md`

**Step 1: Measure with PSI API (primary)**

```bash
# Mobile audit
curl -s "https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=${project.stagingUrl}&strategy=mobile&category=performance&category=accessibility&category=best-practices&category=seo&locale=${project.locale}" -o <scratch>/psi-mobile.json

# Desktop audit
curl -s "https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=${project.stagingUrl}&strategy=desktop&category=performance&category=accessibility&category=best-practices&category=seo&locale=${project.locale}" -o <scratch>/psi-desktop.json

# Parse scores
python -X utf8 -c "import json,sys;c=json.load(open(sys.argv[1],encoding='utf-8'))['lighthouseResult']['categories'];print({k:round(v['score']*100) for k,v in c.items()})" <scratch>/psi-mobile.json
```

**Step 2: Local Lighthouse (for auth pages or deeper analysis)**

```bash
npx lighthouse ${project.stagingUrl} --preset=desktop --port=9222 --chrome-flags="--headless=new --disable-gpu --no-first-run --no-default-browser-check --disable-background-networking --disable-extensions"
npx lighthouse ${project.productionUrl} --preset=desktop --port=9333 --chrome-flags="--headless=new --disable-gpu --no-first-run --no-default-browser-check --disable-background-networking --disable-extensions"
```

**Step 3: React Doctor** (render/effect health, 0–100 score)

```bash
${tooling.packageManager} run doctor    # when the project wires a React health scanner
```

React render/effect health scanners (`react-doctor` and similar) are **optional external tools**, not part of this plugin. When the project declares one, run it from the project's own script and follow the tool's own documentation for flags, config file and suppressions. Do not re-derive its rule list here — a copied rule table goes stale the first time the tool ships a release.

> Remediation follows the same atomic-task loop as any other finding: one rule, one fix, re-measure.

---

### `security-baseline`

```bash
bun audit
gitleaks detect --source .
curl -I ${project.stagingUrl}
```

Check at least: access control, injection resistance, auth flows, misconfiguration, secrets.

---

### `seo-geo-baseline`

> Technical SEO (robots, sitemap, metadata, indexability): `references/seo-playbook.md`
> Content SEO (keywords, on-page, schema, internal linking, local): `references/seo-content.md`

**Step 1: PSI API for SEO scores**

```bash
curl -s "https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=${project.productionUrl}&strategy=mobile&category=seo&category=accessibility&locale=${project.locale}" | jq '{seo: (.lighthouseResult.categories.seo.score * 100 | round), a11y: (.lighthouseResult.categories.accessibility.score * 100 | round)}'
```

**Step 2: Robots and Sitemap**

```bash
curl ${project.stagingUrl}/robots.txt
curl ${project.productionUrl}/robots.txt
curl -I ${project.stagingUrl}/sitemap.xml
curl -I ${project.productionUrl}/sitemap.xml
```

**Step 3: Local Lighthouse (optional, for deeper SEO audits)**

```bash
npx lighthouse ${project.stagingUrl} --preset=desktop --port=9222 --chrome-flags="--headless=new --disable-gpu --no-first-run --no-default-browser-check --disable-background-networking --disable-extensions"
```

Use distinct explicit ports for sequential runs (`9222` for staging, `9333` for production).
If Lighthouse cannot find Chrome automatically, set `CHROME_PATH` to your local Chrome/Chromium executable.

Check at least: metadata, structured data, canonical links, robots, sitemap, CWV.

---

### `vercel-rum`

> Full reference: `references/vercel-data.md`

Real-user CWV from Vercel Speed Insights + traffic from Vercel Analytics, used as cross-check against synthetic PSI after deploy.

**Important constraint**: Vercel public CLI/REST API does NOT expose Speed Insights / Web Analytics query endpoints (verified against `bunx vercel api list` on CLI v53). Only intake routes (`/_vercel/insights/*`) exist. This pack uses the dashboard UI + CSV export. For programmatic CWV, see `references/vercel-data.md § 5` (Vercel Drains, Pro/Ent) or `§ 6` (`web-vitals` self-instrument).

**Pre-flight**

```bash
bunx vercel whoami    # auth; else bunx vercel login
```

Read `.graph-powers/config.json::vercel.{projectId,teamId,scope}` — set once via `bunx vercel link` (copy from `.vercel/project.json`).

If empty → fail with: "Run `bunx vercel link --yes --project <name> --scope <team-or-user>` then copy IDs into `.graph-powers/config.json::vercel`."

**Step 1: Print dashboard URLs**

```bash
# Read both JSON files with the Read tool, or one Python line — `jq` is a separate install
# with no Windows story, and `$( )` is POSIX substitution that cmd.exe passes through literally.
python -X utf8 -c "import json;print(json.load(open('.graph-powers/config.json',encoding='utf-8')).get('vercel',{}).get('scope',''), json.load(open('.vercel/project.json',encoding='utf-8')).get('projectName',''))"

echo "Speed Insights: https://vercel.com/${SCOPE}/${PROJECT_NAME}/speed-insights"
echo "Web Analytics:  https://vercel.com/${SCOPE}/${PROJECT_NAME}/analytics"
```

User opens both. Reads p75 LCP / INP / CLS per route + top pages. Last 7d default.

**Step 2: CSV export (when > 5 routes)**

Speed Insights dashboard → "Export" (top-right) → CSV → `/tmp/vercel-cwv.csv`.

```bash
# Flag routes failing thresholds
python -X utf8 -c "import csv,sys;[print(f'FAIL {r[0]:<40} LCP={r[1]} INP={r[2]} CLS={r[3]} n={r[4]}') for i,r in enumerate(csv.reader(open(sys.argv[1],newline='',encoding='utf-8'))) if i and (float(r[1])>2500 or float(r[2])>200 or float(r[3])>0.1)]" <path-to-csv>
```

(Schema: column order may vary. Check header row first; map columns route/lcp/inp/cls/samples accordingly.)

**Step 3: Cross-reference local code**

For each failing route:
1. Map `routeId` → file path (under `${paths.frontendRoot}`).
2. Read the file. Identify:
   - Heavy synchronous imports → candidate for `lazy()` + `<Suspense>`.
   - `<img>` without `width`/`height` → CLS contributor.
   - Inline third-party scripts → script-blocking LCP.
   - Long lists without virtualization → candidate for a list-virtualization library.
3. Recommend exact fix per row.

**Step 4: Cross-check with PSI**

Run `performance-core` pack (PSI mobile + desktop) on same prod URL. Build comparison:

| Route | RUM LCP | Lab LCP (PSI) | Verdict |
|---|---|---|---|
| / | 1800ms | 1500ms | PASS — RUM aligns with lab |
| /app/dashboard | 4200ms | 1900ms | INVESTIGATE — real users much slower than lab; check device mix / network throttling |

PSI bad + RUM good → PSI config aggressive; investigate but don't act on lab alone. PSI good + RUM bad → real-user device or network issue (mobile networks in the audience's region are often slower than PSI's "Slow 4G" profile).

**Step 5: Report**

```markdown
## Vercel RUM Report (last 7d)

Pack: vercel-rum

### Dashboard links
- Speed Insights: <url>
- Web Analytics: <url>

### Per-route CWV (p75) — from CSV export
| Route | RUM LCP | RUM INP | RUM CLS | Samples | Lab LCP (PSI) | Status |
|---|---|---|---|---|---|---|

### Traffic shape
| Top page | Pageviews | Bounce |
|---|---|---|

### Failing routes — recommended fixes
1. `<route>` — `${paths.frontendRoot}/<file>:<line>` — [fix description]

### Risks / Follow-up
- [remaining risk]
```

**Bottleneck Routing (Vercel-RUM-specific)**

```
LCP > 2500ms     → check vendor-react / route chunk size; lazy-load below-fold
INP > 200ms      → React Doctor for unstable handlers; split heavy event handlers
CLS > 0.1        → audit images for explicit width/height; check ad/embed reflow
Empty dashboard  → Speed Insights toggle off, or < 24h since enable, or zero traffic
Single mega-row  → <SpeedInsights route={...}> not wired correctly (verify root layout)
```

---

## Targets

**Source of truth = `.graph-powers/config.json::gates`.** Read the configured values before each run — a project may set them stricter than the web.dev "Good" line, and the configured gate is what you pass. If the project also runs a Lighthouse gate in CI, keep its config in sync with these keys.

| Metric      | Project gate (`config.json`) | web.dev "Good" (context) |
| ----------- | ---------------------------- | ------------------------ |
| LCP         | `gates.lcp`                  | ≤ 2500ms |
| INP         | `gates.inp`                  | ≤ 200ms |
| CLS         | `gates.cls`                  | ≤ 0.1 |
| FCP         | not gated (warn only)        | ≤ 1800ms |
| TBT         | not gated (warn only)        | ≤ 200ms |
| Lighthouse Perf / A11y / BP / SEO | `gates.lighthouse.*`        | — |
| Initial JS (gzip, per chunk) | `gates.initialJsKb`         | — |
| API p95     | project-defined              | — |
| Real-user p75 LCP per route (RUM) | ≤ `gates.lcp`               | ≤ 2500ms |

## Bottleneck Routing

- Initial load slow → inspect critical rendering path and bundle split.
- Interaction slow → inspect re-renders and long handlers.
- API slow → inspect N+1 patterns and missing indexes. Use `database-performance` pack.
- Memory growth → inspect subscription/listener/interval cleanup.
- DB pool exhaustion → tune `max`, `idleTimeoutMillis`, `connectionTimeoutMillis` in Pool constructor.

## High-Value Fixes

**Frontend:** Route-level lazy loading for heavy pages and modals. Remove unstable props/callbacks causing unnecessary re-renders. Virtualize long lists.

**Backend/DB:** Remove N+1 queries with joins or batch strategy. Ensure FK columns are indexed. Avoid unbounded list queries.

## Guardrails

- Do not optimize based on intuition only.
- Do not over-memoize cheap operations.
- Do not expand scope to unrelated refactors.
- Do not claim improvement without before/after evidence.

## Report Template

```markdown
## Optimization Report

Pack: [performance-core|security-baseline|seo-geo-baseline|memory-optimization]

| Metric | Before | After | Delta |
| ------ | ------ | ----- | ----- |
| ...    | ...    | ...   | ...   |

### Changes
1. [change] -> [impact]

### Risks / Follow-up
- [remaining risk]
```

---

## Memory Optimization Pack (absorbed from retired `/optimize-memory-usage`)

Use when investigating memory leaks, OOM crashes, GC pause times, or high baseline heap. Applies across browser (Chrome DevTools), Node (`--inspect`, heap snapshots), and native runtimes (Valgrind).

### 11-step playbook

1. **Memory analysis and profiling** — profile current memory usage with appropriate tools (Chrome DevTools, Node `--inspect`, Valgrind); identify leaks and consumption hotspots; analyze GC patterns; capture baseline; document allocation hotspots and growth patterns over time.
2. **Memory leak detection** — set up leak detection per runtime; capture heap snapshots and diff over intervals; track DOM-node leaks in browser; verify event-listener cleanup; identify growing memory patterns.
3. **Garbage collection optimization** — configure GC settings; tune Node heap sizes and GC flags; monitor pause times and frequency; alerting on GC pressure; optimize object lifecycles to reduce pressure.
4. **Memory pool / object reuse** — implement object pooling for frequently allocated objects; buffer pools in Node; reuse DOM elements/components in frontend; design memory-efficient data structures (circular buffers, sparse arrays); pre-allocate to reduce runtime allocation overhead.
5. **String / text optimization** — string interning for frequently used strings; optimize concatenation and manipulation; minimize duplication; consider compression for large text data.
6. **Database connection optimization** — connection pooling with appropriate limits; timeouts + cleanup; query result cache memory; monitor connection memory overhead; leak detection on connections.
7. **Frontend memory optimization** — component lifecycle + cleanup; event-listener cleanup; lazy-load images and components; minimize bundle size + code split; monitor browser memory patterns.
8. **Backend memory optimization** — optimize request handling + cleanup; streaming for large data; appropriate memory limits + monitoring; middleware/request lifecycle; memory-efficient data processing.
9. **Container / deployment optimization** — container memory limits; optimize Docker layers; production memory monitoring; memory-based auto-scaling; alerting + thresholds.
10. **Memory monitoring + alerting** — real-time dashboards; usage alerts and thresholds; production leak detection; metrics over time; automated optimization testing.
11. **Production memory management** — graceful pressure handling; memory-based health checks; usage trending and analysis; emergency cleanup procedures; ongoing pattern monitoring.

### Measure before/after

Always capture baseline (RSS, V8 heap used, GC pause p50/p95) before optimization and again after. Report the delta — do not claim improvement without numbers.

### Anti-patterns

- Tuning GC flags without baseline measurement → can regress
- Reusing pooled objects across request scopes → cross-request data leakage
- Increasing heap limit instead of fixing the leak → defers OOM, doesn't fix it
- Detecting leaks only in dev → production leak patterns differ (real traffic, real session lengths)
