# Execution floor

How the work is coordinated: when to delegate, how many at a time, who owns which file, and what
comes back. The counterpart of `safety-floor.md` — that file says what must never happen, this one
says how the work is run.

It is a floor, not a menu. What is below holds whatever the task is and whichever harness is
running. Where a rule already has a single owner under `references/shared/`, this file names the
owner instead of restating it: a second copy of a number is how two files stop agreeing.

**Both harnesses, one source.** Claude Code reads it at
`${CLAUDE_PLUGIN_ROOT}/references/execution-floor.md`; Codex reads the copy the installer writes
into its own harness directory, named in the delimited block of the project's `AGENTS.md`. Same
bytes.

**Subagents do not inherit it.** A subagent starts with its own prompt and nothing else, exactly as
`safety-floor.md` describes. What an agent needs from here is §4's return contract, mirrored into its
own body with the same provenance comment the safety floor uses:

```markdown
- <!-- mirror of execution-floor.md §4 --> Return the Context Handoff, and nothing longer than it.
```

The sections about *deciding* the fan-out — §1 to §3 — belong to whoever spawns. The twelve agents in
this plugin have no `Agent` tool, so mirroring those into them would be weight with no reader.

---

## §1 — Delegating is not optional

The ladder is `references/shared/020-complexity-routing.md`, and it is the only one. What this
section adds is that the ladder binds:

| Level | What is required |
|---|---|
| L1-L2 | **Do not delegate.** One file, a known pattern: re-establishing a subagent's context costs more than the parallelism returns |
| L3 | One background agent, at least |
| L4-L5 | Two to three, on disjoint files |
| L6+ | A coordinator and its specialists |

Unsure between two levels, take the higher one. `020`'s other floor — below roughly half an hour of
real work, do not orchestrate at all — is about size, not about permission, and still holds.

Which agent is `references/shared/030-agent-assignment-matrix.md`. Which skill is
`references/shared/060-skill-domain-matrix.md`. Neither is repeated here.

**When a task needs both repository facts and current external behaviour, that is two agents, spawned
in the same message** — `graph-powers:explorer` and `graph-powers:librarian`, both in the background.
Running them one after the other is the most common way a session spends twice the wall clock for the
same answer.

## §2 — One message, background by default

`references/shared/070-parallel-agent-spawn.md` is the rulebook: everything in one message,
`run_in_background: true` for anything read-only, foreground for anything that writes, one return
contract per batch, and the wave width and the session ceiling as configuration keys rather than as
numbers copied into prose.

Spawning agents one per message is not a smaller version of parallel work. It is serial work carrying
the overhead of parallel work.

Hand-writing a `Workflow({ script })` instead of calling one by name has its own contract in
`references/shared/130-workflow-authoring.md`, including the parse failure that happens after the
script is written and before anything runs. Read it first, and check the script with the command it
names.

## §3 — One writer per file

Units that run at the same time own disjoint paths, declared per task, never inferred at dispatch and
never negotiated between two agents already running. The full rule — including what is never parallel
with anything, because its ordering is load-bearing — is `070-parallel-agent-spawn.md § 7`.

Overlap is not a conflict to settle. It is a split that was drawn wrong: re-slice by directory, route
or component family, or lift the shared thing out into its own task.

## §4 — The delegation contract

**Before the prompt, four lines out loud.** They cost nothing to write and they catch the two
failures that are invisible afterwards — the wrong specialist, and a skill left out by accident
rather than by decision:

```
Agent selected:   <name>
Why this one:     <the match between its speciality and this task>
Skills:           <included> — and <omitted>, because <reason>
Expected outcome: <the concrete deliverable>
```

The omission line is the one that earns its place. An included skill announces itself; a skill that
should have been loaded and was not leaves no trace at all.

When the scope is ambiguous — nobody named the agent, two could plausibly own the work, or the
deliverable is not a concrete change — run `Skill("superpowers:brainstorming")` before locking the
choice. Skip it when the agent is named or the matrix is unambiguous.

Every spawned prompt then carries these seven sections. Not six, and not a paraphrase — §7
consolidates mechanically, and it can only do that when every return has the same shape.

