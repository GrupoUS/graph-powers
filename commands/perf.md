---
description: "Performance audits + optimization. Modes (positional arg) — default: runtime audit (PSI/Lighthouse) · build: bundle analysis, code splitting, build-tool tuning · db: pool audit, N+1 scan, index gaps, prepared-statement candidates · vercel: real-user CWV + traffic from Vercel Speed Insights/Analytics · doctor: React Doctor render/effect health audit (local/advisory). Pass URL/scope/strategy after the mode token."
workflow_type: orchestrator-workers
---

# /perf — Performance & Optimization

**ARGUMENTS**: $ARGUMENTS

> **Read before step 0 — never reconstruct these from memory:** `${CLAUDE_PLUGIN_ROOT}/references/shared/000-config-loader.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/005-superpowers-bootstrap.md`
> Read `${CLAUDE_PLUGIN_ROOT}/references/shared/010-quality-gates.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/015-verification-gate.md`
> Read `${CLAUDE_PLUGIN_ROOT}/references/shared/070-parallel-agent-spawn.md`

> First positional arg = mode. Examples:
> ```
> /perf                            # default — runtime audit (PSI/Lighthouse)
> /perf url=https://example.com    # runtime audit on specific URL
> /perf strategy=mobile            # runtime, mobile only
> /perf build                      # bundle/build-tool optimization
> /perf db                         # database performance (N+1, indexes, pool)
> /perf vercel                     # real-user CWV + traffic (Vercel Speed Insights/Analytics)
> /perf doctor                     # React Doctor render/effect health audit (local/advisory)
> /perf compare baseline.json after.json    # compare two runs
> ```
> All modes use **Skill `performance-optimization`** + agent `graph-powers:performance-optimizer`.

---

## 0. Setup (every mode)

```typescript
Skill("superpowers:using-superpowers");              // meta — bootstrap (per `${CLAUDE_PLUGIN_ROOT}/references/shared/005-superpowers-bootstrap.md`)
Skill("superpowers:verification-before-completion"); // every PASS/FAIL claim must cite captured score / exit code
Skill("performance-optimization");                    // the project performance + security + SEO knowledge
```

Read `.graph-powers/config.json`:
- `${project.stagingUrl}` → default audit target (override via `url=`)
- `${tooling.buildTool}` → build-tool selection (vite / webpack / esbuild / rollup / turbopack / astro / next / etc.)
- `${tooling.typeChecker}` / `${tooling.testRunner}` / `${tooling.packageManager}`
- `${gates.lighthouse}` / `${gates.lcp}` / `${gates.cls}` / `${gates.inp}` / `${gates.initialJsKb}` → pass thresholds

If the project keeps an SEO supplement in `${rulesDir}/`, load it — route specifics and content rules this plugin cannot know.

---

## 1. Mode dispatch

Parse first positional token from `$ARGUMENTS`:

| Token | Section |
|---|---|
| (none) / `runtime` / `routes` / `all` | § 2 (runtime audit) |
| `fix` | § 2 + auto-fix loop (§ 2.5) |
| `compare` | § 2.6 (compare two PSI runs) |
| `vercel` / `rum` | § 2.7 (Vercel Speed Insights + Analytics) |
| `build` / `bundle` | § 3 (build/bundle optimization) |
| `db` / `database` | § 4 (database performance) |
| `doctor` / `react` | § 2.8 (React Doctor render/effect audit) |

Other tokens after mode are kwargs (`url=`, `strategy=`, `scope=`, etc.).

---

## 2. Runtime audit (default mode)

Google PageSpeed Insights v5 (zero-dependency). Falls back to Lighthouse CLI when quota exceeded.

### 2.1 Measurement tool selection

```
1. Try PSI API (preferred — no Chrome needed). No key needed for ad-hoc use
   (25k/day free). For automated/repeated runs, append `&key=<your PSI API key>` to
   dodge the per-IP 429 (key from https://console.cloud.google.com → PageSpeed
   Insights API). Endpoint: https://www.googleapis.com/pagespeedonline/v5/runPagespeed
2. If HTTP 429 (quota) → Lighthouse CLI:
   ${tooling.packageManager} dlx lighthouse URL --output=json --chrome-flags="--headless=new --no-sandbox --disable-gpu --no-first-run --disable-extensions"
3. For full crawl → Unlighthouse:
   ${tooling.packageManager} dlx unlighthouse --site URL --throttle --samples 1
```

