---
description: "Make something measurably faster, lighter or more findable — slow page, slow query, oversized bundle, poor Core Web Vitals, weak SEO or security baseline. Use when the user says something takes too long, feels sluggish, times out, or that the bundle is too big. Modes (positional) — default runtime audit · build · db · vercel · doctor · seo · sec. Pass URL, scope or strategy after the mode. Do not use when the output is wrong rather than slow (/debug)."
workflow_type: orchestrator-workers
---

# /perf — Performance & Optimization

**ARGUMENTS**: $ARGUMENTS

> **Read before step 0 — never reconstruct these from memory:** `${CLAUDE_PLUGIN_ROOT}/references/shared/000-config-loader.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/005-method-bootstrap.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/015-verification-gate.md`
> Read `${CLAUDE_PLUGIN_ROOT}/references/shared/070-parallel-agent-spawn.md` and `${CLAUDE_PLUGIN_ROOT}/references/shared/010-quality-gates.md` only for `fix`, the one mode that spawns agents and runs gates.

## What this file is, and is not

This file is the **procedure**: which mode, what to run, in what order, what comes out, what to do
when it fails. It holds no thresholds and no fix catalogue.

- **The method and the numbers** — measure-first rules, the target table, the pattern-to-fix
  catalogue, the five packs — are `Skill("performance-optimization")`, loaded on every run.
- **The exact invocation of a tool** is that tool's reference, read on the branch that uses it:
  `skills/performance-optimization/references/psi-api.md` (PSI, Lighthouse CLI, Unlighthouse) ·
  `…/references/vercel-data.md` (Speed Insights, Web Analytics) ·
  `…/references/seo-playbook.md` and `…/references/seo-content.md` (SEO / GEO).

One procedure, one home. When a step below feels thin, the depth is in one of those files — do not
restate it here.

---

## 0. Setup (every mode)

```typescript
Skill("performance-optimization"); // method, targets, pack catalogue
```

Every PASS/FAIL claim follows `015-verification-gate.md`: captured measurement or exit code first.

From `.graph-powers/config.json`: `${project.stagingUrl}` (default target, override with `url=`) ·
`${tooling.buildTool}` · `${tooling.packageManager}` · literal `${tooling.commands.*}` gates ·
`${gates.lighthouse.*}` · `${gates.lcp}` · `${gates.cls}` · `${gates.inp}` · `${gates.initialJsKb}`.

**The gate is whatever the config says**, never the web.dev line — a project commonly configures
stricter. If `${rulesDir}/` carries an SEO or performance supplement, load it: route specifics and
content rules this plugin cannot know.

---

## 1. Mode dispatch

First positional token of `$ARGUMENTS`. Everything after it is `key=value` (`url=`, `strategy=`,
`scope=`).

| Token | Section | What it does |
|---|---|---|
| (none) / `runtime` / `routes` / `all` | § 2 | synthetic audit of one or more URLs |
| `fix` | § 2.5 | audit, then one agent per failing route |
| `compare` | § 2.6 | delta between two saved runs |
| `vercel` / `rum` | § 2.7 | real-user CWV, cross-checked against the lab |
| `doctor` / `react` | § 2.8 | render/effect health from the project's own scanner |
| `build` / `bundle` | § 3 | build time, chunk sizes, splitting, caching |
| `db` / `database` | § 4 | pool, N+1, `select *`, index gaps, prepared statements |
| `seo` | § 5 | `seo-geo-baseline` pack |
| `sec` / `security` | § 5 | `security-baseline` pack |

---

## 2. Runtime audit (default mode)

### 2.1 Measure

The ladder, and the reason to step down it: **PSI API** (no Chrome, no install) → **Lighthouse CLI**
(PSI returned 429, the page needs auth, or a custom throttle is required) → **Unlighthouse** (every
route in one pass). Invocation, parsing and the 429 fallback: `psi-api.md`.

Routes: read the router files under `${paths.frontendRoot}` (`routes/`, `app/`, `pages/`) or take
the user's list. Strategies: mobile **and** desktop unless `strategy=` says otherwise.

### 2.2 Prioritise what the score actually weighs

