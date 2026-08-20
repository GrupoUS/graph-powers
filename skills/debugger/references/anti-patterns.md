# Anti-Patterns + Negative Constraints

> Project-specific bug patterns + consolidated "NEVER do" lookup. Loaded by `/debug` command and `debugger` skill.
> Append on discovery — do NOT delete entries.
> The catalogue below is generic. Each project adds its own entries under `${rulesDir}/` — an anti-pattern list that never names anything the project it is installed in actually did is decoration.

---

## Negative Constraints (NEVER do)

Each constraint points to canonical source — this section is a lookup aid.

### Design / UI

- **NEVER** use hardcoded hex colors → the project's own rules in `${rulesDir}/`, `${rulesDir}/design.md`
- **NEVER** introduce a colour outside the project's declared tokens → `${rulesDir}/design.md`
- **NEVER** center all text by default → root `DESIGN.md` §11/§15
- **NEVER** use emoji as design elements → root `DESIGN.md` §15
- **NEVER** exceed `--text-xl` for body text → root `DESIGN.md` §5
- **NEVER** place custom product composites in the design-system primitives folder (`${paths.componentsRoot}/ui/`) → `${paths.frontendRoot}/AGENTS.md`

### Code Quality

- **NEVER** invoke the type-checker binary directly (`tsc --noEmit` and friends) — use the project's declared gate, `${tooling.commands.typeCheck}` → the project's own rules in `${rulesDir}/`
- **NEVER** use a package manager other than the one the project declares (`${tooling.packageManager}`) — a second lockfile is a second dependency graph → the project's own rules in `${rulesDir}/`
- **NEVER** add a scripting language the repository does not already use — a new runtime in `scripts/` is a dependency nobody agreed to
- **NEVER** commit without running `${tooling.commands.format}` on edited files → `${CLAUDE_PLUGIN_ROOT}/references/safety-floor.md § 1`
- **NEVER** use `localStorage` / `sessionStorage` → `${paths.frontendRoot}/AGENTS.md`
- **NEVER** mark a task done without verification evidence → root `AGENTS.md § Cardinal Rule 2`
- **NEVER** use `console.log` / `debugger` in production code → `${rulesDir}/stability.md § H`
- **NEVER** use `as any` — narrow types or use `unknown` → `${rulesDir}/backend.md`
- **NEVER** use non-null assertion `!` on optional data → `${rulesDir}/stability.md § B`
- **NEVER** use `href="#"` for actions — use `<button>` → `${rulesDir}/stability.md § K`

### Architecture

- **NEVER** create new files when enhancing existing ones suffices → extension beats addition, every time
- **NEVER** add a dependency without checking monorepo first → the project's own rules in `${rulesDir}/`
- **NEVER** bypass the WISC tier loading protocol → root `AGENTS.md § WISC`
- **NEVER** write raw SQL outside Drizzle for schema ops → `${rulesDir}/database.md`
- **NEVER** add an FK column without a matching index → `${rulesDir}/database.md`
- **NEVER** invoke a database MCP server the project has disabled — use the vendor CLI its rules name → the project's own rules in `${rulesDir}/`
- **NEVER** use `SELECT *` in ORM queries — specify columns → `${paths.backendRoot}/routers/AGENTS.md`
- **NEVER** hand-roll auth/admin checks when a narrower procedure already exists (the admin or tenant-scoped procedure) → `${paths.backendRoot}/routers/AGENTS.md`

### Agents & Workflows

- **NEVER** spawn >5 sub-agents per user request without a checkpoint → `${CLAUDE_PLUGIN_ROOT}/references/recovery-protocol.md`
- **NEVER** attempt >3 fixes on the same hypothesis — escalate to evaluator → `${CLAUDE_PLUGIN_ROOT}/references/recovery-protocol.md`
- **NEVER** stack multi-agent patterns without justification → `${CLAUDE_PLUGIN_ROOT}/references/recovery-protocol.md`
- **NEVER** hand a review task to a write-capable subagent. Observed failure: a review agent with Bash and write tools "partitioned ownership" of a diff, classified in-flight uncommitted work as unrelated, and reverted it to HEAD — roughly 80 lines of the file under review, destroyed by the reviewer. Reviews go to read-only agents (`evaluator`, `security-reviewer`) or read-only slash commands
- **NEVER** commit CRLF line endings → the project's own rules in `${rulesDir}/`
- **NEVER** skip hooks with `--no-verify` / `--no-gpg-sign` unless user explicitly asks → `${CLAUDE_PLUGIN_ROOT}/references/safety-floor.md § 1`
- **NEVER** use destructive git operations (`reset --hard`, `push --force`, branch deletion) without confirmation → root `AGENTS.md § Executing actions with care`

