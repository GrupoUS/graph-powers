# Harness wiring audit — does this harness resolve to itself?

Mode B of `skill-improve`, in full. The SKILL.md body carries the routing and the hard rules; this
file carries the phases. Read it when the question is about the **link between artefacts**, not the
content of one of them.

Phases 0-4 gather evidence. Phase 5 hands the judgement to an isolated subagent
(`graph-powers:skill-improver`), because **whoever gathers does not judge**. Phase 6 synthesises and
**stops**.

Default scope is the project's `.claude/`; `--all` includes `~/.claude/` too, and the repository
wins on a conflict. Marketplace plugins are reported, never edited.

## Phase 0 — Inventory

Enumerate the scope (default `.claude/`). Per artefact: path, type, bytes, short hash, raw
frontmatter. Compare the count against a full recursive file count of the scope and **declare what
was skipped** (`__pycache__`, `logs/`, `agent-memory/`, `audit/`). → `.claude/audit/inventory.json`

Skipped for the *inventory* is not skipped for *reading*: `.claude/agent-memory/skill-improver/MEMORY.md`
is opened at the start of the round and pasted into the Phase 5 prompt. It is excluded from the
artefact count because it is round state, not an artefact.

**Before accusing anything of being missing, test the four silent resolvers:**

1. A directory listing that shows symlinks, for a target that resolves elsewhere.
2. Enterprise > personal > project precedence, for a bare name.
3. Any alias map in the config, for a basename that differs from `name`.
4. A grep for an importer, for hooks not declared in `settings.json`. A hook can be dead in the
   settings and alive as a module.

Skipping this step is how a false P0 gets written. See `../learning.md`, inherited pattern 3.

## Phase 1 — Static validation

