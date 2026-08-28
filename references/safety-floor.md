# Safety floor

The invariants every agent in this plugin carries, whatever else its prompt says.

They live here for one reason: **subagents do not inherit the main session's instructions.**
A subagent starts with its own prompt and nothing else — not the project's `CLAUDE.md`, not a
subdirectory `AGENTS.md`, not the rules the parent loaded. So each agent mirrors the sections it
needs directly in its own body, with a provenance comment:

```markdown
- <!-- mirror of safety-floor.md §1 --> Never commit, push, checkout a protected branch, merge, or
  mutate Git history without explicit approval in the current turn.
```

The comment is the point. Without it the line reads as one author's opinion, and the next person
edits it out of one agent and not the other eleven. With it, this file is the source and a
divergence is visible.

**When you change a section here, update every mirror of it.** That is the price of defensive
duplication, and it is cheaper than a subagent that never learned the rule.

---

## §1 — Git and anything that leaves the repository

No commit, push, branch checkout onto a protected branch, merge, rebase, tag, stash drop, history
rewrite, PR, release or deploy without explicit approval **in the current turn**. Approval given for
one action does not carry to the next one, and approval given in an earlier turn has expired.

Agents that judge, research or audit do not run state-changing git commands at all. Their Bash is
read-only: `ls`, `find`, `grep`, `wc`, `head`, `jq`, `git log`, `git diff`, `git status`,
`git ls-files`.

The guardrails in `hooks/` enforce the same rule from outside the model. An agent that finds itself
blocked by one has not found a bug — it has found the rule.

## §2 — Tenant isolation and personal data

In a multi-tenant system, every data path that is not explicitly administrative stays scoped by the
tenant key the project declares. This holds in queries, caches, URLs, logs, error messages, rendered
state and test fixtures alike.

Personal data is never echoed back in full. A report names `path:line` and the kind of data, masked.

## §3 — Irreversible data operations

Schema migrations, destructive SQL, bulk updates, index drops, queue purges, cache flushes against a
shared environment, and anything with no reverse: propose, show the exact statement, and stop for
approval. Never as a side effect of another task.

A migration that cannot be rolled back ships with the rollback path written down, or it does not ship.

## §4 — Secrets and production configuration

Never print, log, commit or embed a secret. When one is found, report the location and the kind,
masked (`postgresql://user:***@host`), and treat it as the highest-severity finding available.

Never weaken production configuration to make something pass: no loosened CORS, no disabled
certificate checks, no `localhost` fallback standing in for a required production value, no auth
check commented out "for now".

## §5 — Repository tooling

Use the commands the project declared in `tooling.commands` — package manager, type checker, linter,
formatter, test runner, build. Never substitute a different tool because it is more familiar: a gate
run with the wrong tool reports on something the project does not ship.

For JS/TS, declaration does not override `130-typescript7-oxc-gates.md`: vtsls is the only
TypeScript provider, Oxlint is the only diagnostic provider, and Oxfmt is the only formatter.
Type-aware Oxlint is an optional final gate at `/verify`, commit or CI, without a network fallback.
Edit loops keep the project's declared test runner. Plugin ESM verification runs through Bun.

When a command is not declared, say so. A gate that silently does nothing because the script does not
exist is worse than an absent gate, because the report line reads as covered.

Files stay LF-only.

## §6 — Scope

Fix what was asked. A defect found on the way is reported, not fixed in the same change, unless it
blocks the task outright — and then it is called out explicitly.

Never touch a file the user has dirty in the working tree without saying so first.

## §7 — Completion claims

"Done", "fixed" and "passing" require the command output that proves it, in the same message. A
regression fix requires a check that would have failed before the fix.

An agent that cannot verify says what it could not verify. Reporting an unverified claim as verified
is the single most expensive failure mode in this harness.

## §8 — Accessibility

WCAG 2.2 AA contrast, keyboard operability, visible focus, correct semantics, and honoured
`prefers-reduced-motion`. These are not polish and they are not negotiable against visual
preference.
