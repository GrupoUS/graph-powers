## Section 3: Agent Assignment Matrix

| Task type | Agent | Background? |
|---|---|---|
| Backend handler/service/auth/DB | `graph-powers:debugger` | No (write-capable) |
| React/components/UI/styling | `graph-powers:frontend-specialist` | No (write-capable) |
| Schema/migrations/indexes | `graph-powers:debugger` | No |
| Tests/QA | `graph-powers:debugger` | No |
| Performance/security/SEO | `graph-powers:performance-optimizer` | No |
| Codebase patterns/files lookup | `graph-powers:explorer` | **YES — mandatory** |
| External docs/packages | `graph-powers:librarian` | **YES — mandatory** |
| Architecture consultation | `graph-powers:evaluator` (Mode 3) | Caller decides |
| Plan synthesis / sprint breakdown | `graph-powers:project-planner` | Caller decides |
| UI or user-flow verification, after the code lands | `graph-powers:verification` | No (drives a browser) |
| Harness wiring verdict, dispatched by `skill-improve` Mode B | `graph-powers:skill-improver` | No (the caller gates the next phase on the verdict) |

Read-only agents (`graph-powers:explorer`, `graph-powers:librarian`) **must** use `run_in_background: true`.

**Explorer vs Librarian:**

| Question | Agent |
|---|---|
| What exists in this codebase? | `graph-powers:explorer` |
| How does this library/API work? | `graph-powers:librarian` |
| Both needed? | Spawn both in same message |

### The name carries the plugin

Every agent above ships inside this plugin, and the registry names it `graph-powers:<agent>`. Drop
that prefix and the name addresses something else, or nothing — and `Explore`, with a capital E, is
the CLI's own built-in, which is not this plugin's agent at all.

If a spawn fails to resolve, load `${CLAUDE_PLUGIN_ROOT}/references/shared/035-agent-resolution-recovery.md`
and follow that route; do not load the failure-path reference during normal assignment.
