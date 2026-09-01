# Pack execution guides

Per-pack deltas over the Step 0-6 chain, plus the Step 2 parallel-research templates.

## Contents

- [The flow, once](#the-flow-once) — identical for `frontend`, `backend` and `auth-db`
- [Per-pack delta](#per-pack-delta) — evidence, sub-agents, focus
- [`systematic-audit` runs differently](#systematic-audit-runs-differently) — inventory before any fix
- [Parallel-research templates](#parallel-research-templates-step-2) — A, B, C, D

---

## The flow, once

Three of the four packs run the same eight moves; only the columns in the next table differ.

1. Pre-flight (Step 0) — pack chosen, gates baselined, `bunx agent-browser --version` when the pack
   needs browser evidence.
2. Build the reproducer (Step 1). **Nothing below starts before this command exists.**
3. Dispatch the pack's sub-agents (Step 2 templates below) while the baseline gates run.
4. Consolidate findings, rank ≥3 falsifiable hypotheses (Step 3), instrument the survivors (Step 4).
5. Minimal fix per `references/methodology.md § Step 5` — RED first through
   `${CLAUDE_PLUGIN_ROOT}/skills/planning/references/execution/tdd-policy.md` (Step 5).
6. Verification gates, exit code read (Step 6).
7. Capture the pack's evidence — browser, database, or both.
8. Report: confirmed hypothesis, root cause, evidence, what was ruled out.

## Per-pack delta

| Pack | Browser evidence | Database evidence | Sub-agents (Step 2) | Focus |
|---|---|---|---|---|
| `frontend-debug` | **required** — screenshot before any fix | — | A + B + C | React/UI regressions, hydration, interaction, visual |
| `backend-debug` | — | **required** | B + C (+ D on any mutation) | procedure and service failures, mutation side effects |
| `auth-db-debug` | — | **required** | B + C + D | authentication, roles, tenant isolation |

**`frontend-debug` rules.** Screenshot before the fix or the "before" no longer exists. Never act on
a `@ref` without a fresh `snapshot` — refs die on any DOM change. Browser mode, target URL and the
`[HARD]` never-`close`-over-CDP rule all live in `Skill("webapp-testing")`; do not restate them here.

Only after Step 1 has produced the runnable reproducer may a concrete React incident run the optional
`${tooling.commands.renderHealth}` probe. Execute that command literally: append no flags, change no
package manager, and do not install or invent a scanner. When it is absent, record `SKIPPED — not
declared` and continue the incident without it.

Treat each finding only as input to Step 3's ranked hypotheses. Confirm or disprove it against the
reproducer and code; a scanner finding is neither root cause nor authorization to auto-fix. Empty or
incomplete output is not a clean bill: zero findings is `CLEAN` only when the scanner explicitly
confirmed it covered the requested scope; otherwise report the coverage gap.

A post-fix re-scan is supplementary evidence. It never replaces real-seam RED/GREEN, declared gates,
or required browser evidence.

**`backend-debug` rules.** Confirm which procedure boundary the call actually crosses — generic
authenticated, admin, or tenant-scoped. Check the input schema against what the client sends.
Guard every `.returning()` destructure. Before citing any "never use transactions here" rule, read
the driver import in the connection module — the doctrine and why it matters are in
`Skill("debugger") § Iron Law`.

**`auth-db-debug` rules.** Walk the whole tenant-resolution chain the context builder uses. Every
`UPDATE` carries the tenant predicate — an ownership check read before the write is a TOCTOU gap.
Verify the auth provider's webhook signing secret matches across environments, and that the
middleware matcher covers the affected route.

Symptom-to-cause lookups for all three: `Skill("debugger") § Common Root Causes` and
`references/anti-patterns.md`.

## `systematic-audit` runs differently

It is a sweep, not an incident, and the difference is that **nothing is fixed while it inventories.**

1. Pre-flight + browser check.
2. Dispatch a bounded batch: A (`graph-powers:verification`) for the browser baseline when a UI
   exists; one `graph-powers:explorer` package combining B-D (structure, known patterns and data
   integrity); and `graph-powers:security-reviewer` only when a sensitive surface exists. Never one
   agent per audit dimension.
3. **Inventory only.** Classify every finding P0-P3. No edits in this phase.
4. Present the findings table and let the user prioritize.
5. Fix P0 one at a time, verifying after each; then P1, then P2.
6. Full gates: `${tooling.commands.typeCheck}`, `${tooling.commands.lint}`, `${tooling.commands.test}`,
   `${tooling.commands.build}` — one per line, each exit code read before the next.
7. Browser evidence of the critical flows after the fixes.
8. Report, with the remaining P3 items logged rather than silently dropped.

Cross-reference `${rulesDir}/stability.md` and `references/methodology.md § Security checklist`.

---

## Parallel-research templates (Step 2)

Dispatched **after** Step 1 produced a runnable reproducer. Read
`${CLAUDE_PLUGIN_ROOT}/references/shared/070-parallel-agent-spawn.md` first — it enforces distinct
scope, a shared return contract and single-message dispatch.

**Shared contract for every template below.** `run_in_background: true`. Read-only **by frontmatter,
never by instruction**: B, C and D are consolidated into one package for
`subagent_type: "graph-powers:explorer"`
(`disallowedTools: Write, Edit`), and A uses `subagent_type: "graph-powers:verification"`, the browser
specialist, which carries `Skill` so it can load `webapp-testing`. These roles were
`graph-powers:debugger` once — told in prose to fix nothing while holding `Write` and `Edit`, which is
the incident recorded in `references/anti-patterns.md`. Return under 2000 tokens, findings as
`| # | Finding | Confidence (1-5) | Source | Impact |`, and pass the symptom, the failing
URL or procedure, and the affected files in the prompt.

### A — Evidence Collector (`frontend-debug`, `systematic-audit`)
```
Public page  → headless: open "[URL]" → snapshot -i -c → screenshot → eval overlay → get title/url → close
Authenticated → --cdp attach, same sequence, plus console + errors, and NO close
RETURN: mode used · screenshot path · framework error-overlay text if present · page URL + title. Fix nothing.
```

### B — Code Archaeologist (all packs)
```
1. Find the failing component / route / procedure; pin the EXACT file:line where the error originates.
2. git log --oneline -10 -- <affected-files>.
3. Map the chain: handlers → data-layer queries → auth middleware → input validators.
4. Flag the recent changes that could have caused the regression.
5. `systematic-audit` only — structural sweep per references/structural-quality.md: files over 1000 lines,
   ad-hoc branching hotspots, near-duplicate helpers against their Canonical Home. Inventory only.
RETURN: findings table · affected file:line ranges · last 3 commits touching them · dependency chain · gaps.
```

### C — Regression Hunter (all packs)
```
1. Scan references/anti-patterns.md and the Common Root Causes table in SKILL.md.
2. Search the project auto-memory for matching patterns.
3. Check ${rulesDir}/stability.md for rules that bear on the symptom.
MATCH    → pattern name, root cause, recommended fix, file guidance.
NO MATCH → top-3 hypotheses ranked by probability, each with evidence for and against plus a probe.
RETURN: MATCHED / NO_MATCH, then whichever branch applies.
```

### D — DB State Inspector (`backend-debug`, `auth-db-debug`)
```
1. Read the schema under ${paths.schemaRoot} to learn the real table structure.
2. Construct targeted SELECT queries that verify the suspected data state.
3. Check orphaned rows, missing foreign-key references, tenant-key gaps, enum drift, and an index on every FK.
IMPORTANT: do NOT execute them. Return the queries; the lead agent runs them after review.
RETURN: table structure summary · diagnostic queries, ready to run · suspected inconsistencies.
```