> **Lighthouse Performance score weights (v10+, for prioritising fixes):** TBT 30% · LCP 25% · CLS 25% · FCP 10% · Speed Index 10%. TBT + LCP + CLS = 80% — fix those first. Default emulation: mobile, 4× CPU slowdown, simulated Slow-4G. When the project keeps a Lighthouse CI config, run it with `numberOfRuns: 3` (median) against `${project.stagingUrl}` — a single run is noise.

### 2.2 Default config

```yaml
KEY_ROUTES: detect from router files (${paths.frontendRoot}/routes/, app/, pages/) or use user-provided list
THRESHOLDS:
  performance:    { pass: ${gates.lighthouse.performance}, warn: 50 }
  accessibility:  { pass: ${gates.lighthouse.accessibility}, warn: 70 }
  best-practices: { pass: ${gates.lighthouse.bestPractices}, warn: 70 }
  seo:            { pass: ${gates.lighthouse.seo}, warn: 80 }
CWV_TARGETS:
  LCP: ${gates.lcp}ms
  CLS: ${gates.cls}
  INP: ${gates.inp}ms
  FCP: 1800ms
  TBT: 200ms
```

### 2.3 Execute

Call PSI API for the resolved URL with each selected strategy (mobile + desktop unless overridden).

### 2.4 Output

```markdown
## PSI Report: {URL}

### Scores ({strategy})
| Category | Score | Status |
|---|---|---|
| Performance | XX | PASS / WARN / FAIL |
| Accessibility | XX | PASS / WARN / FAIL |
| Best Practices | XX | PASS / WARN / FAIL |
| SEO | XX | PASS / WARN / FAIL |

### Core Web Vitals
| Metric | Value | Target | Status |
|---|---|---|---|
| FCP | X.Xs | 1.8s | PASS / FAIL |
| LCP | X.Xs | {gates.lcp}ms | PASS / FAIL |
| CLS | X.XX | {gates.cls} | PASS / FAIL |
| INP | Xms | {gates.inp}ms | PASS / FAIL |
| TBT | Xms | 200ms | PASS / FAIL |

### Top Opportunities
| Audit | Savings | Display |
|---|---|---|
| unused-javascript | XXXms | Est savings XXX KiB |
```

### 2.5 Auto-fix loop (`/perf fix`)

Before the batch spawn, invoke `Skill("superpowers:dispatching-parallel-agents")` to enforce distinct scope + shared return contract across the per-route agents.

1. Measure baseline against all key routes.
2. Identify routes with Performance < threshold.
3. Spawn 1 `graph-powers:performance-optimizer` agent per failing route, all in **single message**, each with `isolation: "worktree"`.
4. Each agent prompt includes: route-specific scores, CWV, top opportunities, failing audits, scope (which files/components), task (read web rules from `${rulesDir}/design.md`, fix top 3 opportunities by `savings_ms`, run quality gates per `${CLAUDE_PLUGIN_ROOT}/references/shared/010-quality-gates.md`, report changes).
5. After all agents return: re-measure and verify improvements via `Skill("superpowers:verification-before-completion")` — capture the new PSI scores as evidence before claiming "regression fixed".

Skip routes already at threshold.

### 2.6 Compare (`/perf compare baseline.json after.json`)

Load both JSON outputs. Display delta table: Δ score per category, Δ CWV per metric, regressions highlighted.

### 2.7 Vercel mode — `/perf vercel`

Cross-check synthetic PSI (§ 2) against real-user CWV from Vercel Speed Insights and Web Analytics. Run after every prod deploy.

Full reference: `Skill("performance-optimization")` → `${CLAUDE_PLUGIN_ROOT}/skills/performance-optimization/references/vercel-data.md`.

**Important constraint**: Vercel's public CLI/REST API does NOT expose Speed Insights or Web Analytics query endpoints (verified against `bunx vercel api list`). The `<Analytics>` + `<SpeedInsights>` components POST to intake-only routes (`/_vercel/insights/*`); only the dashboard reads aggregated data. Programmatic options: Vercel Drains (Pro/Enterprise) or self-instrument with `web-vitals`. See `${CLAUDE_PLUGIN_ROOT}/skills/performance-optimization/references/vercel-data.md § 5` and `§ 6`.

**Pre-flight**

```bash
bunx vercel whoami
```

If not authed → fail with: "Run `bunx vercel login` (or set VERCEL_TOKEN)."

The dashboard URL needs the team/user scope and the project slug. Both come from the local link state that `bunx vercel link` writes (`.vercel/project.json`, gitignored). If the project is not linked → fail with: "Run `bunx vercel link` first."

**Step 1 — Print dashboard links + run synthetic baseline**