```markdown
## TASK
<one atomic task>

## EXPECTED OUTCOME
<concrete deliverables and success criteria>

## MANDATORY CONTEXT
**Original request:** <verbatim, or a short quote>
**Decisions already made:** <what is locked>
**Prior findings:** <summaries only>
**Current state:** <phase / sprint / task>
**Do NOT redo:** <research and work already finished>

## REQUIRED SKILLS & TOOLS
<the skills to invoke, and the explicit tool whitelist>

## MUST DO
- <requirements, nothing implicit>

## MUST NOT DO
- <scope boundaries and forbidden actions>

## RETURN FORMAT
Context Handoff, per `${CLAUDE_PLUGIN_ROOT}/skills/senior-prompt-engineer/references/agent-handoff-contracts.md`.
For a parallel batch: `| # | Finding | Confidence (1-5) | Source | Impact (Low/Med/High) |`,
plus a `Severity (P0-P3)` column when the batch is a review.
```

**After it returns, three questions.** Does it actually work; does it follow the patterns already in
this codebase; and did the agent honour MUST DO and MUST NOT DO. A handoff that reads well is not
evidence — `safety-floor.md § 7` is the standard the answer is held to.

**Filling these seven sections needs no skill.** `Skill("senior-prompt-engineer")` is for *designing*
the machinery, not for using it: a new `agents/*.md` file, a change to the handoff schema itself, or
an LLM feature inside the product. Loading it to write one ordinary spawn prompt spends sixteen
kilobytes to be told what this section already says.

When all you need is the return shape, read the one file rather than the skill around it:
`${CLAUDE_PLUGIN_ROOT}/skills/senior-prompt-engineer/references/agent-handoff-contracts.md`.

## §5 — Claude Code and Codex route the same, trigger differently

The intent is identical in both. The trigger model is not, and pretending otherwise is how a Codex
session silently does everything in one thread:

- **Claude Code** may delegate on its own. Agent descriptions, skill descriptions and hooks are the
  routing surface, and a task that matches the matrix gets its specialist without being asked.
- **Codex** spawns explicitly. A skill, command or prompt that expects parallel agents has to say so
  in words — "spawn one subagent per point, wait for all, consolidate" — because nothing there will
  infer it.
- **A hook may guide, log and validate the routing. A hook never spawns.** One that describes itself
  as spawning is describing something that did not happen.

## §6 — One thread per scope

Cloud threads and worktrees follow §3, one level up: one thread per task scope, and never two of them
editing the same files unless they are genuinely isolated and there is a written merge plan.

Keep network access off during the agent phase unless the task needs live external documentation;
install dependencies at setup time instead. Every thread reports the paths it changed, the commands
it ran and what it could not resolve — a result without those three is not a result, it is a claim.

## §7 — What the parent does with the answers

1. Check each return against the contract in §4. One that does not follow it gets re-asked, not
   guessed at.
2. Deduplicate by concrete claim, not by wording.
3. Sort by severity, then confidence, then impact.
4. Do not implement from a finding with confidence 2 or below unless it is marked `[ASSUMED]` and
   accepted as such out loud.
5. Run the smallest gate that means anything before reporting progress. `safety-floor.md § 7` is why:
   a consolidated report is still a completion claim.

The rules the shared columns imply — the severity scale, which tool wins when two agents disagree,
what a batch does with a member that never returned — are one file, not a skill: read
`${CLAUDE_PLUGIN_ROOT}/skills/senior-prompt-engineer/references/parallel-batch-contracts.md`.

## §8 — A name that does not resolve is a route, not a stop

A plugin cannot guarantee its agents are registered in the session that is running. When a spawn
fails to resolve, `030-agent-assignment-matrix.md` carries the two failure shapes, which of them is
the caller's defect and which is a hook's, and the fallback order. The part that belongs in a floor:
**the work still gets done, the route taken is stated in one line, and the name is not retried.**

A write-capable agent has no fallback. Standing in for one with a general agent discards the
disjoint-file ownership §3 depends on — when one of those does not resolve, stop and say so.
