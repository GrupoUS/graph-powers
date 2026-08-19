# Layer map

> Loaded by the `planning` skill to order sprint phases and analyse dependencies.

A plan that reaches presentation before the data shape is fixed gets rewritten. Layer ordering is
the cheapest way to stop that, and it is the same idea in every stack: **build in the direction the
dependencies point.**

---

## Where the real map comes from

This file carries the generic ordering. The project's actual layout is read, in this order:

1. `${rulesDir}/layer-map.md` — if the project wrote one, it wins outright
2. `paths.*` in the config — `schemaRoot`, `backendRoot`, `frontendRoot`, `componentsRoot`,
   `libRoot`, `stylesRoot`
3. the repository itself — read it before assuming

**An empty `paths.*` field means the project has no such layer.** A static site has no
`schemaRoot`, and a plan that invents a data phase for one is a plan for a different repository.
Drop the layer; do not fabricate it.

---

## Generic ordering for a cross-layer change

| # | Layer | Typical home | Skip when |
|---|---|---|---|
| 1 | Data — schema, migration, fixtures | `${paths.schemaRoot}` | field empty |
| 2 | Cross-cutting singletons — db handle, logger, provider clients | `${paths.backendRoot}/_core` or equivalent | no backend |
| 3 | Shared types and constants used by more than one app | shared package | single app |
| 4 | Service layer — external provider integrations | `${paths.backendRoot}/services` | no external providers |
| 5 | API surface — handlers, procedures, routes | `${paths.backendRoot}` | no backend |
| 6 | Registration — the router or index the new surface must appear in | entry index | — |
| 7 | Client data layer — hooks, queries, SDK calls | `${paths.libRoot}` | no client fetching |
| 8 | Presentation primitives — design-system components | `${paths.componentsRoot}` | no new primitive |
| 9 | Presentation composites and pages | `${paths.frontendRoot}` | no UI change |
| 10 | Cross-cutting — auth, telemetry, SEO, a11y, performance | wherever the project puts it | — |
| 11 | Verification — the gates from `tooling.commands`, then browser E2E if UI moved | — | — |

Step 6 is the one that gets forgotten. A handler nobody registered is a file, not an endpoint.

---

## Ordering rules that hold regardless of stack

- **Schema before anything that reads it.** A type generated from a schema that has not been pushed
  compiles locally and fails on deploy.
- **Registration in the same phase as the thing being registered**, never "later".
- **Validation schemas at module level**, not rebuilt inside a handler on every call.
- **Presentation last.** Not because it matters least — because it is the layer that has to change
  again when an earlier one moves.

---

## Forbidden cross-layer patterns

These are stack-independent; a project adds its own to `${rulesDir}/`.

- Presentation importing server internals directly instead of going through the declared client layer
- Two layers at the same level importing each other — that is one layer wearing two names
- A lower layer re-instantiating a singleton the cross-cutting layer already owns (db handles,
  loggers, provider clients)
- Feature folders importing across each other; only the shared primitives layer is a legitimate
  fan-in point
- A type duplicated in two apps instead of living in the shared layer — the exact divergence this
  whole plugin exists to prevent, one scale down
