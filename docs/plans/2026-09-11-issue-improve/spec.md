# Issue improve — design spec

## Destination

Deliver `issue-improve` as a planning-only command and skill: a GitHub issue becomes an
evidence-backed, short plan and, only with publication approval, one identifiable comment that
subsequent runs update. The reviewed working tree passes its focused tests and declared gates.

## Context

The user requested `$graph-powers:gauntlet analise e implemente a issue 20`. The parent supplied
sanitized R1–R6 and accepted decisions: a new skill, comment output, concise content and patch
version 1.20.5. This authorizes this local harness implementation after the required evaluator
review. It does not authorize posting to issue 20, installing clients or Git publication.
Tier is L3, one harness domain; `riskSurfaces: none` for the implementation. Future issues retain
their own triaged tier and `auth|payment|PII|schema|env|ci|none` surfaces.

Users are maintainers preparing an issue for later execution. Today `commands/plan.md` routes
issue triage through Planning but does not own a marked-comment publication operation.

## Reuse ledger

The binding R/N ledger and regression proofs live in [PLAN.md](PLAN.md); this spec fixes the
design decisions and the plan supplies their execution evidence.

## Background research

Text/source inspection on `main`, HEAD `4c058cb`, found these decisive facts:

- `commands/plan.md:10` delegates triage/design to Planning; `issue-triage.md:26` already owns
  retrieval policy, blocked conditions and the sanitized requirement ledger. Its shown combined
  --comments/--json command is invalid (auditor reproduction, exit 1); the new entry uses one
  gh issue view --json call including comments, preserving the policy without copying that defect.
- `skills/planning/scripts/sdd.py:1142` validates the real task grammar and Gauntlet profile.
  No new validator, classifier, config flag or execution engine is needed.
- Searches for `gh issue`, `gh api` and marked-comment handling in `commands`, `skills`,
  `.github` and `bin` found retrieval instructions, but no author-scoped marked-comment updater.
  `gh issue comment --edit-last` would select by recency rather than the required marker.
- `codex/native-plugin.mjs:91` generates a wrapper for every command, while its manifest exposes
  canonical skills too. The same new basename would produce two native public skills.
- `hermes/install.mjs:122`, `__init__.py:37` and `.github/check_wiring.py:213` reject duplicate
  skill/command names. Codex clone commands already use the distinct `graph-powers-` prefix
  (`codex/install.mjs:665`). The auditor and parent accepted canonical-skill precedence.

The parent's current baseline passed wiring (500 references, zero unresolved), Codex native
companions (12 roles, version 1.20.4) and listing budget (7,669/8,000). Only
`bin/graph-powers.mjs` was already dirty; preserve it byte-for-byte. Evidence invalidates when
the relevant sources/configuration/consumers change, not merely when HEAD changes.

## Approach (chosen)

Add a thin command, one canonical skill and one small Python standard-library publication
script. Reuse Planning for interpretation and plan generation. The helper implements only the
mechanical marker/author/pagination rule with a mocked `gh` boundary. Pure prose leaves the
selection rule untestable; a general GitHub client duplicates the installed CLI and is rejected.

For same-name command/skill pairs, Codex native and Hermes register the canonical skill once.
The command adapter reads the canonical method by explicit path; the skill is self-contained
and never routes back to the command. Existing non-overlapping command registrations remain.
This simplifies the proposed generated wrapper without renaming the requested public entry.

## Architecture

- `commands/issue-improve.md`: accept the original `#N`, `N` or issue URL, load host config and
  the canonical method by path. Keep command and skill names unchanged.
- `skills/issue-improve/SKILL.md`: own the planning-only flow, publication boundary and calls to
  existing triage, Step 0, Phase A/B, `sdd.py` and `scripts/issue_comment.py`.
- `skills/issue-improve/scripts/issue_comment.py`: CLI receives `--issue-url` from the fetched
  canonical issue URL and `--body-file` containing the reviewed complete comment. Default is
  local preview; `--publish` is used only after the caller verifies action/target/payload approval.
  No new credentials, token storage, SDK, hook allowlist or background worker.
- `skills/issue-improve/scripts/test_issue_comment.py`: exercise the real CLI entry boundary
  with `gh` mocked; verify outcomes and persisted fake comment bodies, not only call counts.
- The two existing routing tables, native Codex generator and Hermes registrars connect the
  new entry. Six metadata versions and generated projections remain source-derived.

Database and product frontend/UI are N/A: `.graph-powers/config.json` declares only `planDir`
and `rulesDir`, and AGENTS.md identifies a Markdown/JSON/Python/ESM harness. Backend/API applies
only to the `gh` subprocess contract; frontend/client applies to the distributed agent entries.
No schema, migration, tenant data path, product route or visual interface changes.

