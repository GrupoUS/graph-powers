---
name: harness-audit
description: "Audits a whole agent harness as a graph and proposes prioritised patches. Use when the question is about the WIRING between artefacts rather than the content of one of them: 'are my agents, skills and commands connected?', 'audit my harness', 'this skill fires at the wrong time', 'the subagent is not found', 'what part of .claude no longer earns its place?', before adding a new agent or skill, after a model upgrade, or at a periodic review. Covers frontmatter, dangling references, orphans, repo-versus-global name shadowing, trigger collision, hooks, workflows, and loop-engineering compliance. Report-only; never applies a patch without approval. Do NOT use it to create or rewrite ONE skill (that is `skill-creator`), to design ONE agent's prompt (that is `senior-prompt-engineer`), or to choose which agents to spawn for a task (that is `agent-orchestration`)."
user-invocable: true
argument-hint: "[path | --all | --phase N] — defaults to .claude/"
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
---

# Harness Audit — does this harness actually resolve to itself?

## Overview

Phases 0-4 gather evidence; Phase 5 hands the judgement to an isolated subagent
(`skill-improver`), because **whoever gathers does not judge**; Phase 6 synthesises and **stops**.

Default scope is the project's `.claude/`; `--all` includes `~/.claude/` (the repository wins on a
conflict). Marketplace plugins are reported, never edited.

What this skill does **not** do: write or rewrite a skill (`skill-creator`), design an agent's
prompt (`senior-prompt-engineer`), decide which agents to use for a task (`agent-orchestration`), or
review production code (`/pr-review`, `evaluator`).

## Hard rules

- **Report-only.** No patch is applied without the user's explicit approval in the turn. Writing is
  permitted in exactly three places: `.claude/audit/` (freely — those are scan artefacts), this
  skill's `learning.md`, and the auditor's memory file — the last two **only after approval in the
  turn**, and never with patch content, only the record of the round and the failure pattern. Every
  other file in the harness is approval territory, not this skill's.
- **`[HARD]`** Never `git commit` or `git push` on your own initiative — `safety-floor.md §1`.
- **`[HARD]`** A secret you find is never printed in the clear. Report `path:line` plus the kind,
  masked. A secret in the harness is P0 and ships in its own batch, before any other fix.
- An orphan is never deleted in this round. Classify it `DOCUMENT` / `DIRECT_INVOCATION_OK` /
  `REMOVAL_CANDIDATE` — the last needs double evidence and the user's decision.

## Phase 0 — Inventory

Enumerate `$1` (default `.claude/`). Per artefact: path, type, bytes, short hash, raw frontmatter.
Compare the count against `find <scope> -type f | wc -l` and **declare what was skipped**
(`__pycache__`, `logs/`, `agent-memory/`, `audit/`). → `.claude/audit/inventory.json`

**Before accusing anything of being missing, test the four silent resolvers:** `ls -la` for a
symlink · enterprise > personal > project precedence for a bare name · any alias map in the config
for a basename that differs from `name` · a grep for an importer, for hooks not declared in
`settings.json`.

## Phase 1 — Static validation