```bash
python -X utf8 -c "import json,pathlib,subprocess;r=subprocess.run(['vercel','whoami'],capture_output=True,text=True);s=r.stdout.strip() if r.returncode==0 else '';p=pathlib.Path('.vercel/project.json');n=json.loads(p.read_text(encoding='utf-8')).get('projectName','') if p.is_file() else '';print(f'Speed Insights: https://vercel.com/{s}/{n}/speed-insights\nWeb Analytics:  https://vercel.com/{s}/{n}/analytics') if s and n else print('not linked — run `vercel link` first')"
```

One Python line rather than five shell constructs. The shell version used `$( )`, `2>/dev/null`,
`[ -n … ]` and a line continuation — none of which exist in cmd.exe — and depended on `jq`, which
§ 5 already admits may be absent.

> If either value is empty, do not guess a slug — say the project is not linked and let the user open the dashboard.
> A wrong dashboard URL costs more than a missing one.

Open both. Note p75 LCP/INP/CLS per route + top pages.

In parallel, run § 2 (PSI mobile + desktop) on the same prod URL for synthetic lab data. Provides cross-check baseline.

**Step 2 — Build comparison table**

```markdown
## Vercel + PSI Cross-check Report

### Per-route p75
| Route | RUM LCP (Vercel) | Lab LCP (PSI) | RUM INP | RUM CLS | Samples | Status |
|---|---|---|---|---|---|---|

(Fail RUM when LCP > ${gates.lcp}ms, INP > ${gates.inp}ms, CLS > ${gates.cls})
```

If `<SpeedInsights>` not yet aggregating (< 24h since deploy), skip RUM column and note "no data yet, retry after 24h".

**Step 3 — CSV export option**

When > 5 routes need analysis, use the dashboard's "Export" button and save the CSV wherever the
user keeps scratch files — ask, or use `python -X utf8 -c "import tempfile,os;print(os.path.join(tempfile.gettempdir(),'vercel-cwv.csv'))"`. Do not
hardcode `/tmp`: it does not exist on Windows, and this repository's own rule forbids absolute
machine paths. Then parse it:

```bash
python -X utf8 -c "import csv,sys;[print(f'{r[0]:<40} LCP={r[1]} INP={r[2]} CLS={r[3]} n={r[4]}') for i,r in enumerate(csv.reader(open(sys.argv[1],newline='',encoding='utf-8'))) if i and (float(r[1])>2500 or float(r[2])>200 or float(r[3])>0.1)]" <path-to-csv>
```

**Step 4 — Failing routes → fix path**

For each FAIL row: map `routeId` → the route file under `${paths.frontendRoot}` → recommend lazy-load / image dimensions / virtualization / third-party defer.

Optionally chain into `/perf fix` scoped to those routes for auto-remediation.

**Cross-check rule**: PSI good + RUM bad → device mix / network conditions issue (real users on slower connections than PSI's "Slow 4G"). PSI bad + RUM good → PSI config aggressive; investigate but don't act on lab alone.

**For programmatic CWV access** (CI gates, automated reporting): see `${CLAUDE_PLUGIN_ROOT}/skills/performance-optimization/references/vercel-data.md § 5` (Drains, Pro/Ent) or `§ 6` (`web-vitals` self-instrumentation).

---

## 2.8 Static health mode — `/perf doctor`

Static code-health audit of the client layer: render and effect correctness, dead code, dependency
risk. **Advisory, not a CI gate** — this pass finds candidates, it does not decide what ships.

The scanner is an **external tool the project chooses** (`react-doctor` for React codebases, or
whatever its ecosystem provides). This plugin does not vendor one, does not restate its rule list,
and does not pin its version — a copied rule table is stale the day the tool ships a release.

Read the command from `tooling.commands`, or from the project's own script (`doctor`, `analyze`,
`audit`). If the project declares none, say so and stop: running a linter nobody configured produces
findings nobody agreed to.

### Remediation loop (atomic)

1. **Baseline.** Run the scanner. Record the score and the error/warning counts verbatim — this is
   the evidence the closing claim is measured against (per `Skill("superpowers:verification-before-completion")`).
2. **Triage.** Group findings by **file**, not by rule, and sort by severity. Honour the project's
   existing suppressions; re-fixing a deliberately suppressed rule is noise, not progress.
3. **Fix one file.** All related fixes for a single file, in one pass. Never batch unrelated files.
4. **Validate that file.** Format, type check, then the file's own test if it has one — all from
   `tooling.commands`.
5. **Re-scan.** Counts must move monotonically. A plateau means the remaining findings need
   judgement, not another loop.