Lighthouse performance score, v10 and later: **TBT 30% · LCP 25% · CLS 25% · FCP 10% · Speed Index
10%.** TBT + LCP + CLS is 80% of it — fix those three first, in savings order. Pass/fail comes from
`${gates.lighthouse.*}` and `${gates.lcp}` / `${gates.cls}` / `${gates.inp}`; the target table with
its web.dev context lives in `Skill("performance-optimization") § Targets`.

A single run is noise. For anything that gates a merge, take the median of three.

### 2.3 Report

```markdown
## PSI Report: {URL} ({strategy})

| Category | Score | Gate | Status |
|---|---|---|---|
| Performance / Accessibility / Best Practices / SEO | XX | ${gates.lighthouse.*} | PASS / FAIL |

| Metric | Value | Target | Status |
|---|---|---|---|
| LCP / INP / CLS / FCP / TBT | … | ${gates.lcp} / ${gates.inp} / ${gates.cls} / 1800ms / 200ms | PASS / FAIL |

### Top opportunities (savings order — this is the fix order)
| Audit | Est. saving | Detail |
```

Field data absent (`loadingExperience` empty) means too little CrUX traffic. Report the lab numbers
and say the field data is missing — not that it passed.

### 2.4 Verdict

Every row above is PASS, FAIL, or **NOT MEASURED**. A run that could not be taken is never reported
as a pass, per `015-verification-gate.md`.

### 2.5 Auto-fix loop (`/perf fix`)

Follow `070-parallel-agent-spawn.md` for the batch — distinct scope, one shared return contract.

1. Measure the baseline across the key routes. **Capture it**; it is what the closing claim is
   measured against.
2. Take only the routes under threshold. Skip the rest, and say how many were skipped.
3. One `graph-powers:performance-optimizer` per failing route, **all in a single message**, each
   with `isolation: "worktree"` — one writer per file, per `070-parallel-agent-spawn.md § 7`.
4. Each prompt carries the seven sections of `references/execution-floor.md § 4`, and inside them:
   that route's scores, CWV and failing audits; its file scope; the project's own web rules from
   `${rulesDir}/`; the top 3 opportunities by `overallSavingsMs`; the gates from
   `010-quality-gates.md`.
5. Re-measure with the same tool and the same strategy. Report before → after → delta. The evidence
   gate closes it: no delta, no claim.

### 2.6 Compare (`/perf compare baseline.json after.json`)

Delta per category and per metric, regressions first. The one-liner is in `psi-api.md § Read a saved
report`.

### 2.7 Vercel — real-user CWV (`/perf vercel`)

Run it after every production deploy. **The procedure is `vercel-data.md § 0`** — pre-flight,
dashboard URLs, the PSI cross-check, the CSV path when there are more than five routes, and what
each lab-versus-RUM disagreement means. Do not restate it; run it.

The constraint that shapes the whole mode: Vercel's public CLI and REST API expose **no** Speed
Insights or Web Analytics read endpoint (verified against `vercel api list`, CLI v53). Only the
dashboard reads aggregated data. Programmatic access is Drains (Pro/Enterprise) or self-instrumenting
with `web-vitals` — `vercel-data.md § 5` and `§ 6`.

```markdown
## Vercel + PSI cross-check

| Route | RUM LCP (p75) | Lab LCP | RUM INP | RUM CLS | Samples | Verdict |
|---|---|---|---|---|---|---|
```

`Verdict` is PASS, or one of the two disagreements named in `vercel-data.md § 0.4`. Under 24h since
the deploy: no RUM column, say "no data yet, retry after 24h", and do not fill it with zeros.

### 2.8 Static health (`/perf doctor`)

Render and effect correctness, dead code, dependency risk. **Advisory, never a CI gate** — it finds
candidates, it does not decide what ships.

The scanner is the project's own (`react-doctor` for React, or whatever its ecosystem provides).
Read the command from `tooling.commands`, or from a project script named `doctor` / `analyze` /
`audit`. **The project declares none → say so and stop.** Running a linter nobody configured
produces findings nobody agreed to, and this plugin does not vendor a scanner or pin its rule list.

The loop, and it is atomic on purpose:

1. **Baseline** — run it, record score and error/warning counts verbatim.
2. **Triage** — group by **file**, not by rule; sort by severity; honour existing suppressions.
3. **Fix one file** — every related finding in that file, one pass. Never batch unrelated files.
4. **Validate that file** — format, type check, then its own test, all from `tooling.commands`.
5. **Re-scan** — counts must move. A plateau means what remains needs judgement, not another loop.
6. **Stop** when what is left is deliberate. Do not chase 100: past a point the tool measures its
   own opinions.

False positive → the narrowest control the tool offers. An inline suppression with a written reason
beats a config-wide disable, which beats turning off a category.

---

## 3. Build mode — `/perf build`

### 3.1 Detect

`${tooling.buildTool}` from config, confirmed against what is on disk: the build config file
(`vite.config.*`, `webpack.config.*`, `rollup.config.*`, `astro.config.*`, `next.config.*`), the
type checker (the resolved native `tsgo` or framework-specific command; never legacy `tsc`) and the `package.json` scripts.

### 3.2 Baseline

```bash
# Time a build. `time` is a bash keyword — PowerShell's Measure-Command differs and cmd has nothing,
# so the timing is done by the thing being timed.
python -X utf8 -c "import subprocess,sys,time;t=time.perf_counter();c=subprocess.run(sys.argv[1:]).returncode;print(f'elapsed={time.perf_counter()-t:.1f}s exit={c}')" ${tooling.packageManager} run build

# Repeat for the warm-cache build, and for the type check when it is a separate script.

# The 20 largest build outputs, from whichever output directory exists.
# `|` binds tighter than `||`, so the shell version of this line silently left the common case
# unsorted and untruncated on every platform.
python -X utf8 -c "import pathlib,sys;d=next((p for p in map(pathlib.Path,sys.argv[1:]) if p.is_dir()),None);print('no build output found') if not d else [print(f'{f.stat().st_size/1024:9.1f} KB  {f.relative_to(d)}') for f in sorted((f for f in d.rglob('*') if f.is_file()),key=lambda f:-f.stat().st_size)[:20]]" ${paths.frontendRoot}/dist/assets ${paths.frontendRoot}/.output/public build
```

Record: clean build, incremental build, type-check time, per-chunk sizes, slowest phases from the log.

### 3.3 Analyse the bundle

Run the visualizer that matches the build tool — `rollup-plugin-visualizer` (Vite/Rollup),
`webpack-bundle-analyzer`, `esbuild-visualizer`, or `source-map-explorer` on the production build.
Identify the largest chunks and their top contributors, dependencies duplicated across chunks, and
splitting opportunities.

### 3.4 Checklist

| Area | What must be true |
|---|---|
| Splitting | heavy pages lazy-loaded behind `<Suspense>` or equivalent; charts, PDF, editors dynamically imported; vendor chunks explicit (`manualChunks`); chunk-size warning set |
| Caching | dependency pre-bundle cache populated (`.vite/deps`, `.cache`); `incremental: true` + `tsBuildInfoFile`; CI caches the package manager, the build tool and the type checker between runs |
| Assets | WebP/AVIF, lazy loading, correct sizing, explicit `width`/`height` (CLS); CSS purge active in production; gzip **and** brotli at the edge; `sideEffects: false` on pure utility packages |
| Output | modern `target`; `minify: 'esbuild'`; `sourcemap` off or `hidden` in production |
| TypeScript | `skipLibCheck: true`; `moduleResolution: 'bundler'`; project references above ~200 files per package; no `paths` alias that forces the full graph to re-resolve |
| Dev | esbuild/SWC transform, never Babel; HMR active; cheap source maps |
| CI | type-check, lint and test run as parallel jobs; build after type-check |

### 3.5 Report

```markdown
## Build Optimization Report

| Metric | Before | After |
|---|---|---|
| Clean build / incremental / type check | Xs | Xs |
| Total JS (gzip) / total CSS (gzip) / largest chunk | XXX KB | XXX KB |

### Findings
| # | Issue | Impact | Effort |

### Budgets (set these in CI so a regression fails)
| Total JS gzip | ${gates.initialJsKb} KB |
| Largest chunk | 500 KB |
```

---

## 4. Database mode — `/perf db`

Generic across SQL databases. The pattern-to-fix catalogue, with code, is
`Skill("performance-optimization") § database-performance`; below is the scan order.

### 4.1 Connection pool