Reuse the gates that already exist; do not write a new validator:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/skill-improve/scripts/quick_validate.py <skill-path>
python3 -c "import json;json.load(open('.claude/settings.json'))"
```

Measure with `python3`, not by eye: `description` plus `when_to_use` within the listing entry cap
(see the SKILL.md body for the measured number); any loop prompt under 25,000 bytes; each
`agent-memory/*/MEMORY.md` under 200 lines and 25 KB. Capture every gate's exit code as evidence.
**A gate that fails a valid file is a finding, not a reason to skip the gate.**
→ `.claude/audit/static.json`

## Phase 2 — The wiring graph

Extract every edge with `path:line` at both ends: `subagent_type`, `Skill()`, a `skills:` preload,
`Agent({...})`, `Workflow({name})`, hook to script, command to rule, skill to `references/`.
Classify dangling edges, orphans and cycles.

Severity of a dangling edge comes from its call site: it executes (P0) beats it is a live
instruction (P1) beats it sits inside an illustrative code block (P3 — report, do not fix).

An orphan is never deleted in this round. Classify it `DOCUMENT` / `DIRECT_INVOCATION_OK` /
`REMOVAL_CANDIDATE` — the last needs double evidence and the user's decision.

→ `.claude/audit/graph.json` plus `graph.mmd`, at most 40 nodes, grouped by layer

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
territory — and measure the hit rate in isolated, parallel subagents, one skill per subagent.

Save each response to `.claude/audit/eval-responses/resp-<case>.txt` and run the trigger gate
**case by case**. A false-positive rate above 20% means the `description` is the defect: propose
corrected wording, plus one new negative case carrying the exact phrase that collided.

This is the collision-detection sibling of Mode A's description tuning. Mode A tunes one
description against near-misses; this phase finds which descriptions overlap in the first place.

## Phase 5 — Independent judgement

You do **not** judge your own gathering. Dispatch the auditor with the inventory and graph attached.

Note the escaped backticks in the prompt below and keep them. An audit prompt is prose about
frontmatter fields, so it is dense with backticks, and the prompt is a template literal — one
unescaped backtick ends the literal and the call fails at parse. If you fan this phase out through
a hand-written `Workflow({ script })` instead of `Agent()`, read
`${CLAUDE_PLUGIN_ROOT}/references/shared/130-workflow-authoring.md` and check the script before
running it; there the same mistake costs the whole script rather than one spawn.

```ts
Agent({
  subagent_type: "graph-powers:skill-improver",
  prompt: `TASK: audit <scope> against the D/W/L/E/S/C rubric.
EXPECTED OUTCOME: a PASS|NEEDS_WORK verdict plus P0-P3 findings with path:line, confidence and patch.
MANDATORY CONTEXT: inventory and graph in .claude/audit/*.json.
  <paste the FULL contents of .claude/agent-memory/skill-improver/MEMORY.md here>
  — mandatory, not "if it exists": the agent does not declare \`memory:\` (that would grant
  Write/Edit), so this paste is the ONLY path by which accumulated failure patterns reach it.
  Skipping it makes the auditor repeat a mistake already catalogued.
MUST DO: reopen every edge on disk before confirming it dangles.
MUST NOT DO: write any file; touch application or package source.
RETURN FORMAT: the agent's own output contract, under 2000 tokens.
DO NOT REDO: the inventory — it is attached; contest it, do not rebuild it.`,
})
```

The rubric the agent scores against is `../../../references/rubrics/skill-improver-rubric.md`. The
agent loads it itself; the prompt names the dimensions, not the path, so a moved rubric breaks one
file instead of two.

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
6. **STOP.** Apply nothing. Record the round in `../learning.md`
   (hypothesis, change, measurement, verdict) with measured numbers, never estimates. Anything the
   auditor returned under `RECURRING PATTERN` goes into
   `.claude/agent-memory/skill-improver/MEMORY.md`, after approval — you are the only possible
   writer, because the agent has no `Write` tool. Keep that file under 200 lines and 25 KB; past
   those limits the injection truncates and the oldest patterns fall off silently.

## Gates for Mode B

No line enters this table without having been pasted into a shell and run verbatim, plus one run it
must fail. See `../learning.md`, inherited pattern 1 — writing the expected exit code is not the
gate.

| Gate | Command, with every required argument | Expected exit | Phase |
|---|---|---|---|
| Skill frontmatter | `python3 ${CLAUDE_PLUGIN_ROOT}/skills/skill-improve/scripts/quick_validate.py <skill-path>` | 0 | 1 |
| Settings/config JSON | `python3 -c "import json;json.load(open('.claude/settings.json'))"` | 0 | 1 |
| Trigger, **case by case** | the runner line from the SKILL.md body, one invocation per case id, reading the responses captured in Phase 4 | 0 per case | 4 |
| Edges resolve | every edge resolves, or is marked `DANGLING` with a cause | — | 2 |
| Default-FAIL contract | `python3 -c "import json;d=json.load(open('.claude/audit/harness-contract.json'));assert not [c for c in d['criteria'] if c['passes'] and not c.get('evidence')]"` | 0 | 5 |

## Stopping and red flags

- Empty or partial scope → a degradation report saying what was missing, never a stack trace.
- Corrupt frontmatter → a finding with `path:line`, and the scan **continues**.
- The auditor disagreeing with the user across two or more rounds → the agent's prompt is the
  defect; fix it before another scan.
- A P0 finding with confidence at or below 2 after two passes → `BLOCKED`, not `NEEDS_WORK`.
- More than roughly 15 subagents in one round → stop and report. An audit does not justify unbounded
  fan-out; a full baseline round has been measured at roughly 1.0M tokens with 8 agents.
- Never propose a fix in application or package source — out of scope, report it.

## References

- `../../../references/rubrics/skill-improver-rubric.md` — the D/W/L/E/S/C rubric, the default-FAIL
  contract, and the auditor's own known failure patterns
- `../../../agents/skill-improver.md` — the judge; primitives verified against primary sources
- `../../../references/shared/010-quality-gates.md`,
  `../../../references/shared/090-verdict-matrix.md`,
  `../../../references/shared/070-parallel-agent-spawn.md` — the three the audit scores against
- `../../../references/shared/110-guardrails-index.md` — which guardrails deny in code and which are
  convention. An audit that treats a rule file as enforcement reports coverage that does not exist
- `../learning.md` — this skill's round history and inherited failure patterns

## Configuration

Reads `.graph-powers/config.json` at the start: `project.locale` for the report language,
`paths.rulesDir`, and any agent alias map. Writes only into `.claude/audit/`.
