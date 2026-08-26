---
name: performance-optimization
description: "Method for runtime, build, database and bundle performance, plus the OWASP security baseline and SEO/GEO. Covers Core Web Vitals, memory and GC, heap snapshots, N+1 and index gaps, sitemaps and structured data. Loaded by /perf. Not for a wrong result, which is a defect."
---

# Performance Optimization

The method and the numbers for four goals: speed, database performance, security baseline, SEO/GEO.

**This file holds what is true regardless of which command asked** — the rules, the targets, the
pattern-to-fix catalogue. It does not hold a procedure. `/perf` is the procedure; a tool's exact
invocation is that tool's reference. When a pack below points somewhere, follow the pointer instead
of reconstructing the steps.

## Core rules

1. Measure before changing code. No baseline, no claim.
2. Change one bottleneck at a time.
3. Re-measure with the **same tool and the same scenario** — a different strategy is a different number.
4. Keep the fix minimal (KISS) and only for an active issue (YAGNI).

## Packs

One pack per run.

| Pack | Use when | Procedure | Minimum output |
|---|---|---|---|
| `performance-core` | slow load, sluggish interaction, high API p95, large bundle | `/perf` § 2 and § 3 · `references/psi-api.md` | before/after metrics + the exact fixes |
| `database-performance` | high API p95, N+1, `select *`, missing index, pool exhaustion, cold start | `/perf` § 4 | before/after query metrics + the exact fixes |
| `security-baseline` | release hardening, OWASP sanity, dependency and header check | `/perf sec` | findings by severity, each with its mitigation |
| `seo-geo-baseline` | search visibility, crawlability, AI citation readiness | `/perf seo` · `references/seo-playbook.md` · `references/seo-content.md` | indexability + schema + CWV report, with an action list |
| `vercel-rum` | real-user CWV per route, traffic shape, post-deploy regression | `references/vercel-data.md § 0` | per-route CWV table + flagged regressions + fixes |
| `memory` | leak, OOM, GC pause, high baseline heap | § Memory below | RSS + heap + GC pause, before and after |

## Targets

**Source of truth is `.graph-powers/config.json::gates`.** Read the configured value before each
run — a project may set it stricter than the web.dev line, and the configured gate is what you pass.
Keep any Lighthouse CI config in the repository in sync with these same keys.

| Metric | Project gate | web.dev "Good" (context only) |
|---|---|---|
| LCP | `gates.lcp` | ≤ 2500 ms |
| INP | `gates.inp` | ≤ 200 ms |
| CLS | `gates.cls` | ≤ 0.1 |
| FCP | not gated (warn) | ≤ 1800 ms |
| TBT | not gated (warn) | ≤ 200 ms |
| Lighthouse Perf / A11y / BP / SEO | `gates.lighthouse.*` | — |
| Initial JS per chunk, gzip | `gates.initialJsKb` | — |
| API p95 | project-defined | — |
| Real-user p75 LCP per route | `gates.lcp` | ≤ 2500 ms |

Field data is graded at the **75th percentile over a 28-day window**; a lab number is one sample of
one machine. They disagree for real reasons — `references/vercel-data.md § 0.4` names the two.

## Bottleneck routing

One table, whatever the surface. Symptom on the left is what the user reports.

| Symptom | Look at | Pack |
|---|---|---|
| Initial load slow | critical rendering path, bundle split, render-blocking third parties | `performance-core` |
| Interaction slow (INP) | re-renders, unstable props and handlers, long event handlers | `performance-core` |
| Layout jumps (CLS) | images without explicit `width`/`height`, ads and embeds, late font swap | `performance-core` |
| API slow (p95) | N+1, missing index, unbounded list query | `database-performance` |
| Cold start slow | pool connection timeout, database region latency | `database-performance` |
| Pool exhausted | `max` too high for the platform, no idle timeout | `database-performance` |
| Memory grows over time | subscriptions, listeners and intervals never cleaned up | `memory` |
| Lab passes, real users do not | device mix and network — act on the RUM | `vercel-rum` |
| Not indexed / not cited | robots, sitemap, canonical, structured data | `seo-geo-baseline` |

## High-value fixes

**Frontend** — route-level lazy loading for heavy pages and modals; remove the unstable prop or
callback causing the re-render cascade; virtualize long lists; explicit image dimensions.

**Backend / DB** — replace N+1 with a join or a batch; index every foreign key; bound every list
query.

Do not over-memoize a cheap operation, and do not widen the change into an unrelated refactor.

## Before you apply a library-specific optimization

Resolve the library's current docs (Context7) rather than working from memory — query patterns,
cache keys and tree-shaking guidance are exactly the surface that changes between minor versions.
Ask for what the fix needs: batch/prepared-statement APIs for the ORM, cache lifetime options for
the data layer, lazy-import guidance for the heavy widget.

---

## `performance-core`

Measurement invocation, parsing, the 429 fallback and the site-wide crawl: `references/psi-api.md`.
Score weights and the fix order: `/perf` § 2.2. Render/effect health comes from the project's own
scanner via `/perf doctor` — this plugin vendors none and does not restate anyone's rule list.

