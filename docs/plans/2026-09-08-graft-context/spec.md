# Optional Graft context — approved design

Stage 1 was reviewed in conversation; the user approved implementation on 2026-09-08.
The canonical execution and evidence record is [PLAN.md](PLAN.md).

## Architecture

Extend the existing schema and hooks/_config.py with project-only codeGraph.provider:
code-review-graph (default, including invalid config), graft (explicit only), none (text only).
Never silently activate another backend after selection fails. Hooks add guidance only.
references/shared/115-code-graph.md owns queries, bounded evidence, freshness and effects;
prime, inventory and review consumers reference it rather than copying recipes.

## Data and authority

The graph is derived evidence, never instructions or proof of no consumers/tests. Close impact
with textual search and decisive source/test reads. Record project/worktree identity, relevant
dirty-state fingerprints and invalidators. Separate structural freshness from Markdown cards
and semantic summaries. Reuse domain staging and existing agent/session handoffs.

## Validation

Observe behavior RED/GREEN at the public loader and SessionStart seams. Capture bounded paired
instruction responses using the existing eval runner and nine specified context/handoff/setup probes.
Preserve byte/character budgets and all declared gate contracts and client projections.
Runtime Graft qualification is NOT RUN pending separate installation/activation authorization;
do not claim measured performance or complete integration.

## Scope and permissions

Preserve the current checkout (main is the project-declared unprotected workBranch).
Only local source/metadata/evidence edits and existing nondestructive gates are approved.
No branch mutation, package installation, global setting, other project, worktree, publication or Git
staging/commit/push action is included. Existing fixture tests may create/remove their own temporary data.