6. **Stop.** When what is left is deliberate. Do **not** chase a score to 100 — past a point the
   tool is measuring its own opinions.

For a false positive, prefer the narrowest control the tool offers: an inline suppression with a
written reason beats a config-wide rule disable, which beats turning off a category.

---

## 3. Build mode — `/perf build`

Generic across build tools. Detects `${tooling.buildTool}` from config + project files.

### 3.1 Build system detection

Read config + project files to confirm:
- Build tool: `vite`, `webpack`, `rollup`, `esbuild`, `turbopack`, `astro`, `next`, `nuxt`, etc.
- Type checker: `tsgo`, `tsc`, `swc`, `babel`
- Bundler-specific config files (`vite.config.*`, `webpack.config.*`, `rollup.config.*`, `astro.config.*`, etc.)
- Build scripts in `package.json`

### 3.2 Performance baseline

```bash
# Build timings. `time` is a bash keyword — PowerShell has Measure-Command with different
# semantics, cmd has nothing — so the timing is done by the thing being timed's own runner.
python -X utf8 -c "import subprocess,sys,time;t=time.perf_counter();c=subprocess.run(sys.argv[1:]).returncode;print(f'elapsed={time.perf_counter()-t:.1f}s exit={c}')" ${tooling.packageManager} run build

# Repeat the same line for the warm-cache build, and for the type check if it is separate.

# The 20 largest build outputs, from whichever output directory exists.
python -X utf8 -c "import pathlib,sys;d=next((p for p in map(pathlib.Path,sys.argv[1:]) if p.is_dir()),None);print('no build output found') if not d else [print(f'{f.stat().st_size/1024:9.1f} KB  {f.relative_to(d)}') for f in sorted((f for f in d.rglob('*') if f.is_file()),key=lambda f:-f.stat().st_size)[:20]]" ${paths.frontendRoot}/dist/assets ${paths.frontendRoot}/.output/public build
```

The shell version of that last one had a bug on every platform, not just Windows: `|` binds tighter
than `||`, so `a || b || c | sort | head` parses as `a || b || (c | sort | head)` and the common
case — the first listing succeeding — was never sorted or truncated.

Document: clean vs incremental times, bundle sizes per chunk, type-check time, slowest phases from build log.

### 3.3 Bundle analysis

Run an appropriate visualizer for the build tool. Generic options:
- Vite / Rollup: `rollup-plugin-visualizer` (or `vite-bundle-visualizer`)
- Webpack: `webpack-bundle-analyzer`
- esbuild: `esbuild-visualizer`
- Generic: `source-map-explorer` on the production build

Identify: largest chunks + top contributors, duplicate dependencies across chunks, splitting opportunities.

### 3.4 Caching strategy

**Dependency pre-bundling cache** (Vite `.vite/deps`, Webpack `.cache`, etc.) — verify it exists and is populated.
**TypeScript incremental** — `tsBuildInfoFile` set, `incremental: true`.
**CI/CD cache** — package manager cache, build-tool cache, type-checker cache, between pipeline runs.

### 3.5 Code splitting & lazy loading

- Route-based splitting: heavy page components lazy-loaded with `<Suspense>`/equivalent
- Heavy deps (charts, PDF, rich-text editors, code editors) dynamically imported
- Vendor chunks separated explicitly via `manualChunks` (or equivalent)
- Chunk size warning limit set (default 500KB)

### 3.6 Asset optimization

- Images: WebP / AVIF, lazy loading, correct sizing, explicit `width`/`height` for CLS
- CSS: framework purge active in production builds
- Compression: gzip + brotli at server / CDN / proxy
- Tree shaking: `sideEffects: false` for pure utility packages

### 3.7 Build-tool-specific recommendations

Apply patterns appropriate to the detected `${tooling.buildTool}`. Examples:

```
target: 'es2020'           # modern target = smaller output
minify: 'esbuild'           # esbuild faster than terser
cssMinify: true
sourcemap: false            # disable in prod (or 'hidden')
chunkSizeWarningLimit: 500
optimizeDeps.include: [stable deps]
```

For TypeScript-heavy projects: `skipLibCheck: true`, `moduleResolution: 'bundler'`, project references for monorepos > 200 files/package, avoid `paths` aliases that force re-resolution of full module graph.

### 3.8 Dev mode

- Dev transformer uses fast path (esbuild / SWC) — never Babel in dev
- HMR / Fast Refresh active
- Cheap source maps for fastest rebuilds

### 3.9 CI/CD optimization

