> Hermes auxiliary: `content/` paths are `file_path` values relative to the registered-document parent. Apply the loaded graph-engineering mapping and host policy; this file is served without template expansion.

## Section 3: Agent Assignment Matrix

| Task type | Agent | Background? |
|---|---|---|
| Backend handler/service/auth/DB | `graph-powers:debugger` | Optional (write-capable) |
| React/components/UI/styling | `graph-powers:frontend-specialist` | Optional (write-capable) |
| Schema/migrations/indexes | `graph-powers:debugger` | No |
| Tests/QA | `graph-powers:debugger` | No |
| Performance/SEO implementation | `graph-powers:performance-optimizer` | No |
| Security/tenancy/secrets adversarial review | `graph-powers:security-reviewer` | Yes |
| Visual direction and UX review | `graph-powers:ui-ux-designer` | Yes |
| Codebase patterns/files lookup | `graph-powers:explorer` | **YES — mandatory** |
| External docs/packages | `graph-powers:librarian` | **YES — mandatory** |
| Architecture consultation | `graph-powers:evaluator` (Mode 3) | Caller decides |
| Plan synthesis / sprint breakdown | `graph-powers:project-planner` | Caller decides |
| UI or user-flow verification, after the code lands | `graph-powers:verification` | No (drives a browser) |
| Harness wiring verdict, dispatched by `skill-improve` Mode B | `graph-powers:skill-improver` | No (the caller gates the next phase on the verdict) |

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

If a spawn fails to resolve, load `content/references/shared/035-agent-resolution-recovery.md`
and follow that route; do not load the failure-path reference during normal assignment.

### The role also carries the model

Use the matrix role, never a generic/dynamic name. Harder judgment changes the role.

- Claude Agent: canonical `agents/<role>.md` alias, no override; a host gateway may route it elsewhere.
- Claude Workflow: load `agents/*.md`; pass its model on each call; stop if missing.
- Codex: derive eligible role/model/effort from `content/codex/model-policy.json`, preserving overrides.

For enabled Jev coordination use execution-floor §4a. Same-model roles remain distinct actions.