---

## Database / ORM (Drizzle + Postgres)

1. **Drizzle `.returning()` empty-array trap.** Empty `[]` is truthy. ALWAYS destructure first then null-check: `const [row] = await db...returning(); if (!row) throw ...`.
2. **Drizzle `onConflictDoNothing` misses partial unique indexes.** When a unique index has a `WHERE` clause, must add `targetWhere` to `onConflictDoNothing` — else conflict not detected.
3. **Schema drift → tRPC 500.** Drizzle `db.select().from(table)` enumerates ALL schema columns. Missing DB columns → Postgres error → tRPC 500. Recover with a script that runs the migration through the pool driver (`drizzle-kit push --force` blocks on a TTY).
4. **Stale prepared-statement cache.** After a schema migration the running container may still hold the old plan. Restart it if the 500 persists post-migration.
5. **The runtime's bare test subcommand instead of the project's test script.** Bun's native runner, for one, does not implement vitest's `vi.mocked`/`vi.hoisted`. Always go through `${tooling.commands.test}`.

## Backend (tRPC + Hono)

6. **Hand-rolled admin checks inside the generic authenticated procedure.** Use the narrower admin procedure — never re-implement role checks manually.
7. **Per-request provider client construction.** Always reuse the shared singletons the backend core module (`${paths.backendRoot}/_core/`) already exports — AI client, orchestrator, `db`, logger factory.
8. **Localized error messages as contract.** Frontend must branch on `error.data.appCode`, never on substrings. Surface code via `cause: { code }` so tRPC error formatter exposes `appCode`.
9. **Date.now() race in tests.** Use `vi.useFakeTimers()` for timing-sensitive boundary tests.
10. **`Number.isFinite` over `typeof === 'number'` for stored numerics.** DB may return strings/Decimal; explicit numeric guards prevent drift.
11. **Tenant defense-in-depth on child fetches.** Even when parent rows already filtered by `tenantId` and child FK references parent, fetching the child via `inArray(child.id, parentIds)` WITHOUT a tenant filter leaks cross-tenant data on corrupted rows. PostgreSQL FK constraints check the referenced PK exists, NOT that ownership chains agree. Always add `eq(child.tenantId, input.tenantId)` to the child WHERE. Observed shape: a list procedure joined a child table through a join-table's id column only, and one corrupted join row was enough to return another tenant's records.
12. **4-layer persistence bug pattern (stateful UI).** When "saved visual state lost on reload" symptom appears, audit ALL FOUR layers before claiming a root cause — fixing only one leaves the bug:
    - Schema column missing → can't persist
    - Mutation payload omits the field → schema column always NULL
    - Component state is `useState` internal-only → no payload to send
    - Render path ignores the prop → re-load shows default even when DB has the data
    The fix REQUIRES all four to align. Each layer's "evidence" is independent: schema row in DB, network tab payload, React DevTools state, computed styles in inspector.

## Frontend (React 19 + Vite)

