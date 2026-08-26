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

The scope is the skill's argument: a path, `--all` (the project plus the personal layer), or
nothing, which means `.claude/`. `--phase N` re-runs one phase against the artefacts a previous
round left in `.claude/audit/` instead of starting from the inventory — it exists so a Phase 4
re-measure after a description change does not cost a Phase 0 to 3 nobody asked for.

Enumerate the scope. Per artefact: path, type, bytes, short hash, raw frontmatter. Compare the count
against a full recursive file count of the scope —
`python3 -c "import pathlib,sys;print(sum(1 for p in pathlib.Path(sys.argv[1]).rglob('*') if p.is_file()))" .claude`
— and **declare what was skipped** (`__pycache__`, `logs/`, `agent-memory/`, `audit/`).
→ `.claude/audit/inventory.json`

Skipped for the *inventory* is not skipped for *reading*: `.claude/agent-memory/skill-improver/MEMORY.md`
is opened at the start of the round and pasted into the Phase 5 prompt. It is excluded from the
artefact count because it is round state, not an artefact.

On the first round in a repository that file does not exist, and that is not permission to drop the
paste: the Phase 5 prompt carries the literal line `MEMORY.md: absent — first round in this
repository` in its place, so the auditor knows it inherits nothing rather than wondering whether the
caller forgot. The file is created after that round's approval, from what the auditor returned under
`RECURRING PATTERN` — never before, because an empty file pasted verbatim proves nothing.

**Before accusing anything of being missing, test the four silent resolvers:**

1. A directory listing that shows symlinks, for a target that resolves elsewhere.
2. Enterprise > personal > project precedence, for a bare name.
3. Any alias map in the config, for a basename that differs from `name`. This plugin's schema
   declares no alias key today; a host's config or a routing hook may carry one. Read the schema
   before asserting either way — an assertion that names a key nothing reads is a phantom resolver.
4. A grep for an importer, for hooks not declared in `settings.json`. A hook can be dead in the
   settings and alive as a module.

Skipping this step is how a false P0 gets written. See `../learning.md`, inherited pattern 3.

## Phase 1 — Static validation

Reuse the gates that already exist; do not write a new validator. The commands are the Phase 1
rows of the Gates table at the end of this file — one home, not restated here.

Measure with `python3`, not by eye: `description` plus `when_to_use` within the listing entry cap
(see the SKILL.md body for the measured number); any loop prompt under 25,000 bytes; each
`agent-memory/*/MEMORY.md` under 200 lines and 25 KB. Capture every gate's exit code as evidence.
**A gate that fails a valid file is a finding (rubric E3), not a reason to skip the gate.**
→ `.claude/audit/static.json`

## Phase 2 — The wiring graph

Extract every edge with `path:line` at both ends: `subagent_type`, `Skill()`, a `skills:` preload,
`Agent({...})`, `Workflow({name})`, hook to script, command to rule, skill to `references/`.
Classify dangling edges (W2), orphans (W3) and cycles (W6), and write the rubric code beside every
finding: the Phase 5 contract has one criterion per rubric dimension, and a finding with no code has
no row to land in.

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

