> Hermes auxiliary: `content/` paths are `file_path` values relative to the registered-document parent. Apply the loaded graph-engineering mapping and host policy; this file is served without template expansion.

# Agent Handoff Contracts

Canonical contract for the execution floor, planning and agents. Keep this file as the only owner of
the spawn context, return, consultation and recovery shapes.

## 1. Spawn template (5 mandatory context fields)

```markdown
## TASK
<one bounded task>
## EXPECTED OUTCOME
<deliverables and observable acceptance criteria>
## MANDATORY CONTEXT
**Original request:** <lossless scope/authorization>
**User decisions:** <chosen options or —>
**Prior agent findings:** <relevant completed facts or —>
**Current plan state:** <phase/task and completed work>
**Do NOT redo:** <already-covered work or —>
## REQUIRED SKILLS & TOOLS
<methods to load, tools and relevant project authorities; supply excerpts when local reads are forbidden>
## MUST DO
<requirements and owned paths>
## MUST NOT DO
<scope boundaries and forbidden actions>
## RETURN FORMAT
Context Handoff from this contract; add the findings table for a parallel batch.
```

Include exact text when its wording is authoritative (authorization, errors, contracts). The execution
floor requires this seven-section envelope; the five context fields prevent rediscovery. The parent
supplies applicable AGENTS.md, config/rules and domain skills or their exact paths; an external-only
researcher receives the necessary facts and return/rubric excerpts in its prompt, not local read tasks.

## 2. Context Handoff (return schema)

```markdown
## Context Handoff
- **Status:** COMPLETED | BLOCKED | REVISION_REQUIRED
- **Confidence:** 1-5
- **Artifacts:** [{ path, lines, action }]
- **Quality gates:** [{ name, status, evidence }]
- **Decisions:** [{ what, why }]
- **Risks:** [{ desc, mitigation }]
- **Next agent:** <name> | NONE
- **Resume hint:** <one sentence>
```

Extend the existing fields, never the envelope keys:

- **Artifacts:** touched/decisive sources, scoped query results and links to active plan, sprint,
  snapshots and ledgers when present; name relevant new/removed files.
- **Decisions:** objective and completed/pending work; choices and reasons; rejected attempts and
  why not to repeat them; existing authorization's exact action/scope and provenance (user message
  or approval artifact). Record project/worktree, branch/HEAD, relevant staged/unstaged state and
  source/config/consumer digests; graph evidence also records provider/scope.
- **Quality gates:** exact command, result/exit, evidence location and tested snapshot, including
  relevant files, configuration, dependencies and environment; identify validity and invalidators.
- **Risks:** critical restrictions, unresolved questions, missing evidence/authority and freshness
  limits, each with mitigation or the bounded recheck.
- **Resume hint:** exactly one next action, preserving its scope and prerequisites.

Unchanged SHA alone is insufficient. Reuse while relevant identities and freshness hold; invalidate
dependent findings when they change. Keep structural and card/semantic evidence distinct. Record
unknown state explicitly; do not invent telemetry, dump graph output or create a second memory.

Recorded authorization grants no new permission or opt-in; verify action/scope against its provenance
and applicable rules. When writing a session/plan checkpoint, read `content/commands/evolve.md § 4` for that format; do not copy the agent envelope into a second memory.

### JSON form (for a consolidating caller, and for tooling)

```json
{"status":"COMPLETED","confidence":4,"artifacts":[{"path":"<path>","lines":"<lines>","action":"modified"}],"qualityGates":[{"name":"<gate>","status":"PASS","evidence":"<output>"}],"decisions":[{"what":"<decision>","why":"<why>"}],"risks":[{"desc":"<risk>","mitigation":"<mitigation>"}],"nextAgent":"NONE","resumeHint":"<next step>"}
```

## 2a. Consultation request/result envelope

```json
{"taskId":"T2","decisionKey":"architecture-boundary","question":"<question>","evidence":["path:line or output"],"options":["option-a","option-b"],"recommendation":"option-a","risk":"<uncertainty>","verdict":"PENDING","requesterRole":"parent","depth":0,"backend":"evaluator","capabilityStatus":"SUPPORTED","status":"RESERVED"}
```

