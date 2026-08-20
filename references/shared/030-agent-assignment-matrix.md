## Section 3: Agent Assignment Matrix

| Task type | Agent | Background? |
|---|---|---|
| Backend handler/service/auth/DB | `debugger` | No (write-capable) |
| React/components/UI/styling | `frontend-specialist` | No (write-capable) |
| Schema/migrations/indexes | `debugger` | No |
| Tests/QA | `debugger` | No |
| Performance/security/SEO | `performance-optimizer` | No |
| Codebase patterns/files lookup | `explorer` | **YES — mandatory** |
| External docs/packages | `librarian` | **YES — mandatory** |
| Architecture consultation | `evaluator` (Mode 3) | Caller decides |

Read-only agents (`explorer`, `librarian`) **must** use `run_in_background: true`.

**Explorer vs Librarian:**

| Question | Agent |
|---|---|
| What exists in this codebase? | `explorer` |
| How does this library/API work? | `librarian` |
| Both needed? | Spawn both in same message |

> `explorer` = custom agent (`${CLAUDE_PLUGIN_ROOT}/agents/explorer.md`), NOT the built-in `Explore`. Use `subagent_type: "explorer"`.
