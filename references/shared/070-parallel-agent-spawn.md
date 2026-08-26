## Section 7: Parallel Agent Spawn pattern

This file is the rulebook for any batch of two or more agents — `execution-floor.md § 2` names it. It enforces one-message dispatch, background by default, distinct scope per agent, one return contract per batch, the wave width, one writer per file, and the model coming from the agent.

When invoking 2+ agents in parallel:

1. **Single message** — all `Agent()` calls in the same response (concurrent execution).
2. **Background flag** — `run_in_background: true` for read-only agents (`graph-powers:explorer`, `graph-powers:librarian`, audit dimensions, codex:codex-rescue diagnose).
3. **Foreground only** when the agent must write/edit (`graph-powers:frontend-specialist`, `graph-powers:debugger` in fix mode).
4. **Distinct scope** — each agent prompt has non-overlapping investigation area; otherwise merge into one agent.
5. **Same return contract** — all agents in a parallel batch return findings in the same format (table, columns, severity scale) so consolidation is mechanical.
6. **Width: `graphGuardrails.maxParallelWave` agents in one fan-out** (default 5). Beyond it →
   checkpoint with the user, or split into waves. This is not the same quantity as
   `graphGuardrails.maxSpawnsPerSession` (default 25), which is the session TOTAL and is the one
   `hooks/graph_guardrails.py` refuses at. A run can hit the width limit many times and never
   approach the total, and only the total is enforced in code — the width is a design rule that
   planning Phase C applies when it slices a wave.

7. **One writer per file.** Units running at the same time own **disjoint** paths, declared per task
   (`Owns:`), never inferred at dispatch and never negotiated between two running agents. Overlap
   means the split is wrong: re-split by directory, route or component family, or move the shared
   thing into the plan's contract as its own task. Schema and migrations, cross-cutting singletons
   and global stylesheets are never parallel with anything — their ordering is load-bearing.
   `skills/planning/scripts/sdd.py validate` rejects concurrent ownership collisions before Phase C
   creates the write lease; a plan that needs the re-slice was drawn wrong.

8. **The model comes from the agent, not the caller.** Each agent in `agents/` declares its tier
   (§2), and the `Agent` tool honours it — so a spawn passes no `model`. An override wins silently,
   both directions damaging: `graph-powers:explorer` spawned on `opus` makes the cheap lane
   expensive, and a specialist on the session's model is not the one the work was sized for. Only
   the runtime's own agents (`Explore`, `Plan`, `general-purpose`) take an explicit model, since
   they have no frontmatter. Inside `workflows/*.js` the rule inverts: state the model every time.

**When not to parallelise.** Failures that are related (fixing one may fix the others); a diagnosis that needs the full system state; exploratory debugging, where what is broken is not yet known; shared state, where the agents would edit the same files or use the same resource. Those get one agent, or sequential ones.

**After the batch returns.** Read each summary; check for conflicting edits between agents; run the full gate, not the slice each agent ran; spot-check — agents make systematic errors, and a batch makes the same one in parallel. Consolidation itself is `execution-floor.md § 7`.

Anti-pattern: spawning agents serially across multiple messages → loses parallelism + multiplies overhead.
