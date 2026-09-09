## Section 7: Parallel Agent Spawn pattern

Rules for every batch of two or more agents: one-message dispatch, distinct scopes, bounded width and
total, one return contract, one writer per file and role-owned models.

When invoking 2+ agents in parallel:

1. **Single message** — all `Agent()` calls in the same response (concurrent execution).
2. **Background flag** — `run_in_background: true` for read-only agents (`graph-powers:explorer`, `graph-powers:librarian`, audit dimensions, codex:codex-rescue diagnose).
3. **Foreground only** when the agent must write/edit (`graph-powers:frontend-specialist`, `graph-powers:debugger` in fix mode).
4. **Distinct scope** — each agent prompt has non-overlapping investigation area; otherwise merge into one agent.
5. **Same return contract** — all agents in a parallel batch return findings in the same format (table, columns, severity scale) so consolidation is mechanical.
6. **Bounds are ceilings.** `maxParallelWave` limits concurrency; `maxSpawnsPerWorkflow` counts all
   inner config, specialist, retry and review dispatches. Reserve the final Evaluator before each
   wave. At the total, return `NEEDS_WORK`/`BLOCKED` with completed/deferred evidence.
   Direct `maxSpawnsPerSession` and `maxRoundsPerAgent` count only the rolling `spawnWindowMinutes`
   window in the native session; they are not persistent cross-session counters. Phase C retains
   dispatch/consultation reservations and correction history in its existing plan ledgers across
   resume, compaction and model/context changes. Never clear those budgets to retry. Unresolved
   loops use `/debug recover` with selected facts and rejected attempts, preserving their reasons.

7. **One writer per file.** Concurrent units declare **disjoint** `Owns:` paths before dispatch.
   Re-split overlap by boundary or make shared work a sequential task; never negotiate ownership
   while running. Schema/migrations, cross-cutting singletons and global stylesheets run serially.
   `skills/planning/scripts/sdd.py validate` rejects concurrent collisions before the Phase C lease.

8. **The role owns the model.** Native `Agent` calls pass no override; `workflows/*.js` pass the
   canonical `M(role)` because that runtime does not read frontmatter. Never substitute a generic
   agent when the matrix in §3 has the role.

9. **Cluster by role and boundary.** Package compatible work for one existing specialist; never one
   fixer/refuter per finding. Use one `graph-powers:evaluator` per plan, wave, PR or integrated
   result and at most one material-correction re-review. Security and design roles fire only on
   their surfaces; workflows consolidate configured lenses by role.

**When not to parallelise.** Related failures, unresolved system-wide diagnosis or shared files/state
get one agent or sequential work.

**After the batch returns.** Check summaries, conflicting edits and integration evidence under
`execution-floor.md § 7`; reuse only valid checks and spot-check claims.

Anti-pattern: spawning agents serially across multiple messages → loses parallelism + multiplies overhead.