Only the parent/controller at depth zero reserves/records a stable `decisionKey`; workers and
read-only reviewers cannot consult. Evaluators cannot spawn or consult. A duplicate returns its recorded result. Caps return
`USER_REQUIRED`. Native Fable/advisor requires positive `SUPPORTED` metadata; `UNKNOWN` or
`UNSUPPORTED` selects the existing read-only evaluator fallback, never a native probe. Unresolved
capability or an unavailable fallback returns `BLOCKED` without a spawn or retry. Reserve and record
through `content/skills/planning/scripts/sdd.py consult reserve|record` in the plan's existing workspace; retain the ledger on resume.
Optional `fallback` and bounded `reason` record that routing.

### Codex typed routing (optional Jev)

Only the parent may consult Jev for material uncertainty between eligible roles/models. Required
reviews remain separate and use the named reviewer. With no doubt, or identical resolved model
and effort across candidates, choose the role directly; do not pay for a redundant comparison.
Jev returns a recommendation, never review prose, authorization or an automatic spawn.

Explicitly enable `codex.evaluation.enabled` in the host configuration; supply `AI_GATEWAY_API_KEY`
through the environment. Optional `timeoutMs` is 100–60000 (default 10000). No credential discovery,
chat fallback, model substitution or retry. Invoke with JSON on the command runner's stdin:

```bash
bun "content/codex/evaluate.mjs" --project . --plan "<PLAN_FILE>"
```

Input: `materialDoubt` (boolean), `taskId`, `decisionKey`, `question`, `evidence` (string array),
`risk`, `state` (minimal non-sensitive object), `requesterRole` (parent/controller), `depth` (zero),
and `candidates`. Each candidate contains `id`, canonical `role`, and `capability` with `model`,
`reasoningEffort`, `status: SUPPORTED`, and `evidence` referencing a real smoke. Model/effort must
match policy after overrides; a valid slug alone proves no account capability. Updating policy
requires revalidating the latest official family IDs and smoking the resolved combination.
The adapter sends no automatically collected repository content or history.

The existing ledger uses backend `jev`, retaining an `evaluationRequest` with model, state,
choice question, resolved candidates and policy identity. A fingerprint binds immutable input.
Only a fresh reservation's transient `callAuthorized: true` permits sending; it is never persisted.
Duplicates return false, including pending decisions after a crash. Changed input under the same
key is rejected. Pending means reconcile the outcome, never resend. The cap remains three per task.

`evaluationResult` retains model, eligible choice and probabilities; `evaluationError` contains a
bounded generic code/reason. Terminal replay needs no credential or traffic. Unknown Jev capability
blocks without fallback; legacy Fable/advisor routing is unchanged. The parent consumes the result
without an uncalibrated probability threshold and remains responsible for the next action.
CLI exits: 0 for success/skipped, 2 for invalid input/configuration, 4 for blocked, capped or pending
decisions; unexpected adapter failure is 1. A plan must resolve inside the same Git root as the host,
including through symlinks. Jev's recorded verdict must equal its typed choice.

## 3. Status semantics + invariants

| Status | Required condition |
|---|---|
| `COMPLETED` | gates pass; artifacts may be `[]` only for read-only work |
| `BLOCKED` | risk includes mitigation (use `ESCALATE` when applicable) |
| `REVISION_REQUIRED` | reviewer-only; decisions name failed criterion/threshold |

A critical finding below confidence 3 is `BLOCKED`. `nextAgent: NONE` is terminal
`COMPLETED` only. A completion without gate evidence is defective.

## 4. Coordinator failure recovery

Forward a reviewer failure to its responsible specialist twice at most. A third would-be revision
returns `BLOCKED` with criterion and last evidence; the main agent runs `/debug recover`.
Do not loop or escalate to the user before that triage.

## 5. Parallel batch override

For two or more agents, add the findings table in `content/skills/senior-prompt-engineer/references/parallel-batch-contracts.md`. Consolidation
dedupes artifacts/findings, a single gate FAIL fails the batch, and the worst status wins
(`BLOCKED` > `REVISION_REQUIRED` > `COMPLETED`).

## 6. What NOT to put in the handoff

Do not narrate the journey, repeat the prompt, dump skill text, hide uncertainty, or claim done
without evidence. Lead with outcome and preserve exact paths, commands, numbers and decisions.

Owner: `senior-prompt-engineer` skill.
