# Node anatomy — what a node looks like, and what the gate cannot see

Step 6 of the skill. Two shapes — the downlink row the root carries, and the child node — plus one
example, one before-and-after, and the checklist that needs a reader rather than a script.

## The root's side: a downlink row, not a section

Upstream adds an `## Intent Layer` section to the root file. Here the root `AGENTS.md` already has
the place for it: the `Where things live` table that `templates/AGENTS.md` ships and step 4a
fills. A child node is one more row there, with the node's path in it:

```markdown
## Where things live

| Area | Path | Read first |
|---|---|---|
| API and services | `packages/api/` | `packages/api/AGENTS.md` |
| Web app | `apps/web/` | `apps/web/AGENTS.md` |
| Shared types | `packages/types/` | — small enough to read whole |
```

That table is the root's downlink index, and `check` reads it: a child whose path appears in no
ancestor node is an orphan. One line above the table, once, is enough for the directive upstream
repeats in every root: **before editing under a path with a node, read the node first.**

Global invariants stay in the root's `Invariants` section, where the template already puts them.
Do not open a second invariants list for the intent layer; one list, in the root.

## The child node

```markdown
# {Area}

Owns {one sentence}. Does NOT own {the neighbour it is confused with} (`../neighbour/AGENTS.md`).

## Entry points
- `src/api/` — the public surface, reached through the gateway only
- `src/workers/` — background processors

## Contracts and invariants
- Every external call goes through `src/clients/`; nothing else opens a socket
- Idempotency key on every mutation — the `ProcessorClient` type enforces it since the
  duplicate-charge incident

## The usual change
Adding a {typical unit}:
1. type in `src/types/`
2. adapter in `src/adapters/`
3. register in `src/adapters/index.ts`

## Anti-patterns
- Bypassing `src/clients/` — it is where retries and tracing live
- Storing card numbers — tokenise, always

## Pitfalls
- `src/legacy/` looks dead and handles every pre-2023 account

## Related
- Database layer: `./db/AGENTS.md`
- Shared utilities: `../shared/AGENTS.md`
```

The purpose line is the first line after the title and it is a sentence, not a heading — `check`
looks for it within the first five lines. Relative paths throughout, so the node survives a move
of the whole subtree.

## A monorepo root, as a node

```markdown
# Platform

Monorepo: payment, billing and user services, one message queue between them.

## Invariants
- Services talk through the queue, never by direct HTTP — the outage of 2025-11 was a direct call
- Runtime configuration lives in `platform-config/`; nothing is hardcoded
- Shared types come from `packages/types/`; a service that redeclares one has forked it

## Where things live
| Area | Path | Read first |
|---|---|---|
| Payment | `services/payment/` | `services/payment/AGENTS.md` |
| Billing | `services/billing/` | `services/billing/AGENTS.md` |
| Shared libraries | `packages/` | utilities only — business logic does not go here |
```

## Compression, before and after

Before, about 800 tokens:

```markdown
# User Service

## Overview
The User Service is a microservice that is responsible for managing user accounts in our
platform. It handles user registration, authentication, profile management and user preferences.
This service is built using TypeScript and Express.js, and it uses PostgreSQL as its database
through Prisma ORM.

## Technologies Used
- TypeScript 5.0
- Express.js 4.x
- PostgreSQL 15
…
```

After, about 250 tokens:

```markdown
# User Service

Manages accounts, auth and preferences. Express + Prisma + PostgreSQL.

## Entry points
- `src/routes/` — REST
- `src/jobs/` — background sync

## Contracts
- Auth tokens come from `packages/auth/`
- User events are published as `events.users.*`

## Anti-patterns
- Never store a password — `packages/auth/hash.ts`
- Never query the users table from another service — consume the events
```

What was cut is what the reader already knows or can see in one file. What stayed is what it
cannot see: where the boundary is, and what crosses it.

## The checklist the gate cannot run

`check` measures size, links, placeholders, the purpose line and the Codex chain. The rest needs a
reader:

- **No duplication with an ancestor.** A contract stated in the root and again in a child will be
  edited in one of them. Say it once, at the lowest common ancestor, and point.
- **Contracts are explicit.** "Handle carefully" is not a contract; "every mutation carries an
  idempotency key, enforced by the `ProcessorClient` type" is.
- **Anti-patterns come from incidents.** One that happened outranks five that might. Attach the
  cost when it is known.
- **The purpose says what it does not own.** The neighbour a subtree is confused with is the most
  useful sentence in the node.
- **Nothing generic.** How to plan, debug or verify comes from the plugin; a node that restates it
  is the drift this harness exists to end, one directory down.
