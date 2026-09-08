---
name: graph-engineering
description: Apply Graph Engineering workflows inside Hermes.
version: 1.0.0
author: GrupoUS
license: MIT
metadata:
  hermes:
    tags: [Engineering, Delegation, Planning, Verification]
---

# Graph engineering in Hermes

Graph Powers is canonical upstream; this adapter only translates names and limits Hermes cannot
provide. Read the installed plugin's referenced files with `read_file`; do not maintain another
inventory.

| Graph Powers | Hermes |
|---|---|
| Agent invocation | `delegate_task(goal=..., context=...)` with the selected `agent-<slug>` contract |
| Graph Powers skill invocation | `skill_view("graph-powers:name")` |
| Read/Grep/Glob/Bash | `read_file` / `search_files` / `terminal` |
| Web tools | `web_search` / `web_extract`, unless a needed MCP is configured |
| Background read-only spawn | top-level `delegate_task` already runs in background |
| Native hooks | Unsupported: parent carries safety rules and approvals |
| Child clarification | parent `clarify`; child returns the decision point |

## 1. Classify and load only needed context

Use `references/shared/020-complexity-routing.md` and `025-solution-ladder.md`. L1-L2 stay local;
L3 may delegate once; L4-L5 use a disjoint batch; L6+ plans before waves. Read project config when
present, then only matching rules and the nearest authority. Missing config/rule is a stated gap,
not an error or an invented default.

## 2. Choose and dispatch a specialist

Use `030-agent-assignment-matrix.md` and `060-skill-domain-matrix.md`. State the agent contract,
why it fits, required skills and deliberate omissions, and the outcome. Read the contract through
`skill_view("graph-powers:agent-<slug>")`; a read-only contract must become an explicit child
`MUST NOT DO`, because Hermes children inherit parent tools.

Use one `delegate_task(tasks=[...])` call for independent tasks. Each child gets the canonical
seven-section prompt and Context Handoff from
`references/execution-floor.md §4` and the handoff contract. Declare exact disjoint `Owns:` paths.
Read live `delegate_task` limits; do not hardcode concurrency or models. Children do not delegate,
clarify, use memory, or message. They have their own working directory, so pass absolute paths.

## 3. Gauntlet translation

`/gauntlet` and `/verify loop` are **NOT SUPPORTED** Hermes slash commands. When requested, read
`graph-powers:gauntlet` and `graph-powers:verify`, validate the approved plan with
`sdd.py validate ... --profile gauntlet`, and apply the normalized tier. L1-L2 is `NOT ELIGIBLE FOR
GAUNTLET`; invalid input routes to planning. For L3+, acquire the Gauntlet lease before writers,
use disjoint waves within live limits, run each focused CHECK, then an independent critic. A capped
or blocked lane is not success. Release only after PASS.

## 4. Verify and close

Run or reuse the project-declared checks only while their diff, config, and environment remain
relevant and unchanged. Capture exit codes and actual status; a child report is not evidence.
Undeclared JS/TS gates route to `graph-powers:debugger`. Do not add a verification specialist for
ordinary L1-L2 work.

`VERIFIED` means all required signals passed; `VERIFIED-WITH-NOTES` has only documented minor
issues; `NEEDS-WORK` means a required signal failed or could not run. A regression fix needs a test
that would fail before it. Resolve an independent verification specialist once for final Gauntlet
close; use its documented objective fallback once if unavailable and report the degradation.

## 5. External CLI routing

Use `terminal` with a narrow workdir and explicit safety context. Claude Code is preferred for
implementation; Codex CLI plans detailed changes, reviews work it did not write, or is the fallback
after Claude Code stalls. Inspect the resulting diff and verify it yourself.

## Safety carried into every child or CLI

- No commit, push, protected-branch checkout, merge, rebase, tag, PR, release, deploy, or
  publication without explicit approval for that action and scope. The same approved action remains
  authorized in this session; it does not authorize another action.
- Propose irreversible data work with the exact statement and stop for approval.
- Never expose secrets, weaken production/auth controls, violate tenant isolation, or widen scope.
- An approval denial is a gate, not a route-around.

If an agent name fails, follow `references/shared/035-agent-resolution-recovery.md` once. A missing
write-capable specialist blocks the task. Report changed paths, checks with exit codes, and blockers.