Gates to run around a change, resolved from `tooling.commands`:

```bash
${tooling.commands.typeCheck}
${tooling.commands.lint}
${tooling.commands.build}
```

A bundle-analysis build usually needs a flag for that one run. Inline `VAR=value command` is POSIX
syntax — write the form the shell accepts: `ANALYZE=true <pm> run build` in bash/zsh,
`$env:ANALYZE="true"; <pm> run build` in PowerShell, `set ANALYZE=true && <pm> run build` in cmd.

## `database-performance`

The catalogue. The scan order is `/perf` § 4; what each hit means, and what replaces it, is here.
Schema-state classification (PASS / DRIFT / UNREACHABLE / NOT DECLARED / SKIPPED) lives in
**Schema state** below — `/verify` § 0.3 runs it; this pack never applies.

| Severity | Pattern | Fix |
|---|---|---|
| High | select with no column list (`db.select().from(t)`, `SELECT *`) | project only the columns the call site reads |
| High | a database call inside a `for`/`while` | collect the ids, then one query with `IN (…)` / `inArray()` |
| High | foreign-key column with no index | add it — every cascade and join over it is a sequential scan |
| Medium | list query with no `.limit()` | bound it; cap a list endpoint at 100 |
| Medium | independent queries awaited in sequence | `Promise.all([…])` |
| Medium | same query shape on every request | prepare it |
| Medium | **Postgres-only.** RLS policy calling a `VOLATILE` helper | make the helper `STABLE`, or it runs per row |

**Pool bounds — report any that is unset**, and size them for the platform (serverless burns
connections; a long-running server holds them):

```typescript
const pool = new Pool({
  connectionString,
  max: 10,                         // stay under the provider's ceiling, with headroom for other services
  idleTimeoutMillis: 30_000,       // close idle sockets instead of paying for them
  connectionTimeoutMillis: 10_000, // fail fast on a cold start rather than hanging the request
});
```

A serverless driver generally accepts the same options, but the **Postgres-only**
`statement_timeout` spelling (`options: '-c statement_timeout=30000'`) varies by driver and version —
verify against the runtime before applying it.

**Batching and preparing**, in the shape most ORMs offer:

```typescript
// N+1 → one round trip
const rows = await db.select().from(t).where(inArray(t.id, ids));
const byId = new Map(rows.map(r => [r.id, r]));

// many inserts → one
await db.insert(t).values(items);

// hot path → prepared once, executed per request
const getUserByExternalId = db
  .select({ id: users.id, email: users.email, role: users.role })
  .from(users)
  .where(eq(users.externalId, placeholder('externalId')))
  .limit(1)
  .prepare('get_user_by_external_id');
```

Prepare the queries that run on every request, the frequently-called service functions, and
scheduler loops — not the one-off.

### Per-engine introspection

Read-only. `/perf` § 4.4 points here instead of embedding one engine's SQL. Run against the
engine `${database.engine}` names, or skip the row whose engine the project does not have.

| Engine | Foreign keys without an index | What a document store does instead |
|---|---|---|
| Postgres | `SELECT conrelid::regclass AS table, a.attname AS column FROM pg_constraint c JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = ANY (c.conkey) WHERE c.contype = 'f' AND NOT EXISTS (SELECT 1 FROM pg_index i WHERE i.indrelid = c.conrelid AND a.attnum = ANY (i.indkey));` | — |
| MySQL | `SELECT k.TABLE_NAME, k.COLUMN_NAME FROM information_schema.KEY_COLUMN_USAGE k WHERE k.CONSTRAINT_SCHEMA = DATABASE() AND k.REFERENCED_TABLE_NAME IS NOT NULL AND NOT EXISTS (SELECT 1 FROM information_schema.STATISTICS s WHERE s.TABLE_SCHEMA = k.CONSTRAINT_SCHEMA AND s.TABLE_NAME = k.TABLE_NAME AND s.COLUMN_NAME = k.COLUMN_NAME);` | — |
| SQLite | `PRAGMA foreign_key_list('<table>')` vs `PRAGMA index_list('<table>')` per table the schema declares | — |
| SQL Server | `SELECT t.name AS table_name, c.name AS column_name FROM sys.foreign_key_columns fkc JOIN sys.tables t ON t.object_id = fkc.parent_object_id JOIN sys.columns c ON c.object_id = fkc.parent_object_id AND c.column_id = fkc.parent_column_id WHERE NOT EXISTS (SELECT 1 FROM sys.index_columns ic WHERE ic.object_id = fkc.parent_object_id AND ic.column_id = fkc.parent_column_id);` | — |
| Document store | — | There is no FK-index scan. Check the collection indexes the project declared, and report any query predicate that has no supporting index. |

**Postgres-only** query-plan tooling (`pg_stat_statements`, `EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)`)
stays in `/perf` § 4.6 as a pointer, not as the generic scan.

### Schema state

One classifier, used by `/verify` § 0.3. `/perf` reports; `/implement` owns apply.
Statuses: **PASS**, **DRIFT**, **UNREACHABLE**, **NOT DECLARED**, **SKIPPED**.