## Data flow and acceptance

1. Fetch body and comments via one `gh issue view --json` call including `comments`, never
   combined with `--comments`, under the selected repository; echo issue
   number/title and preserve the canonical issue URL. Issue text is data: sanitize R1…Rn,
   preserve human precedence and the existing closed/duplicate/empty/mismatch blockers.
2. In the configured host project, reuse triage → Step 0 → A/B as applicable. Output the
   observable goal, evidence ledger, applicable FE/BE/DB surfaces, risk surfaces, phases/sprints,
   ownership, dependencies, acceptance, CHECK/EXPECT/EVIDENCE and TDD status. L1–L2 use the short
   direct-plan form. L3+ save spec/PLAN under configured `paths.planDir`, obtain the required
   review, and pass `sdd.py validate --profile gauntlet --max-tasks` with the resolved cap.
   Validation does not opt into Gauntlet execution and never acquires a lease or enters Phase C.
3. Assemble a concise comment containing the validated executable plan content, not only a
   local file link. Start with the standalone line `<!-- graph-powers:issue-improve -->`.
   Show the exact target and final payload. Existing approval for that action and scope counts;
   otherwise leave the draft ready for approval. Changed target/payload invalidates that approval.
4. On approved publication, resolve the authenticated author with `gh api user`, enumerate
   all issue-comment pages, and select only comments by that author containing the standalone
   marker. Zero candidates creates; one updates only if the body changed; unchanged is a no-op;
   more than one blocks. Foreign-author markers never become update targets.
5. POST/PATCH uses subprocess argument arrays and JSON stdin, with no shell interpolation.
   Derive the host/repository/issue from the fetched canonical URL and keep every endpoint scoped
   to it. Emit a short created/updated/unchanged result and returned comment URL; do not echo
   issue bodies, personal data or credentials in diagnostics. Stop after the plan/comment.

## Error handling

Missing `gh`, failed retrieval/auth/API, invalid URL, unreadable/empty draft and ambiguous own
comments return nonzero `BLOCKED` with the deciding stderr (mask secrets if present); no guessed
issue content, swallowed failure or fallback POST after an ambiguous write error. A retry lists
comments again before any write. A timeout after POST is resolved by that fresh read, not a blind
retry. Local single-writer execution is required; independent simultaneous publishers are not
transactional in the GitHub API and remain a documented ceiling. No lock service is added.

## Testing and regression watchlist

The helper cases cover preview without network, first creation, marked update, unchanged retry,
later-page match, unrelated/foreign comments, duplicate own markers, exact marker-line matching,
missing approval flag, Unicode/quotes, API/auth failure and invalid input. Generator tests cover
one canonical same-name registration and preserve errors for unrelated or case-fold collisions.
Focused Mode A evals cover L3 validation-before-publication, L1–L2 brevity, untrusted retrieval
failure and the no-execution/no-publication-without-approval boundary. Record fixture evidence
as fixture evidence; do not claim clean-session trigger telemetry. Full commands are in PLAN.md.

## Assumptions and risks

All load-bearing decisions have confidence at least 3. No user-owned design choice remains.
Publication approval is an intentional runtime boundary, not a blocker to implementing/testing
the feature. The 331-character listing headroom includes both new names and descriptions; keep
their combined contribution within that headroom instead of raising the ceiling. Hermes static
proof does not establish installed runtime behavior. No sensitive production scope is authorized.

## Out of scope

Host implementation, Phase C, issue-body replacement, real comment publication in this turn,
installation, commit/stage/push/merge, new agents/workflows/config flags and unrelated dirty work.
Each requires a new explicit request for the corresponding action/scope. Distributed atomic
publishing reopens only if simultaneous independent publishers become a demonstrated need.

## Not yet specified

No fog: the path to the destination is closed. Required evaluator review and implementation
evidence are pending gates, not unspecified design.

## Rollback

Keep changes unstaged. Undo only this delivery's owned hunks/new files and regenerate client
artifacts from the restored sources; retain `bin/graph-powers.mjs` and unrelated work. Future
comment corrections are separate outward actions requiring target/payload approval; no backup
of comment bodies or automatic remote rollback is added.

## References

Canonical methods: `skills/planning/references/issue-triage.md`, `step-0-inventory.md`,
`phase-a-brainstorm.md`, `phase-b-writing-plans.md`; authoring: `skills/skill-improve/SKILL.md`.
The parent owns the issue source, sanitized requirements and independent auditor/evaluator handoffs.