Reuse the gates that already exist; do not write a new validator:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/skill-creator/scripts/quick_validate.py <skill-path>
python3 -c "import json;json.load(open('.claude/settings.json'))"
```

Measure with `python3`, not by eye: `description` + `when_to_use` ≤ **1,536 characters**; any loop
prompt < **25,000 bytes**; each `agent-memory/*/MEMORY.md` under 200 lines and 25 KB. Capture every
gate's exit code as evidence. **A gate that fails a valid file is a finding (E3), not a reason to
skip the gate.** → `.claude/audit/static.json`

## Phase 2 — The wiring graph

Extract every edge with `path:line` at both ends: `subagent_type`, `Skill()`, a `skills:` preload,
`Agent({...})`, `Workflow({name})`, hook → script, command → rule, skill → `references/`. Classify
dangling (W2), orphans (W3) and cycles (W6).

Severity of a dangling edge comes from its call site: it executes (P0) > it is a live instruction
(P1) > it sits inside an illustrative code block (P3 — report, do not fix).
→ `.claude/audit/graph.json` plus `graph.mmd` (≤40 nodes, grouped by layer)

## Phase 3 — Shadowing and name collision

Cross the repository's `name` values against `~/.claude/skills/`, `~/.claude/agents/` and the
enabled plugins. Precedence is **enterprise > personal > project**: prove which file the listing
actually serves by comparing the two `description` values. A collision where the losing version is
the repository's authority is **P0**.

Check `enabledPlugins` at all three levels — a plugin that is installed but disabled makes every
`Skill("plugin:skill")` dangle at runtime.

## Phase 4 — Trigger collision

For each skill with overlapping territory, generate **at least 3 prompts that should fire and 3
that should not** — prioritise negatives on the border with the real competitor, not in distant
territory — and measure the hit rate in isolated, parallel subagents (one skill per subagent).

Save each response to `.claude/audit/eval-responses/resp-<case>.txt` and run the gate from the table
below, **case by case**. A false-positive rate above 20% → propose corrected `description` wording,
plus one new negative case carrying the exact phrase that collided.

This skill's own cases live in `evals/evals.json`: 3 positives and 4 negatives, of which the
`skill-creator` border is the narrowest ("my skill does not fire" = tuning one skill; "it fires at
the wrong time" = collision between N skills).

## Phase 5 — Independent judgement

You do **not** judge your own gathering. Dispatch the auditor with the inventory and graph attached:

```ts
Agent({
  subagent_type: "skill-improver",
  prompt: `TASK: audit <scope> against ../../references/rubrics/skill-improver-rubric.md.
EXPECTED OUTCOME: a PASS|NEEDS_WORK verdict plus P0-P3 findings with path:line, confidence and patch.
MANDATORY CONTEXT: inventory and graph in .claude/audit/*.json.
  <paste the FULL contents of the auditor's MEMORY.md here>
  — mandatory, not "if it exists": the agent does not declare \`memory:\` (that would grant
  Write/Edit), so this paste is the ONLY path by which accumulated failure patterns reach it.
  Skipping it makes the auditor repeat a mistake already catalogued.
MUST DO: reopen every edge on disk before confirming it dangles.
MUST NOT DO: write any file; touch application or package source.
RETURN FORMAT: the agent's own output contract, under 2000 tokens.
DO NOT REDO: the inventory — it is attached; contest it, do not rebuild it.`,
})
```

Under `--all`, findings about the auditor itself and about this skill come back marked
`SELF-AUDIT`: the severity is **not** lowered, and a P0 of its own fails like any other — the label
qualifies only a `PASS`, never a fail.

With the verdict in hand, write the default-FAIL contract: one criterion per rubric dimension, every
`passes: true` accompanied by the `path:line` the auditor cited, and every `passes: false` carrying
`gap` plus `minimal_fix`. → `.claude/audit/harness-contract.json`

## Phase 6 — Synthesis and stop

1. De-duplicate by root cause: one cause, N call sites.
2. `VERDICT`: **BLOCKS** | **ADJUST** | **APPROVES**.
3. Findings by severity, each with its minimal patch.
4. **Keep disagreements between your gathering and the auditor's verdict visible.** If it failed
   something you had as fine, the default is that it is right; if you have on-disk evidence against,
   show both and leave the decision to the user.
5. The three concrete next steps.
6. **STOP.** Apply nothing. Record the round in `learning.md`
   (hypothesis → change → measurement → verdict) with measured numbers, never estimates.

## Gates

No line enters this table without its exit code beside it. A documented gate that does not run is
worse than an absent one — it passes for verification already done.

| Gate | Command (complete, with every required argument) | Expected exit | Phase |
|---|---|---|---|
| Skill frontmatter | `python3 ${CLAUDE_PLUGIN_ROOT}/skills/skill-creator/scripts/quick_validate.py <skill-path>` | 0 | 1 |
| Settings/config JSON | `python3 -c "import json;json.load(open('.claude/settings.json'))"` | 0 | 1 |
| Trigger, **case by case** | `RESP_DIR=.claude/audit/eval-responses` (you write `resp-<case>.txt` there in Phase 4, one per case, capturing the response from a clean session), then:<br>`for c in <case ids>; do python3 ${CLAUDE_PLUGIN_ROOT}/skills/skill-creator/scripts/run_evals.py --skill-path ${CLAUDE_PLUGIN_ROOT}/skills/harness-audit --evals-path ${CLAUDE_PLUGIN_ROOT}/skills/harness-audit/evals/evals.json --response-file "$RESP_DIR/resp-$c.txt" --test-case "$c" --threshold 1.0; done` | 0 per case | 4 |
| Edges resolve | 100% resolve, or are marked `DANGLING` with a cause | — | 2 |
| Default-FAIL contract | `python3 -c "import json;d=json.load(open('.claude/audit/harness-contract.json'));assert not [c for c in d['criteria'] if c['passes'] and not c.get('evidence')]"` | 0 | 5 |

`--threshold 1.0` is required, and it is not decorative rigour: the runner's exit code is only
`pass_rate >= threshold` — each assertion's `critical` field **does not enter the exit code**, it is
a severity label in the report. With 2-4 assertions per case, the 0.95 default already demands 100%
in practice; passing `1.0` makes that explicit instead of accidental.

`"$RESP_DIR/resp-$c.txt"` needs the quotes and the directory: written as `<resp-$c.txt>` the shell
reads `<` as an input redirect and the loop dies before python ever runs.

**Never run the eval runner in default mode.** Without `--test-case` it flattens the assertions of
every case against a single response, so `contains: X` (positive) and `not_contains: X` (negative)
cancel out: a mathematical ceiling around 81%, measured at 75% with 4 critical failures even when
the behaviour was correct. The gate is only honest per case.

## Stopping and red flags

- Empty or partial scope → a degradation report saying what was missing, never a stack trace.
- Corrupt frontmatter → a finding with `path:line`, and the scan **continues**.
- The auditor disagreeing with the user across ≥2 rounds → the agent's prompt is the defect; fix it
  before another scan.
- A P0 finding with confidence ≤2 after two passes → `BLOCKED`, not `NEEDS_WORK`.
- More than ~15 subagents in one round → stop and report; an audit does not justify unbounded
  fan-out (the 2026-08-17 baseline round cost roughly 1.0M tokens with 8 agents).
- Never propose a fix in application or package source — out of scope, report it.

## Trigger calibration prompts

**Should fire:** "are my commands, skills and agents wired correctly?" · "audit `.claude` and tell
me what can improve" · "why does this skill fire at the wrong time?"

**Should not fire:** "create a skill for X" (→ `skill-creator`) · "my skill does not fire, how do I
make it fire?" (→ `skill-creator`; the narrowest border) · "improve the debugger agent's prompt"
(→ `senior-prompt-engineer`) · "refactor this component" (→ `/design`).

## References

- `../../references/rubrics/skill-improver-rubric.md` — the D/W/L/E/S/C rubric, the default-FAIL
  contract, and the auditor's own known failure patterns
- `../../agents/skill-improver.md` — the judge; primitives verified against primary sources
- `../../references/shared-context.md` — quality gates, verdict matrix, parallel spawn rules
- `learning.md` — this skill's round history

## Configuration

Reads `.graph-powers/config.json` at the start (`project.locale` for the report language,
`paths.rulesDir`, and any agent alias map). Writes only into `.claude/audit/`.
