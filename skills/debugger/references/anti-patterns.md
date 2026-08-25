# Anti-patterns — the bug catalogue

> Loaded by `/debug` Step 0 as first-line triage, and by `graph-powers:debugger`.
> **Append on discovery — never delete an entry.** A catalogue that only holds what is still
> current is a catalogue nobody learned from.

## Contents

- [Where the NEVER rules live](#where-the-never-rules-live) — this file is not their home
- [Database / ORM](#database--orm) — 1-5
- [Backend / API layer](#backend--api-layer) — 6-13
- [Frontend](#frontend) — 14-22
- [Integrations](#integrations) — 23-29
- [Build, CI and delivery](#build-ci-and-delivery) — 30-37

The catalogue is generic. A project adds its own entries under `${rulesDir}/` — a list that never
names anything the project it is installed in actually did is decoration.

---

## Where the NEVER rules live

They are not restated here. One index, one canonical source per rule:

| Class of rule | Canonical source |
|---|---|
| Git, secrets, irreversible operations, tooling substitution, scope, completion claims | `${CLAUDE_PLUGIN_ROOT}/references/safety-floor.md` §1-§7 |
| What a hook actually denies, and how to release it | `${CLAUDE_PLUGIN_ROOT}/references/shared/110-guardrails-index.md` |
| Fan-out width, spawn ceilings, escalation after failed attempts | `${CLAUDE_PLUGIN_ROOT}/references/recovery-protocol.md` · `shared/070-parallel-agent-spawn.md` |
| Design tokens, stability, execution and UX floors | `${rulesDir}/` — the project's own rules |

One entry is kept here rather than indexed, because it is an incident and not a policy:

**Never hand a review task to a write-capable subagent.** Observed: a review agent holding `Bash`
plus write tools "partitioned ownership" of a diff, classified in-flight uncommitted work as
unrelated, and reverted it to HEAD — roughly 80 lines of the file under review, destroyed by its
reviewer. Reviews go to read-only agents (`graph-powers:evaluator`, `graph-powers:security-reviewer`)
or to read-only commands.

---

## Database / ORM

1. **`.returning()` empty-array trap.** An empty `[]` is truthy. Destructure first, then null-check:
   `const [row] = await db…returning(); if (!row) throw …`.
2. **`onConflictDoNothing` misses partial unique indexes.** When the unique index carries a `WHERE`
   clause, the conflict target needs the same predicate (`targetWhere`) or the conflict is never
   detected.
3. **Schema drift → 500 on a procedure that used to work.** A `select().from(table)` enumerates
   every column the schema declares; a column missing in the database is a driver error surfaced as
   a 500. Recover by running the migration through the pool driver — the push subcommand blocks on a
   TTY.
4. **Stale prepared-statement cache.** After a migration the running container may still hold the
   old plan. Restart it if the 500 survives a correct migration.
5. **The runtime's bare test subcommand instead of the project's test script.** Native runners do
   not implement every mocking primitive the project's test framework exposes. Always go through
   `${tooling.commands.test}`.

## Backend / API layer

6. **Hand-rolled role checks inside the generic authenticated procedure.** Use the narrower
   admin or tenant-scoped procedure the router already exposes.
7. **Per-request provider client construction.** Reuse the singletons the backend core module
   already exports — client, orchestrator, `db`, logger factory.
8. **Localized error text used as contract.** The client branches on an error *code*, never on a
   substring. Surface it via `cause: { code }` so the error formatter exposes it.
9. **Wall-clock race in tests.** Freeze time for boundary tests instead of reading the clock twice.
10. **`typeof === 'number'` on stored numerics.** The driver may return a string or a decimal type;
    guard with an explicit finite-number check.
11. **Tenant defense-in-depth missing on child fetches.** Even when the parent rows are already
    scoped by tenant and the child has a foreign key to the parent, fetching children by
    `inArray(child.id, parentIds)` **without** a tenant filter leaks across tenants on a corrupted
    row: a foreign key proves the referenced row exists, never that the ownership chain agrees.
    Observed shape — a list procedure joined a child table through a join table's id column only,
    and one corrupted join row returned another tenant's records.
12. **Awaiting a third-party API inside a webhook handler.** It gates the provider's ack on someone
    else's latency; the provider redelivers, the handler runs again, and the cascade begins. Extract
    the call and fire it after the database writes, with a never-throws contract so it needs no
    wrapping try/catch. Counter-case: if the result writes back to the database, it *is* part of the
    request — await it inside a try/catch with explicit logging.
13. **Webhook without idempotency.** `INSERT … ON CONFLICT … DO NOTHING RETURNING id`; a null id
    means it was already processed.

## Frontend

14. **Inline object or array prop = a new reference every render.** Memoize, hoist to module scope,
    or use a stable selector — especially in router-state selectors that `.map()`, which defeats
    structural sharing.
15. **`staleTime` different from `refetchInterval`.** Double-fetch storms. Set them equal.
16. **`gcTime` below `staleTime`.** Refetch on every remount. Keep `gcTime >= staleTime`.
17. **`href="#"` for an action.** Use a button. A real anchor is for navigation.
18. **Animating `width` / `height` / `top` / `left`.** Layout thrash. Use `transform` and `opacity`;
    for an accordion, `grid-template-rows: 0fr` to `1fr`.
19. **A dialog footer without `flex-shrink-0`.** It disappears inside a scrollable flex column.
20. **Inline arrow on a memoized child.** A fresh function every parent render, compared by
    reference, so the memo never holds. Pass the stable setter directly, or wrap it. Hottest when
    parent state changes at 60 fps.
21. **Multi-touch gesture without pointer discrimination.** A handler tracking a single "active"
    flag is hijacked by a second simultaneous pointer, which overwrites the gesture origin mid-drag
    and ends it on the wrong release. Store the gesture's pointer id and reject the others.
22. **"Uncontrolled" prop read once through initial state.** Later changes to the prop never reach
    internal state. If the prop doubles as a reset signal — a refetch updates it — sync it in an
    effect guarded by "not controlled", or stale state persists across every refresh.

## Integrations

23. **A connect-time presence flag can kill inbound routing.** Several long-lived messaging socket
    clients stop delivering inbound events when the socket is opened announcing presence. Open it
    silent and send presence explicitly afterwards.
24. **Tight reconnect loop after a disconnect.** An explicit state machine plus exponential backoff;
    different disconnect reasons need different recovery.
25. **OAuth expiry not pre-checked.** Check before using stored credentials and refresh proactively.
26. **Slow webhook acks.** Answer 200 first, process after.
27. **Pixel and server-side deduplication needs the event id in the options argument**, not inside
    the data payload. Put it in `data` and the pixel still fires while the vendor does *not*
    deduplicate it against the matching server-side event — double-counted conversions. The
    server-side call reuses the same id value.
28. **Untrusted claim from memory or an ADR.** When a note cites a removed file or a deprecated
    flag, verify with grep before acting. Memory ages; the tree does not lie.
29. **A "never use transactions here" rule that outlived its driver.** See
    `Skill("debugger") § Iron Law` — the doctrine is there because it is load-bearing enough to sit
    in the skill body.

## Build, CI and delivery

30. **Static imports of shared data inside lazy-split modules defeat code splitting.** Extract the
    data into a pure module imported separately.
31. **CI secrets in a job-level `if:`.** Produces a "workflow file issue" that fails in zero
    seconds. Use `continue-on-error` or a non-secret variable.
32. **Build OOM on the CI runner.** Raise the runtime's old-space size in the build environment.
33. **Concurrent backend deploys can exhaust a small host.** Serialize with a job-concurrency group
    so the second deploy queues instead of building alongside the first.
34. **CRLF in commits blocks CI.** Enforce LF through `.gitattributes`; recover with
    `${tooling.commands.format}` then `git add --renormalize .`.
35. **Direct push to a protected branch.** Work goes through `${git.workBranch}` and a pull request,
    `[skip ci]` included.
36. **A schema file that compiles but was never applied.** It fails on the next deploy, not in
    review. Name who applies it and when.
37. **Turbo `--dry=json` EPIPE is not a Node crash.** Symptom: SIGABRT on `node …/turbo` and bun,
    node's `si_code` is `SI_USER`, stack is `ProcessWrap::OnExit` → `node::Kill` → `uv_kill`.
    Cause: turbo panicked `failed printing to stdout: Broken pipe (os error 32)` because the
    agent's Bash capture is a pipe; the JS wrapper then `process.kill(process.pid, signal)`.
    Do not raise `--max-old-space-size`, reinstall Node, or re-run the same command. Inspect
    the graph with `Skill("bun-verify")` `scripts/turbo_dry_json.py`. Detail:
    `${CLAUDE_PLUGIN_ROOT}/skills/bun-verify/references/turbo-dry-json-epipe.md`.
