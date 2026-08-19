# Evaluator Mode Rubrics

Load only the selected mode section.

## Mode 1 — Plan Review

Score product intent, functional completeness, visual/UX requirements, and code
feasibility. Identify ambiguity landmines, at least the material edge cases,
testable rewrites, AI meaningfulness, sprint dependencies, migrations, rollback,
and browser/test contracts. Return APPROVED or REVISION_REQUIRED.

## Mode 2 — Sprint QA

Map every sprint criterion to evidence: implementation path, focused test, gate,
or browser probe. Mark MET/UNMET, report reproducible bugs with file:line, and
return SPRINT_APPROVED only when all blocking criteria pass.

## Mode 3 — Architecture Analysis

Restate the decision and constraints, identify root forces, present at least two
viable options with operational/security/performance/maintenance trade-offs,
recommend one, state second-order effects and rollback, and calibrate confidence.

## Mode 4 — Code Review

Inspect the branch/diff and relevant context for bugs, regressions, tenant/auth
violations, irreversible data risks, OWASP exposure, performance regressions,
missing tests, and maintainability defects. Prioritize P0–P3 and cite tight
file:line ranges. Return REVIEW_APPROVED or CHANGES_REQUESTED.

Across modes, filter findings that lack a violated contract or plausible impact.