```yaml
cache:
  - <package-manager-cache>
  - <build-tool-pre-bundle-cache>
  - <type-checker-incremental-cache>

# Parallel jobs where independent
jobs:
  type-check:  ${tooling.typeChecker}
  lint:        ${tooling.linter}
  test:        ${tooling.testRunner}
  build:       ${tooling.packageManager} run build  # after type-check
```

### 3.10 Output

```markdown
## Build Optimization Report

### Baseline
| Metric | Value |
|---|---|
| Clean build time | Xs |
| Incremental build time | Xs |
| Type check time | Xs |
| Total JS (gzip) | XXX KB |
| Total CSS (gzip) | XX KB |
| Largest chunk | XXX KB — name |

### Findings
| # | Issue | Impact | Effort |

### Applied Optimizations
| Optimization | Before | After | Δ |

### Remaining Opportunities
[ranked by impact]

### Budgets (set in CI to fail on regression)
| Asset class | Budget |
| Total JS gzip | ${gates.initialJsKb}KB |
| Largest chunk | 500KB |
```

---

## 4. Database mode — `/perf db`

Generic across SQL databases (Postgres / MySQL / SQLite).

### 4.1 Connection pool audit

Locate the connection / pool initialization (`${paths.libRoot}/db.*`, `lib/database.*`, etc.). Verify:
- Pool size appropriate for serverless vs long-running
- Idle timeout configured (avoid orphan connections)
- Max lifetime / recycle settings
- For Postgres: `prepare: false` if using a serverless driver that doesn't support prepared statements (else mismatch causes runtime errors)

### 4.2 N+1 scan

Grep across `${paths.backendRoot}` and service layer:
- `for (...) { await db.query(...) }` — classic N+1
- Loops over arrays calling `findOne` / `select` per item
- Missing `IN (...)` batch queries
- Missing relation eager-loading where used in tight loops

Report each hit with file:line + suggested batched alternative.

### 4.3 SELECT * scan

```bash
# Grep tool: pattern `select \*`, path `${paths.backendRoot}`, glob `*.{ts,js,sql}`,
# output_mode `content`, head_limit 50. Not a shell `grep | head` — neither binary exists
# on Windows, and the pipe would take the first 50 lines of an error message.
```

For each: verify whether all columns are actually used in the call site. Suggest column projection.

### 4.4 Index gap check

For Postgres / MySQL:
- List all FK columns: `SELECT conname, conrelid::regclass, conkey FROM pg_constraint WHERE contype = 'f'`
- For each FK column → check if an index exists. Missing FK index = sequential scan on cascade / join.
- List columns frequently in WHERE clauses (grep app code for repeated filters) without supporting index.
- Composite indexes: WHERE a = ? AND b = ? requires `(a, b)` not `(a)` + `(b)`.

### 4.5 Prepared-statement candidates

Grep for repeated parameterized queries (same SQL shape, different params). Suggest preparing them or moving to a query builder that auto-prepares.

### 4.6 RLS / row-level security perf (Postgres)

When RLS policies use subqueries or function calls:
- Verify the helper function is `STABLE` (cacheable per query) not `VOLATILE`
- Confirm `security definer` functions set `search_path`
- Avoid policies that force per-row function evaluation in hot loops

### 4.7 EXPLAIN ANALYZE walk

Pick 3 hottest queries (from app logs or `pg_stat_statements`). For each:

```sql
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) <query>;
```

Flag: seq scans on big tables, sort spilling to disk, nested loops over many rows, missing index usage.

### 4.8 Output

```markdown
## DB Performance Report

### Pool config
| Property | Value | Recommendation |
|---|---|---|
| Pool size | X | … |
| Idle timeout | Xs | … |
| Prepare | true/false | … |

### N+1 hits
| File:line | Pattern | Suggested fix |

### SELECT * hits
| File:line | Columns actually used |

### Missing indexes
| Table.column | Reason | Migration SQL |

### EXPLAIN ANALYZE highlights
[3 worst queries with annotations]
```

For database-specific deeper guidance, defer to the host database/performance skill declared in project rules.

---

## 5. Error handling

| Error | Action |
|---|---|
| PSI API HTTP 429 | Retry once; fall back to Lighthouse CLI |
| URL unreachable | Report; suggest checking deployment / DNS |
| `jq` not installed | Parse JSON via `${tooling.packageManager}` `-e` script or Python |
| Unlighthouse fails | Fall back to multi-route PSI scan |
| Build fails during § 3 | Run `${tooling.typeChecker}` first to surface compiler errors |
| DB inaccessible during § 4 | Run static-only checks (grep + index check from migration files) |
