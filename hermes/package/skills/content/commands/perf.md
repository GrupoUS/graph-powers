---
description: "Make something measurably faster, lighter or more findable. Modes: runtime audit, build, db, vercel, doctor, seo and sec; `resources`, `hooks`, and `tests` use the resource audit. Do not use when output is wrong (/debug)."
workflow_type: routing
---

> Hermes: first load `skill_view("graph-powers:graph-engineering")` for native calls and host-policy limits. `content/` paths are `file_path` values relative to the common registered-document parent. Source tools/model frontmatter is not host enforcement.

# /perf

**ARGUMENTS:** the user-provided arguments. First token selects mode; pass URL, scope or strategy after it. Read `.graph-powers/config.json` and load `skill_view("graph-powers:performance-optimization")`; use only its relevant pack and matching project rules.

| Token | Route |
|---|---|
| none / `runtime` / `routes` / `all` | § 2 runtime audit |
| resources / hooks / tests | § 2.0 |
| `fix` | § 2.5 measured fix loop |
| `compare` | § 2.6 saved-run delta |
| `vercel` / `rum` | § 2.7 field-vs-lab cross-check |
| `doctor` / `react` | § 2.8 static health |
| `build` / `bundle` | § 3 build |
| `db` / `database` | § 4 database |
| `seo` | § 5 SEO pack |
| `sec` / `security` | § 5 security pack |

## 2. Runtime audit

Measure before proposing a fix: URL/strategy, baseline, dominant opportunity and source evidence. Report metric, observation, estimated impact, confidence and next action.

### 2.0 Resource audit (`resources`, `hooks`, `tests`)

Use the performance skill's resource pack to identify the actual resource, hook, test, startup, memory or CPU cost, its evidence and the smallest corrective route. A functional defect routes to `/debug`.

### 2.5 Measured fix loop (`fix`)

Only when `fix` spawns a bounded repair batch, load `content/references/shared/070-parallel-agent-spawn.md` and `content/references/shared/010-quality-gates.md`. Capture a comparable baseline, assign distinct scopes, make one measured change per scope, remeasure with the same method, and stop at the target or declared cap. Reuse a green gate only while its files, configuration and relevant environment remain valid.

### 2.6 Compare (`compare baseline after`)

Report per-metric and per-category before/after deltas, regressions first. Missing or incomparable input is `NOT MEASURED`, never improvement.

### 2.7 Vercel/RUM (`vercel`, `rum`)

Use the performance skill's field-data procedure. Compare equivalent routes/periods with lab data; for a recent deploy without sufficient RUM, report it and the retry condition rather than zeroes.

### 2.8 Static health (`doctor`, `react`)

Run the declared render-health command when present and report advisory candidates for render/effect/dependency risk. It is not a shipping gate or a substitute for measured runtime evidence.

## 3. Build

Detect the project build, take cold/warm baselines with the platform-neutral method in the performance skill, inspect declared output/bundle evidence, and report the highest-cost cause. Preserve existing bundler and test configuration; add budgets only when the project has an enforcement path.

## 4. Database

Inspect pool use, N+1, broad selects, indexes, prepared statements/RLS and `EXPLAIN ANALYZE` only against the supplied safe environment. Never apply schema/data changes. Return query/path evidence, measured cost, and the safe next action.

## 5. `seo` and `sec`

Load only the selected performance pack. Report scoped findings with evidence and severity; security/auth defects route to `/debug auth-db` for repair.

## 6. Stop

Do not claim improvement without before/after evidence. Run the smallest applicable gate after a change, then one final relevant gate; do not repeat green gates.