**Every layer that serves a listing, not only the personal one.** Four harnesses read one source
(this plugin's cardinal 7), and each has its own skills directory: `~/.claude/skills/` for Claude
Code, `~/.agents/skills/` for Codex and for any tool that follows the agents-skills convention, plus
whatever an installer or marketplace clones (`~/.claude/plugins/cache/<plugin>/<version>/`,
`~/.codex/.tmp/marketplaces/<plugin>/`). Cross the repository's names against all of them, then
cross the copies against each other: a symlink from one layer into another is one file served under
two precedences, and a clone pinned to an older plugin version serves what the repository has already
moved past. Report the version of each copy beside its path — byte-identical today is a measurement,
not a guarantee.

**Ancestors of a merged or renamed skill.** When `learning.md`, `CHANGELOG.md` or `NOTICE` records
that a skill was merged into another or renamed, the retired names are the first place a collision
hides: an installer that once copied the old skill into the personal layer never removes it, so the
pre-merge skill keeps its full description in every listing beside the skill that replaced it —
three descriptions claiming the same phrases, which is Phase 4's collision with the answer already
known. Grep every layer above for each retired name. A hit is an orphan of the personal layer:
classify it `REMOVAL_CANDIDATE` with the two pieces of evidence the rule demands — no call site
anywhere in the global config, hooks or skills, and a successor that carries a strict superset (cite
the round that measured it) — and leave the removal to the user as global scope outside the
repository, which the rubric labels `ESCOPO GLOBAL — fora do repo`. Never unlink it yourself, even
when both proofs are on the table.

## Phase 4 — Trigger collision

For each skill with overlapping territory, generate **at least 3 prompts that should fire and 3
that should not** — prioritise negatives on the border with the real competitor, not in distant
territory — and measure the hit rate in isolated, parallel subagents, one skill per subagent.

Say where each response came from, because the two sources measure different things: a clean
session (`claude -p` with the skill in the listing and the prompt as typed) measures the live
listing; an isolated subagent handed the listing and the prompt measures routing among the entries
it was given, and every round so far has had to write that caveat. Save each response to
`.claude/audit/eval-responses/resp-<case-id>.txt` and grade the directory in one call with the
runner's `--response-dir` mode: one case against its own response, one line per case, a missing
response counted as a failed case, exit 0 only when every case reaches the threshold. That is the
per-case discipline of `--test-case` without a shell loop around it, which is what keeps the gate
portable. A false-positive rate above 20% means the `description` is the defect: propose corrected
wording, plus one new negative case carrying the exact phrase that collided.

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
MANDATORY CONTEXT: .claude/audit/inventory.json, static.json and graph.json are on disk — open them; nothing is pasted except the memory below.
  <paste the FULL contents of .claude/agent-memory/skill-improver/MEMORY.md here; on a first
  round, the literal line: MEMORY.md: absent — first round in this repository>
  — mandatory, not "if it exists": the agent does not declare \`memory:\` (that would grant
  Write/Edit), so this paste is the ONLY path by which accumulated failure patterns reach it.
  Skipping it makes the auditor repeat a mistake already catalogued.
MUST DO: reopen every edge on disk before confirming it dangles.
MUST NOT DO: write any file; touch application or package source.
RETURN FORMAT: the agent's own output contract, under 2000 tokens.
DO NOT REDO: the inventory — it is on disk; contest it, do not rebuild it.`,
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
3. Findings by severity, each with its rubric code and its minimal patch.
4. The picture: `graph.mmd`, at most 40 nodes, in the report. The JSON is for the judge; the
   diagram is for the reader, and a file nobody renders is an artefact nothing consumes.
5. **Scope limits, stated.** Name every layer the scope did not cover — the personal layer under
   the default scope, a disabled plugin, a marketplace clone — so a clean verdict is read as clean
   *within scope*, not as clean.
6. **Keep disagreements between your gathering and the auditor's verdict visible.** If it failed
   something you had as fine, the default is that it is right; if you have on-disk evidence against,
   show both and leave the decision to the user.
7. The three concrete next steps.
8. **STOP.** Apply nothing. Record the round in the host project's `.claude/audit/learning.md`
   (hypothesis, change, measurement, verdict) with measured numbers, never estimates. The plugin's
   own `../learning.md` is written only when the round changed *this skill*: it ships inside the
   plugin and is overwritten by the next update, so a host project's audit history written there
   is lost on the next install. Anything the auditor returned under `RECURRING PATTERN` goes into
   `.claude/agent-memory/skill-improver/MEMORY.md`, after approval — you are the only possible
   writer, because the agent has no `Write` tool. Keep that file under 200 lines and 25 KB; past
   those limits the injection truncates and the oldest patterns fall off silently.

## Gates for Mode B

No line enters this table without having been pasted into a shell and run verbatim, plus one run it
must fail. See `../learning.md`, inherited pattern 1 — writing the expected exit code is not the
gate.

The command text lives in the SKILL.md Gates table — one home — except the contract gate, which is
Mode B's alone. This table adds the phase each gate closes and the direction it must fail in.

| Gate | Command | Must exit 0 on | Must exit 1 on | Phase |
|---|---|---|---|---|
| Skill frontmatter | SKILL.md row *Frontmatter and body size* | every skill in scope | a description with `: ` left unquoted | 1 |
| Settings/config JSON | SKILL.md row *Settings and config JSON* | a valid file, **and an absent one** — a project with no settings is a fact to report, not a traceback | a malformed file | 1 |
| Edges resolve | none — every edge resolves, or is marked `DANGLING` with a cause | — | — | 2 |
| Trigger, one case per response | SKILL.md row *Trigger*, the `--response-dir` line, over `.claude/audit/eval-responses` | every case | any one response file removed | 4 |
| Default-FAIL contract | `python3 -c "import json;d=json.load(open('.claude/audit/harness-contract.json'));assert not [c for c in d['criteria'] if c['passes'] and not c.get('evidence')]"` | a contract whose every `passes: true` cites evidence | one `passes: true` with no `evidence` | 5 |

The settings gate used to be `json.load(open('.claude/settings.json'))` with expected exit 0, and
exited 1 with a `FileNotFoundError` in the very repository that ships it, which has no such file.
Measured in Round 4, in all three directions: absent prints `SKIP` and exits 0, valid exits 0,
malformed raises `JSONDecodeError` and exits 1.

## Stopping and red flags

- Empty or partial scope → a degradation report saying what was missing, never a stack trace.
- Corrupt frontmatter → a finding with `path:line`, and the scan **continues**.
- The auditor disagreeing with the user across two or more rounds → the agent's prompt is the
  defect; fix it before another scan.
- A P0 finding with confidence at or below 2 after two passes → `BLOCKED`, not `NEEDS_WORK`.
- More than roughly 15 subagents in one round → stop and report. An audit does not justify unbounded
  fan-out; a full baseline round was measured at roughly 1.0M tokens with 8 agents (2026-08-17),
  and a five-lens review with eight refuters at 1.06M tokens with 13 (2026-08-26).
- Never propose a fix in application or package source — out of scope, report it.

## References

- `${CLAUDE_PLUGIN_ROOT}/references/rubrics/skill-improver-rubric.md` — the D/W/L/E/S/C rubric, the
  default-FAIL contract, and the auditor's own known failure patterns
- `${CLAUDE_PLUGIN_ROOT}/agents/skill-improver.md` — the judge; primitives verified against primary
  sources
- `${CLAUDE_PLUGIN_ROOT}/references/shared/010-quality-gates.md`,
  `${CLAUDE_PLUGIN_ROOT}/references/shared/090-verdict-matrix.md`,
  `${CLAUDE_PLUGIN_ROOT}/references/shared/070-parallel-agent-spawn.md` — the three the audit scores
  against
- `${CLAUDE_PLUGIN_ROOT}/references/shared/110-guardrails-index.md` — which guardrails deny in code
  and which are convention. An audit that treats a rule file as enforcement reports coverage that
  does not exist
- `../learning.md` — this skill's round history and inherited failure patterns

## Configuration

Reads `.graph-powers/config.json` at the start: `project.locale` for the report language,
`paths.rulesDir`, and any agent alias map. When the file is absent the round still runs (cardinal
3, fail-open): locale `en-US`, rules under `.claude/rules`, no alias map — and the report says the
config was absent, because an audit that silently assumed defaults would certify a project that has
never been set up. Writes only into `.claude/audit/`.
