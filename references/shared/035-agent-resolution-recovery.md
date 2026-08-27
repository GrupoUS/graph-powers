## Section 3.5: Agent Resolution Recovery

This matrix prescribed the bare form until 1.3.1, and every command copied it. That is what produced

    Agent type 'explorer' not found. Available agents: ... graph-powers:explorer ...

— an error naming, in its own list, the string that would have worked.

The opposite message is not the CLI at all:

    Unknown subagent_type 'graph-powers:explorer'. Valid: ... explorer ...

Claude Code's own refusal reads `Agent type 'X' not found. Available agents: ...`. A `Valid:`
phrasing, and a list of **bare** names, means a `PreToolUse` hook matching `Agent` denied the call
before it reached the registry. Such a hook keeps its own allowlist, and an allowlist built by
scanning `.claude/agents/` never contains a plugin's agents — they live in the plugin, are addressed
`<plugin>:<agent>`, and are therefore unknown to it.

Find it and fix it there:

```
claude config get hooks     # or read settings.json: hooks.PreToolUse, matcher "Agent"
```

The hook should not deny a name containing `:`. The runtime registry validates plugin agents itself
and rejects an invalid one with its own clear error, so a second opinion from a stale local list can
only produce false denials. Restarting does **not** help: the hook runs on every call and its
allowlist is rebuilt each time from sources that do not include plugins.

> `graph-powers:explorer` is this plugin's agent (`${CLAUDE_PLUGIN_ROOT}/agents/explorer.md`), NOT
> the CLI's built-in `Explore`.

### When the name does not resolve, that is a route

A plugin cannot guarantee its agents are registered in the session that is running — the same reason
`/plan` treats an unresolved workflow name as a route rather than a defect. Agents had no such rule,
so a spawn that failed to resolve ended the work instead of redirecting it.

| What happened | How it looks |
|---|---|
| The caller used the bare name | `Agent type 'explorer' not found. Available agents: … graph-powers:explorer …` |
| A `PreToolUse` hook denied it before the CLI saw it | `Unknown subagent_type 'graph-powers:explorer'. Valid: … explorer …` |

The first is a defect in the caller: use the namespaced form. The second is not the CLI speaking —
fix the hook, as described above.

**Neither is a reason to stop.** Do the work anyway, by one of these, in order:

1. **`general-purpose`**, with the plugin agent's contract restated at the top of the prompt —
   "You are standing in for `graph-powers:explorer`, which did not resolve. Adopt its contract:
   read-only, report only." The read-only promise then lives in the prompt rather than in
   frontmatter, so say so in the report: it is weaker, and the reader has to know that.
2. **The main thread**, when the work is small enough that a subagent bought only isolation.

Then state in one line which happened and which route you took. **Do not retry the name and do not
report it as a failure** — the finding is produced either way; only the engine differs.

A write-capable agent has no such fallback. `graph-powers:debugger` and
`graph-powers:frontend-specialist` edit files, and standing in for them with a general agent
discards the disjoint-file ownership the wave grouping depends on. When one of those does not
resolve, stop and say so.
