# Safety floor

The invariants every agent carries. Subagents do not inherit the main session's instructions, so an
agent mirrors only the sections it needs and marks the source:

```markdown
- <!-- mirror of safety-floor.md §1 --> Never commit, push, checkout a protected branch, merge, or
  mutate Git history without explicit approval for that action and scope; same-scope session
  approval remains valid.
```

When this source changes, update its mirrors.

---

## §1 — Git and anything that leaves the repository

No commit, push, protected-branch checkout, merge, rebase, tag, history rewrite, PR, release or
deploy without explicit approval for that action and scope. An approval already given in the session
remains valid for the same action and scope; it never authorizes a different outward action.

Review, research and audit agents do not run state-changing Git commands. A hook denial is the
rule, not a workaround opportunity.

## §2 — Tenant isolation and personal data

In a multi-tenant system, every data path that is not explicitly administrative stays scoped by the
tenant key the project declares. This holds in queries, caches, URLs, logs, error messages, rendered
state and test fixtures alike.

Personal data is never echoed back in full. A report names `path:line` and the kind of data, masked.

## §3 — Irreversible data operations

Schema migrations, destructive SQL, bulk updates, index drops, queue purges, shared cache flushes,
and any irreversible operation require the exact statement and explicit approval. A migration needs
a rollback path.

Auth, payment, and PII changes also require explicit authorization for the affected action and
scope. Existing session approval covers that scope; a new sensitive operation needs its own approval.

## §4 — Secrets and production configuration

Never print, log, commit or embed secrets; report location and kind masked. Never weaken production
configuration, authentication, CORS, certificates, or required values to make work pass.

## §5 — Repository tooling

Use the project's declared tooling; do not substitute familiar tools. If a gate is undeclared, say
so. JS/TS follows `130-typescript7-oxc-gates.md`. Files stay LF-only.

## §6 — Scope

Fix what was asked. A defect found on the way is reported, not fixed in the same change, unless it
blocks the task outright — and then it is called out explicitly.

Never touch a file the user has dirty in the working tree without saying so first.

## §7 — Completion claims

"Done", "fixed" and "passing" require applicable command evidence under
`shared/015-verification-gate.md`; a regression fix needs a check that would have failed before the
fix. State what could not be verified.

## §8 — Accessibility

WCAG 2.2 AA contrast, keyboard operability, visible focus, correct semantics, and honoured
`prefers-reduced-motion`. These are not polish and they are not negotiable against visual
preference.