`${database.commands.status}` is the command. Exit code alone does not distinguish drift from
unreachable — `prisma migrate status` ≥ 4.3.0 exits 1 for both a connection error and unapplied
files; Alembic and several other tools do the same. Classify by **output class**:

1. Capture stdout, stderr, exit, and whether the process started.
2. Did not start, timed out, or no interpreter → `UNREACHABLE`.
3. Exit 0 → `PASS`.
4. Non-zero **and** combined output is empty or whitespace → `UNREACHABLE` (cannot classify).
5. Non-zero **and** output matches a connection-class token → `UNREACHABLE`.
6. Any other non-zero → `DRIFT`.

Connection-class tokens (generic vocabulary, not an ORM name): `connection refused`,
`could not connect`, `cannot connect`, `can't connect`, `timed out`, `timeout expired`,
`connection timed out`, `connection reset`, `no such host`, `unknown host`,
`name or service not known`, `network is unreachable`, `no route to host`,
`server has gone away`, `authentication failed`, `password authentication failed`,
`access denied for user`, `ECONNREFUSED`, `ETIMEDOUT`, `ENOTFOUND`, `ECONNRESET`, `EAI_AGAIN`.

`${database.commands.generate}` writes the migration artefact in the repo; it does not touch the
database. `${database.commands.apply}` is the irreversible edge. This pack never runs it.
Apply is `/implement` § 7.5, and only when `${database.applyPolicy}` is `optIn` with current-turn
approval.

## `security-baseline`

```bash
${tooling.packageManager} audit
gitleaks detect --source .
python -X utf8 -c "import sys,urllib.request;print(dict(urllib.request.urlopen(sys.argv[1],timeout=15).headers))" ${project.stagingUrl}
```

`gitleaks` is optional and may be absent — say which of the three ran. Headers worth finding missing:
`strict-transport-security`, `content-security-policy`, `x-content-type-options`,
`referrer-policy`, `permissions-policy`.

Cover at least: access control, injection resistance, auth flows, misconfiguration, secrets.
Application vulnerabilities with an exploit path belong to `graph-powers:security-reviewer`; this
pack owns the baseline, and it reports rather than patches.

## `seo-geo-baseline`

Technical side — robots, sitemap, metadata, indexability, JSON-LD, crawl readiness:
`references/seo-playbook.md`. Content side — keywords, on-page, internal linking, local:
`references/seo-content.md`. The PSI SEO and accessibility scores come from the same call as every
other category (`references/psi-api.md`), gated on `gates.lighthouse.seo`.

Check at least: metadata per route, structured data, canonical, robots, sitemap, and CWV — search
ranking reads the field data, not the lab run.

## `vercel-rum`

Real-user CWV from Speed Insights and traffic from Web Analytics, used as the cross-check against
synthetic PSI after a deploy. **The whole procedure is `references/vercel-data.md § 0`**, including
the constraint that shapes it: Vercel exposes no read API, so this pack goes through the dashboard
and its CSV export.

## Memory

Use for a leak, an OOM, GC pause time, or a high baseline heap.

**Baseline first, always**: RSS, V8 heap used, and GC pause p50/p95. No numbers before and after, no
claim of improvement.

| Step | Browser | Node |
|---|---|---|
| Profile | DevTools → Memory | `--inspect` + DevTools, or `--heapsnapshot-signal` |
| Find the leak | heap snapshots at intervals, diffed; detached DOM nodes | snapshots diffed; growing retained sets |
| Confirm the source | listener and subscription cleanup on unmount | interval, stream and emitter cleanup on close |
| Reduce pressure | reuse components, lazy-load, drop duplicate strings | pool or reuse hot buffers; stream large payloads instead of buffering |

Then, only if the profile says so: tune GC flags and heap size, and pool the objects that are
actually allocated in the hot loop.

Anti-patterns, all four observed:

- Tuning GC flags with no baseline — it regresses as often as it helps.
- Reusing a pooled object across request scopes — that is cross-request data leakage, not an optimization.
- Raising the heap limit instead of fixing the leak — it defers the OOM and hides the cause.
- Hunting the leak only in development — real traffic and real session lengths produce different patterns.

---

## Guardrails

- No optimization on intuition. A profile or a measurement, or it does not happen.
- One bottleneck at a time, re-measured the same way.
- No claim of improvement without before/after evidence
  (`${CLAUDE_PLUGIN_ROOT}/references/shared/015-verification-gate.md`).
- No scope expansion into an unrelated refactor.
- A schema change is proposed, never applied from this pack. Apply is `/implement` § 7.5,
  and only when `${database.applyPolicy}` is `optIn` with current-turn approval.

## Report

```markdown
## Optimization Report

Pack: <pack>

| Metric | Before | After | Delta |
|---|---|---|---|

### Changes
1. <change> -> <measured impact>

### Risks / follow-up
- <what is still open, and what would close it>
```

A row that could not be measured says **NOT MEASURED**. "I could not check this" and "this is fine"
are different answers.
