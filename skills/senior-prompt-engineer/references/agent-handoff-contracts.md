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

**Compact variant.** A lookup returns `Status` plus one `path:line — symbol — note` row per hit; a
review returns its verdict plus one `severity | path:line | problem | fix` row per finding, then
only the Context Handoff fields that carry something. Security findings keep a plain-prose risk.

Extend the existing fields, never the envelope keys: the list below applies to plan-bound or
resumable returns. Ordinary returns fill only applicable fields in ≤ ~400 words; leave detail in
existing artifacts.

- **Artifacts:** decisive sources, scoped results, plan/sprint/snapshot/ledger links and
  new/removed files.
- **Decisions:** objective, completed/pending work, choices/rejected attempts and reasons; exact
  authorization action/scope and provenance (user message or approval artifact). Record project,
  worktree, branch/HEAD, staged/unstaged state and source/config/consumer digests; graph evidence
  also records provider/scope.
- **Quality gates:** exact command, result/exit, evidence location and tested snapshot (files,
  config, dependencies, environment), plus validity and invalidators.
- **Risks:** restrictions, unresolved questions, missing evidence/authority and freshness limits,
  each with mitigation or bounded recheck.
- **Resume hint:** exactly one next action with scope and prerequisites.

Unchanged SHA alone is insufficient. Reuse while relevant identities and freshness hold; invalidate
dependent findings when they change. Keep structural and card/semantic evidence distinct. Record
unknown state explicitly; do not invent telemetry, dump graph output or create a second memory.

Recorded authorization grants no new permission or opt-in; verify action/scope against its provenance
and applicable rules. When writing a session/plan checkpoint, read `${CLAUDE_PLUGIN_ROOT}/commands/evolve.md § 4` for that format; do not copy the agent envelope into a second memory.

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
through `sdd.py consult reserve|record` in the plan's existing workspace; retain the ledger on resume.
Optional `fallback` and bounded `reason` record that routing.

### Codex typed coordination (optional Jev)

Only the parent/controller at depth zero uses `codex/coordinate.mjs`; required reviews remain named
and separate. When enabled, Jev may choose one catalogued agent, skill, command or `main` method,
including same-model specialists. It selects a route only: it never authorizes,
dispatches, reviews or completes work.

Three authorizations are distinct: enable `codex.evaluation.enabled` in host configuration;
authorize configuring `AI_GATEWAY_API_KEY` in the active global Codex environment; then authorize
the bounded paid evaluation batch. Installation, a credential, prior result or replay grants none of the
others. Optional `timeoutMs` is 100–60000 (default 10000). No credential discovery, chat fallback,
model substitution or retry.

Pass JSON on stdin to:

```bash
bun "${CLAUDE_PLUGIN_ROOT}/codex/coordinate.mjs" <catalog|init|link-plan|next|return|finish|status> --project . --session <ID>
```

Each object includes `{"requesterRole":"parent","depth":0}`. The minimum event payloads are:

```json
{"request":"<scope>","taskId":"T1","owns":["<path>"],"checks":[{"name":"<check>","argv":["<runner>","<arg>"]}]}
{"allowed":["agent:verification"],"capabilities":[{"model":"<resolved>","reasoningEffort":"<resolved>","status":"SUPPORTED","evidence":"<smoke>"}]}
{"ticket":"<ticket>","handoff":{"status":"COMPLETED","confidence":4,"artifacts":[],"qualityGates":[],"decisions":[],"risks":[],"nextAgent":"NONE","resumeHint":"<next action>"}}
{"planPath":"<approved-plan-path>"}
```

They are respectively `init`, `next`, `return` and `link-plan`; `finish`, `catalog` and `status` need
only the actor fields. The adapter captures the current snapshot for `finish`; pass minimal
non-sensitive evidence otherwise. It collects no repository history automatically.

1. `catalog` returns source-derived eligible actions. `init` persists request, task, owned paths,
   approved checks and a baseline before selection.
2. `next` accepts the bounded allowed set plus real `SUPPORTED` model/effort capability evidence,
   records one choice and returns `executionAuthorized`, selected methods and a seven-section prompt.
   The parent executes that native agent dispatch or main skill/command method.
3. `return` accepts the Context Handoff and runs approved checks afresh, hashes declared artifacts
   and rejects scope drift. `status` exposes resumable state. The parent calls `next` only if another
   route remains to choose. Once the return proof, current snapshot and linked plan are complete, the
   parent calls `finish` directly; this does not make another Jev evaluation.
4. Before approved implementation, the parent must use `link-plan` with the relative `planPath`
   before Phase C. Linked tasks and gates require real evidence before finish. Planning-only work
   may finish against its original checks without executing the proposed plan. The controller owns
   this scope distinction; the adapter does not infer implementation approval from a plan file.

The ledger retains typed request, policy identity and choice; a fingerprint binds input. Only a fresh
transient `callAuthorized: true` sends one request. The Jev cap is three evaluations per task and
coordination actions use `graphGuardrails.maxSpawnsPerWorkflow` (default 8). Duplicates, pending or
failed decisions do not resend; replays need no credential or traffic. `evaluationResult` retains
model, choice and probabilities; `evaluationError` has a bounded generic reason. Unknown capability
blocks without fallback. The parent uses no probability threshold and owns the next action. CLI exits
are 0 success/skipped, 2 invalid input/configuration, 4 blocked/capped/pending, and 1 unexpected
failure. Plans resolve in the host Git root, including symlinks; recorded verdict equals typed choice.

For user-visible acceptance, select `verification` when browser proof is useful; it loads
`webapp-testing`. Use an authorized target and focused smoke first, then return screenshot plus
console/network evidence or `BLOCKED`. Browser proof does not replace fresh declared checks.

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

For two or more agents, add the findings table in `parallel-batch-contracts.md`. Consolidation
dedupes artifacts/findings, a single gate FAIL fails the batch, and the worst status wins
(`BLOCKED` > `REVISION_REQUIRED` > `COMPLETED`).

## 6. What NOT to put in the handoff

Do not narrate the journey, repeat the prompt, dump skill text, hide uncertainty, or claim done
without evidence. Lead with outcome and preserve exact paths, commands, numbers and decisions.

Owner: `senior-prompt-engineer` skill.
