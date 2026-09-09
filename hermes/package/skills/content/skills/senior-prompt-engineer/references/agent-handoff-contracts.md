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