13. **Inline object/array prop = new ref every render.** Wrap in `useMemo`, hoist to module scope, or use stable selector. Especially in `useRouterState` selectors that `.map()` — defeats `useMemo` structural sharing.
14. **`staleTime !== refetchInterval`.** Causes double-fetch storms. Set them equal.
15. **`gcTime < staleTime`.** Causes re-fetch on remount. Always `gcTime ≥ staleTime`.
16. **`href="#"` for actions.** Use `<button>`. Real `<a href="…">` only for navigation.
17. **Animating `width`/`height`/`top`/`left`.** Layout-thrashing. Use `transform` + `opacity` only. Accordions: `grid-template-rows: 0fr ↔ 1fr`.
18. **DialogFooter without `flex-shrink-0`.** Disappears in scrollable flex-column dialogs.
19. **Inline arrow on memoized child = breaks memo.** `onDelete={(id) => setX(id)}` is a fresh fn every parent render; child `memo()` wrapper compares it by reference and re-renders. Pass `setX` directly when its signature matches (`useState` setters are stable), or wrap in `useCallback`. Especially hot when parent state changes at 60 fps (e.g. slider drag).
20. **Multi-touch gesture without `pointerId` discrimination.** A `PointerEvent` handler that tracks a single `panStateRef.active` flag can be hijacked by a second simultaneous touch / mouse, which overwrites the gesture origin mid-drag and terminates it prematurely on the second pointer's release. Store the gesture's `pointerId` in the ref and reject events whose `e.pointerId` doesn't match.
21. **Compare-style "uncontrolled" props that read initial value via `useState(prop)` only.** `useState(initialFoo)` reads `initialFoo` once on mount; later changes to the prop don't update internal state. If the prop is allowed to act as a "reset to" signal (e.g. data refetch updates it), add `useEffect(() => setFoo(initialFoo), [initialFoo])` guarded by `!isControlled` — otherwise stale state persists indefinitely across data refreshes.

## Integrations (messaging sockets, ad platforms, webhooks)

17. **A connect-time presence flag can kill inbound routing.** Several long-lived messaging socket clients stop delivering inbound events when the socket is opened with `markOnlineOnConnect: true`. Open it offline and send explicit presence updates instead.
18. **Webhook without idempotency.** Always `INSERT … ON CONFLICT … DO NOTHING RETURNING id`. If id null → already processed.
19. **Tight reconnect loops after a socket disconnect.** Use an explicit state machine + exponential backoff. Different disconnect reasons need different recovery.
20. **OAuth token expiry not pre-checked.** Check before using stored credentials, refresh proactively.
21. **Webhook acks slow.** Always 200 first, process async.
22. **`await` on external API inside webhook handler.** Even when service has a 10s timeout, awaiting Meta CAPI / Resend / Slack from `handleCheckoutCompleted` (or any `handle<Provider>Event`) gates the provider's ack on the third-party latency. Provider redelivers → handler runs again → cascade. Pattern: extract the dispatch into `async function dispatchX(...)`, call it as `void dispatchX(...)` after the DB writes. The dispatch function must have a never-throws contract (returns `{ ok, status, reason }`) so the `void` is safe without a wrapping try/catch. Counter-case: if the dispatch result writes back to the DB (e.g. a `capi_status` column on the lead row), then it IS part of the request — await it inside a `try/catch` with explicit error logging.
23. **Pixel/CAPI deduplication needs `eventID` as the 4th `fbq` arg, NOT inside the `data` payload.** Meta's contract is `fbq('track', eventName, data, { eventID })`. If you pass `eventID` as a key in `data`, the Pixel still fires but Meta does NOT deduplicate it against the matching server-side Conversions API event with the same id — you get double-counted conversions. Server-side CAPI must reuse the same `event_id` value (string, typically UUID generated server-side and returned to the client on the mutation that triggers the Pixel event).

## Build / Performance

22. **Static imports of shared data inside lazy-split modules defeat Rollup splitting.** Extract data into pure module imported separately.
23. **GHA secrets in job-level `if:` forbidden.** Causes "workflow file issue" 0s failures. Use `continue-on-error: true` or `vars.*`.
24. **Vite build OOM on GHA.** Set `NODE_OPTIONS: --max-old-space-size=4096` in build env.
25. **Concurrent backend deploys can OOM a small VPS.** Serialize them with a CI job-concurrency group so a second deploy queues instead of building alongside the first.

## CI / DX

26. **CRLF in commits blocks CI.** Enforce LF via `.gitattributes`. Recover: `${tooling.commands.format} && git add --renormalize .`.
27. **Direct push to a protected branch.** All work via `${git.workBranch}` → PR → protected branch. Even `[skip ci]` direct pushes break the policy.
28. **Untrusted ADR claim.** When memory cites a "removed file" or "deprecated flag", ALWAYS verify with grep before recommending action — memory may be stale.
