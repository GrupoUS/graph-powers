---
name: performance-optimization
description: "Method for runtime, build, database and bundle performance, plus the OWASP security baseline and SEO/GEO. Covers Core Web Vitals, memory and GC, heap snapshots, N+1 and index gaps, sitemaps and structured data. Loaded by /perf. Not for a wrong result, which is a defect."
---

> Hermes: first load `skill_view("graph-powers:graph-engineering")` for native calls and host-policy limits. `content/` paths are `file_path` values relative to the common registered-document parent. Source tools/model frontmatter is not host enforcement.

# Performance Optimization

Measure the limiting path, change one bottleneck, and compare the same tool, scenario and metric.
A wrong result belongs to `/debug`; an unmeasured rewrite is not an optimization. `/perf` owns
dispatch; the selected pack below supplies its measurement and interpretation method.

## Packs

| Pack / route | Method |
|---|---|
| `performance-core` / runtime, routes, all | PSI method below; build/bundle uses Build |
| `resources` / hooks, tests | Resource audit |
| `database-performance` / db, database | query/pool evidence below; never apply schema changes |
| `security-baseline` / sec, security | scoped report-only baseline below |
| `seo-geo-baseline` / seo | `content/skills/performance-optimization/references/seo-playbook.md`, `content/skills/performance-optimization/references/seo-content.md` |
| `vercel-rum` / vercel, rum | `content/skills/performance-optimization/references/vercel-data.md` § 0, including insufficient-data handling |
| `memory` | retained heap/RSS/GC procedure below |

## Targets

`.graph-powers/config.json::gates` is the project authority; absent gates are not passes. Track
`gates.lcp`, `gates.inp`, `gates.cls`, `gates.lighthouse.*`, `gates.initialJsKb` and a declared API p95.
Reference values, not substituted project gates: LCP ≤2500ms, INP ≤200ms, CLS ≤0.1; FCP ≤1800ms
and TBT ≤200ms are advisory. Field CWV uses p75 over 28 days; a lab sample is not field evidence.

## `performance-core`

Read `content/skills/performance-optimization/references/psi-api.md`: PSI API → Lighthouse CLI for 429/auth/custom throttle → Unlighthouse
for route-wide collection. Measure mobile and desktop unless scoped otherwise; a gating lab result
uses the median of three comparable samples. Prioritize measured savings: Lighthouse v10+ weights
TBT 30%, LCP 25%, CLS 25%, FCP 10%, Speed Index 10%. Missing CrUX is missing data, never PASS.

Trace load cost to critical rendering/bundles/third parties, INP to long handlers/re-render cascades,
and CLS to dimensions/embeds/font changes. Reuse route splitting, bounded/virtualized lists and
explicit asset dimensions; verify library-specific cache/batch/tree-shaking behavior before changing it.

## Resource audit

On the same machine, measure elapsed time, process count, CPU and peak memory for hook startup,
Stop/PostToolUse invocations, verification fan-out and test workers. Read the declared runner and
JS/TS policy in `content/references/shared/130-typescript7-oxc-gates.md` when relevant.
Stop and PostToolUse each launch at most one changed-file process: no package fetch, full-tree
fallback or persistent result cache. Type-aware Oxlint stays at the final boundary with
`oxlint --type-aware --type-check --threads 1`; editor/edit hooks use regular Oxlint.
Preserve security, trust, approval, protected-file and branch checks while reducing repeated work.
Report the dominant cost and repeat the same measurement after one scoped change.

## Build

Confirm `tooling.buildTool`, on-disk config and the exact declared build command. Use portable
`time.perf_counter()` around `subprocess.run()` of that command's argv and capture elapsed time plus
exit code. Record cache state: a first run is not automatically cold. Measure a known cold build
only in an authorized disposable environment or after approved cache cleanup; then repeat warm.
If a cold baseline is unavailable, label it `NOT MEASURED` rather than deleting unknown directories.

Record cold/warm/type-check time, slow log phases, total gzip JS/CSS and largest chunks. Enumerate
the 20 largest files in the actual output directory with Python `pathlib`/`stat`; use only an
existing project analyzer to trace duplicated modules, heavy dependencies and splitting opportunities.
Check build/package/type caches, lazy imports, pure-module tree shaking, asset sizing/compression
and source-map policy against this bundler's actual configuration. Preserve bundler/test settings
unless measured evidence requires a change; budgets need a declared enforcement path.

## `database-performance`

Measure pool limits/timeouts, connection/region cost, query count and p95 before fixes. Trace N+1
to a batch/join, broad selects to consumed columns, unbounded lists to a declared cap, sequential
independent queries to safe concurrency, and repeated hot query shapes to supported preparation.
Check FK/predicate indexes with the configured engine's catalog and an actual query plan; document
stores use collection indexes instead of SQL FK scans. Prepared statements and `statement_timeout`
are driver-specific; inspect support first. In Postgres, inspect per-row volatile RLS helpers;
never alter tenancy/authorization to improve a metric. `EXPLAIN ANALYZE` executes the query: run
only against the supplied safe environment. Schema/index changes are proposals, never applied here.

### Schema state

Run only `${database.commands.status}` and classify output, not just exit code: absent command is
`NOT DECLARED`; intentionally omitted is `SKIPPED`; no start/timeout or empty nonzero output is
`UNREACHABLE`; exit 0 is `PASS`; nonzero connection/DNS/network/authentication errors are
`UNREACHABLE`; other nonzero output is `DRIFT`. Capture stdout/stderr/exit and the deciding message.
`${database.commands.generate}` writes an artifact; `${database.commands.apply}` is an irreversible
operation requiring its explicit scope approval and declared opt-in, outside this pack.

## `security-baseline`

Report access control, injection, auth, misconfiguration and secret risks. Use the declared package
manager's audit, an already-installed secret scanner with redacted output, and headers from the
supplied target; report unavailable tools. Check HSTS, CSP, nosniff, referrer and permissions policy.
Keep evidence masked; application exploit paths route to `graph-powers:security-reviewer`, and
auth/security repairs to `/debug auth-db`. This pack reports rather than patches security controls.

## `seo-geo-baseline`

Read only the selected search references from Packs. Check route metadata, canonical, robots,
sitemap, structured data, crawl/indexability and CWV; distinguish a deliberate noindex campaign
from an indexable evergreen route. Keep technical and content findings tied to measured evidence.

## `vercel-rum`

Follow `content/skills/performance-optimization/references/vercel-data.md` § 0 for dashboard/CSV acquisition and lab-vs-field disagreements;
compare equivalent routes/periods and sample coverage. A recent deploy without sufficient samples
reports the retry condition, never zero-valued success.

## Memory

Record RSS, heap used and GC pause p50/p95; repeat the same workload/session length. Diff browser
or runtime heap snapshots for growing retained sets/detached DOM, then trace subscription, listener,
interval, stream and emitter cleanup. Optimize hot allocations only when the profile identifies
them. Never pool objects across request/tenant scopes or raise heap limits to conceal a leak.

## Guardrails

Use declared tooling and the smallest relevant gate after a change. Reuse green evidence only while
its files/configuration/environment remain valid; no repeated green rounds outside an explicitly
selected profile. Never expand scope or weaken security/configuration for a score.

## Report

Return pack, metric, before, after, delta, exact changed paths, evidence and remaining risk. Missing
or incomparable measurements are `NOT MEASURED`; stop at a proven target or the declared attempt cap.
