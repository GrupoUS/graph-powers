## Section 7: Parallel Agent Spawn pattern

Rules for every batch of two or more agents: one-message dispatch, distinct scopes, bounded width and
total, one return contract, one writer per file and role-owned models.

When invoking 2+ agents in parallel:

1. **Single message** — all `Agent()` calls in the same response (concurrent execution).
2. **Background flag** — `run_in_background: true` for read-only agents (`graph-powers:explorer`, `graph-powers:librarian`, audit dimensions, codex:codex-rescue diagnose).
3. **Foreground only** when the agent must write/edit (`graph-powers:frontend-specialist`, `graph-powers:debugger` in fix mode).
4. **Distinct scope** — each agent prompt has non-overlapping investigation area; otherwise merge into one agent.
5. **Same return contract** — all agents in a parallel batch return findings in the same format (table, columns, severity scale) so consolidation is mechanical.
6. **Two bounds, neither a target.** `maxParallelWave` limits concurrent work;
   `maxSpawnsPerWorkflow` counts all inner config, specialist, retry and review dispatches. Direct
   calls separately use `maxSpawnsPerSession`. Reserve the final Evaluator before each wave. At the
   total, return `NEEDS_WORK`/`BLOCKED` with deferred evidence — no recursion or omitted gate.

7. **One writer per file.** Units running at the same time own **disjoint** paths, declared per task
   (`Owns:`), never inferred at dispatch and never negotiated between two running agents. Overlap
   means the split is wrong: re-split by directory, route or component family, or move the shared
   thing into the plan's contract as its own task. Schema and migrations, cross-cutting singletons
   and global stylesheets are never parallel with anything — their ordering is load-bearing.
   `skills/planning/scripts/sdd.py validate` rejects concurrent ownership collisions before Phase C
   creates the write lease; a plan that needs the re-slice was drawn wrong.

8. **The role owns the model.** Native `Agent` calls pass no override; `workflows/*.js` pass the
   canonical `M(role)` because that runtime does not read frontmatter. Never substitute a generic
   agent when the matrix in §3 has the role.

9. **Cluster by role and boundary.** Package compatible work for one existing specialist; never one
   fixer/refuter per finding. Use one `graph-powers:evaluator` per plan, wave, PR or integrated
   result and at most one material-correction re-review. Security and design roles fire only on
   their surfaces; workflows consolidate configured lenses by role.

**When not to parallelise.** Failures that are related (fixing one may fix the others); a diagnosis that needs the full system state; exploratory debugging, where what is broken is not yet known; shared state, where the agents would edit the same files or use the same resource. Those get one agent, or sequential ones.

**After the batch returns.** Read each summary; check for conflicting edits between agents; run the full gate, not the slice each agent ran; spot-check — agents make systematic errors, and a batch makes the same one in parallel. Consolidation itself is `execution-floor.md § 7`.

Anti-pattern: spawning agents serially across multiple messages → loses parallelism + multiplies overhead.