Find where the pool is constructed (`${paths.libRoot}/db.*`, `lib/database.*`). Report as a finding
any of these left unset: pool size (sized for serverless vs long-running), idle timeout, connection
timeout, max lifetime. For a serverless Postgres driver, `prepare: false` when the driver does not
support prepared statements — a mismatch fails at runtime, not at startup.

### 4.2 N+1 scan

`Grep` `${paths.backendRoot}` and the service layer for a database call inside a loop: `for`/`while`
with `await db.` in the body, `findOne`/`select` per array item, a missing `IN (…)` batch, a relation
loaded per row inside a tight loop. Report each hit as `file:line` plus the batched alternative.

### 4.3 `select *` scan

Grep tool: pattern `select \*`, path `${paths.backendRoot}`, glob `*.{ts,js,sql}`, `output_mode:
content`, `head_limit: 50`. Not a shell `grep | head` — neither binary exists on Windows, and the
pipe would truncate an error message instead. For each hit, check whether the call site uses every
column; if not, project the columns it needs.

### 4.4 Index gaps

Every foreign-key column needs an index, or a cascade and every join over it is a sequential scan.
The SQL is `Skill("performance-optimization")` **Per-engine introspection** — one row per engine,
not a single-engine query inlined here.

Then: columns that appear repeatedly in `WHERE` clauses in the application code without a supporting
index, and composite order — `WHERE a = ? AND b = ?` needs `(a, b)`, not `(a)` plus `(b)`.

### 4.5 Prepared statements and RLS

Repeated parameterized queries with the same shape are prepare candidates: per-request queries, hot
service functions, scheduler loops. **Postgres-only** for the rest of this subsection: for Postgres
RLS, a policy that calls a helper function needs that function `STABLE` (not `VOLATILE`) or it is
evaluated per row; a `security definer` function must set `search_path`. Details in the skill
catalogue.

### 4.6 `EXPLAIN ANALYZE`

**Postgres-only.** The three hottest queries, from application logs or `pg_stat_statements`:

```sql
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) <query>;
```

Flag sequential scans on large tables, sorts spilling to disk, nested loops over many rows, and an
index that exists but is not used. Other engines: use whatever explain the **Per-engine
introspection** row names, or skip this step and say so.

### 4.7 Report

```markdown
## DB Performance Report

| Pool setting | Current | Recommended | Status |
| N+1 hit | file:line | Batched alternative |
| `select *` hit | file:line | Columns actually used |
| Missing index | table.column | Migration SQL |
| EXPLAIN highlight | query | What the plan shows |
```

Migration SQL is **proposed, never applied** here — a schema change is an irreversible edge.
Apply is `/implement` § 7.5.

---

## 5. Pack modes — `/perf seo`, `/perf sec`

Both are thin on purpose: the pack in `Skill("performance-optimization")` is the procedure, and this
command only routes to it and holds it to the same evidence rule as every other mode.

| Mode | Pack | Depth | Minimum output |
|---|---|---|---|
| `seo` | `seo-geo-baseline` | `skills/performance-optimization/references/seo-playbook.md` (technical: robots, sitemap, metadata, indexability, JSON-LD) · `…/references/seo-content.md` (keywords, on-page, internal linking, local) | indexability + schema + CWV report, with an action list |
| `sec` | `security-baseline` | the project's own security rules under `${rulesDir}/`, when it has them | findings by severity, each with its mitigation |

`sec` reports; it does not patch. A dependency advisory with an exploit path is a finding for the
plan that will fix it, and `graph-powers:security-reviewer` owns application vulnerabilities —
this mode owns the baseline (dependencies, headers, secrets).

---

## 6. Failures

| Symptom | What to do |
|---|---|
| PSI HTTP 429 | retry once, then Lighthouse CLI (`psi-api.md § Failures`) |
| URL unreachable | report it; check the deploy and DNS. Never report an unmeasured URL as passing |
| Build fails in § 3 | resolve and run `${tooling.commands.typeCheck}` first — a compiler error reads like a build-tool problem |
| Database unreachable in § 4 | run the static half only (§ 4.2-4.4 plus the index check against the migration files) and say which half ran |
| Vercel not authed or not linked | stop with the exact command (`vercel login` / `vercel link`). Never guess a project slug |
| The project declares no scanner for `doctor` | say so and stop |
