## Section 7: Parallel Agent Spawn pattern

Before any parallel batch, invoke:

```typescript
Skill("superpowers:dispatching-parallel-agents");
```

This skill enforces: distinct scope per agent, shared return contract, single-message dispatch, stopping conditions. The numbered rules below are the local the project quick-reference.

When invoking 2+ agents in parallel:

1. **Single message** — all `Agent()` calls in the same response (concurrent execution).
2. **Background flag** — `run_in_background: true` for read-only agents (`graph-powers:explorer`, `graph-powers:librarian`, audit dimensions, codex:rescue diagnose).
3. **Foreground only** when the agent must write/edit (`graph-powers:frontend-specialist`, `graph-powers:debugger` in fix mode).
4. **Distinct scope** — each agent prompt has non-overlapping investigation area; otherwise merge into one agent.
5. **Same return contract** — all agents in a parallel batch return findings in the same format (table, columns, severity scale) so consolidation is mechanical.
6. **Width: `graphGuardrails.maxParallelWave` agents in one fan-out** (default 5). Beyond it →
   checkpoint with the user, or split into waves. This is not the same quantity as
   `graphGuardrails.maxSpawnsPerSession` (default 25), which is the session TOTAL and is the one
   `hooks/graph_guardrails.py` refuses at. A run can hit the width limit many times and never
   approach the total, and only the total is enforced in code — the width is a design rule that
   `workflows/ultra-build.js` applies when it slices a wave.

Anti-pattern: spawning agents serially across multiple messages → loses parallelism + multiplies overhead.
