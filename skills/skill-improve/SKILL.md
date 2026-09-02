---
name: skill-improve
description: "Use when authoring or iterating one skill, or when auditing how a whole harness is wired. Trigger on make a skill for X, improve this skill, my skill is not triggering, description tuning, the eval loop — and on are my agents, skills and commands connected, audit my harness, this skill fires at the wrong time, the subagent is not found, what part of .claude no longer earns its place. Proactively before adding an agent or skill and after a plugin or model upgrade. Designing one agent's prompt is senior-prompt-engineer; which agents to spawn is the execution floor."
user-invocable: true
argument-hint: "[skill-path | --all | --phase N] — a skill path picks Mode A, no argument audits .claude/ in Mode B"
---

# Skill Improve

> Derived from `skill-creator` in anthropics/skills (Apache-2.0, see `LICENSE.txt`). Modified by
> GrupoUS: the authoring loop and the harness-wiring audit were merged into one skill, because the
> border between them was measured and never closed. Changes are listed in the NOTICE file at the
> root of the plugin.

Two modes, one territory. Both answer "why is this skill not doing what I meant?" — one by looking
inside a skill, the other by looking at how skills resolve to each other.

| Mode | Question | Writes? | Detail |
|---|---|---|---|
| **A — Author** | What should this one skill say, and does it trigger? | Yes | `references/authoring.md` |
| **B — Audit** | Do the artefacts resolve to each other? | No | `references/harness-wiring-audit.md` |

## Before either mode

Read `learning.md` first, and `.claude/agent-memory/skill-improver/MEMORY.md` when the round will
reach Mode B Phase 5. Both are written at the *end* of a round and are worth nothing if the next
round does not open them — the inherited failure patterns exist to stop a mistake already
catalogued from being made again, and a pattern nobody loads prevents nothing.

`MEMORY.md` is also the one file Phase 5 orders pasted verbatim into the auditor's prompt. The
agent declares no `memory:` field, deliberately, because that would grant it `Write` and `Edit` on
top of its allowlist — so this paste is the only path by which accumulated patterns reach it.

## Which mode

**Mode A** when the subject is one artefact: creating a skill, restructuring a body, tuning a
description so it fires, writing the evals that prove a change helped. One name in the question.

**Mode B** when the subject is the link between artefacts: a subagent that is not found, a skill
that fires in the wrong situation because another one claims the same words, an orphan nobody
dispatches, a hook declared nowhere. Two or more names, or none — a question about the graph.

Ambiguous by design: *"my skill does not fire"* is Mode A when one description is weak, and Mode B
when two descriptions overlap. Start in A, and escalate to B the moment a second skill turns out to
claim the same territory. That border used to be two competing skills; merging them is what removed
the need to guess right on the first turn.

## Proactive lifecycle

This matrix is the one routing authority when an eligible event is observed. It selects a stage, not
an always-on observer; Mode B remains report-only.

| Stage observed before task close | Owner and timing | Minimum evidence | Explicit exclusion |
|---|---|---|---|
| Create a skill, or materially change one skill's body, description, reference or eval behaviour | **Mode A before the first draft/edit.** For a new skill, Mode A completes before any Mode B integration pass. | Intent plus RED for changed behaviour; focused case at `1.0`; `quick_validate.py` | Typo/prose-only repair with no rule, trigger or behaviour change |
| Register a newly authored skill or connect its command/agent/call sites | **Mode B after the Mode A candidate exists and before integration is accepted.** | Changed-edge baseline; caller → resolver → target evidence; report-only verdict | It does not rewrite the skill body that Mode A owns |
| Design or revise one agent prompt/body | **`senior-prompt-engineer` before drafting.** `skill-improve` does not fire. | Prompt-engineering acceptance evidence | Naming the artefact “agent” does not make prompt design Mode B |
| Register, remove or rename an agent, or change its harness call sites/model registration | **Mode B after a prompt candidate exists and before integration is accepted.** | Registration, call-site and generated-client edges; report-only verdict | No agent prompt/body edits |
| Plugin/model upgrade with observed or declared impact on discovery, tool contract, hook payload or model routing | **Mode B before accepting the upgraded wiring.** | Exact changed surface plus native/generated parity | Database, framework, application or package upgrade with no harness impact |
| Two materially similar misses of the same skill rule in current evidence | **Mode A regression before another prose tweak.** | Two named misses, one reproducing RED, then focused GREEN | One isolated application/product failure routes to its domain owner |
| Competing descriptions, shadowing, orphan/dangling edge, or a second claimant discovered during Mode A | **Escalate A → B once the second edge is evidenced.** | The competing claimant/edge; no speculative escalation | A weak description with no second claimant stays Mode A |
| Task boundary | **No new mode.** Report `<mode>: <deciding evidence>` only if a row above fired; otherwise say nothing about this lifecycle. | Trace/eval/wiring command that actually ran | Never invoke a skill merely to manufacture a close-out line |

Allowed lifecycle-event slugs are `skill-authoring`, `skill-wiring`, `agent-wiring`,
`harness-upgrade`, `repeated-skill-miss`, `trigger-collision`, and `proactive-routing`.

Not this skill: designing an agent's prompt — when the audit lands on an `agents/*.md` file rather
than a skill, hand it to `Skill("senior-prompt-engineer")`, which owns the file contract and the
handoff schema. Nor deciding which agents to run for a task (that is the always-in-force
`${CLAUDE_PLUGIN_ROOT}/references/execution-floor.md`), nor reviewing production code
(`/pr-review`, `graph-powers:evaluator`).

## Hard rules

- **Mode B is report-only.** No patch is applied without the user's explicit approval in the turn.
  Writing is permitted in `.claude/audit/` freely — those are scan artefacts — and in `learning.md`
  and the auditor's memory file **only after approval**, carrying the record of the round and the
  failure pattern, never patch content. Every other file in the harness is approval territory, not
  this skill's.
- **A skill cannot restrict its own tools.** `allowed-tools` is an additive pre-approval grant, not
  a restrictive allowlist, so Mode B's report-only promise is behavioural. What *enforces* it is the
  paired agent `graph-powers:skill-improver`, which declares `disallowedTools: Write, Edit`. Say
  this plainly rather than implying a sandbox that does not exist.
- **`[HARD]`** Never `git commit` or `git push` on your own initiative —
  `${CLAUDE_PLUGIN_ROOT}/references/safety-floor.md § 1`, which also covers checking out a protected
  branch, merging and rewriting history.
- **`[HARD]`** A secret you find is never printed in the clear. Report `path:line` plus the kind,
  masked. A secret in the harness is P0 and ships in its own batch, before any other fix.
- An orphan is never deleted in the round that found it. Classify it `DOCUMENT` /
  `DIRECT_INVOCATION_OK` / `REMOVAL_CANDIDATE`; the last needs double evidence and the user's
  decision.

## Measured constraints

These are enforced by scripts in this repository, not by convention. Ignoring one fails a build or,
worse, passes while measuring nothing.

| Constraint | Value | Enforced by |
|---|---|---|
| `description` alone | 1,024 characters | `scripts/quick_validate.py` — the only gate that runs on a skill authored outside the plugin |
| `description` plus `when_to_use`, per entry | 1,536 characters | `.github/check_listing_budget.py` |
| Same, summed over every skill and command | a shared ceiling | same file — your entry spends everyone's headroom |
| SKILL.md body | 500 **non-empty** lines | `scripts/quick_validate.py` |
| `name` | must equal the directory name | `scripts/quick_validate.py`, and CI separately |

Three validator behaviours that look like style advice and are not:

- `name` must be **unquoted**. Quotes are captured as part of the value and fail the hyphen-case check.
- `description` must be a **quoted single-line scalar**. Written as a folded block scalar it is
  captured literally and rejected by the angle-bracket check; written as a literal block it passes
  while the length check silently measures only the first line.
- Keep `<`, `>`, `[` and `]` out of the description text. The bracket check is a substring test, so
  a description that legitimately quotes CLI syntax fails.

## Gates

No line enters this table without having been pasted into a shell and run verbatim, **plus one run
it must fail**. Writing the expected exit code beside a command is not the gate; running both
directions is. That rule was adopted once in the weak form and violated three more times in the same
table — see `learning.md`.

| Gate | Command | Expected exit | Mode |
|---|---|---|---|
| Frontmatter and body size | `python3 ${CLAUDE_PLUGIN_ROOT}/skills/skill-improve/scripts/quick_validate.py <skill-path>` | 0 | A, B |
| Listing budget | `python3 ${CLAUDE_PLUGIN_ROOT}/.github/check_listing_budget.py` | 0 | A |
| Trigger, **one case per response** | either runner line below | 0 for the directory, or 0 per case | A, B |
| Settings and config JSON | `python3 -c "import json,pathlib;p=pathlib.Path('.claude/settings.json');print('SKIP: no .claude/settings.json') if not p.exists() else json.loads(p.read_text(encoding='utf-8'))"` | 0 — absent prints `SKIP`; 1 only on malformed JSON | B |
| Edges resolve | every edge resolves, or is marked `DANGLING` with a cause | — | B |

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/skill-improve/scripts/run_evals.py --skill-path <skill-path> --evals-path <skill-path>/evals/evals.json --response-dir <dir-with-resp-case-id-txt> --threshold 1.0
python3 ${CLAUDE_PLUGIN_ROOT}/skills/skill-improve/scripts/run_evals.py --skill-path <skill-path> --evals-path <skill-path>/evals/evals.json --response-file <captured-response>.txt --test-case <case-id> --threshold 1.0
```

The first line grades every case against its own `resp-<case-id>.txt` in one call and is the
gate; the second grades one case and is for iterating on a single assertion. Replace every
angle-bracket token before pasting: a placeholder left in place is read by the shell as an input
redirect, and the command dies before Python starts with an error about a file that is not the
response file. Five things about that runner, each measured rather than assumed:

1. **Never grade a multi-case file in default mode.** Without `--test-case` or `--response-dir` it
   flattens the assertions of every case against a single response, so `contains: X` on a positive
   case and `not_contains: X` on a negative one cancel out. The mathematical ceiling lands near 81%;
   a correct set of artefacts measured 75% with 4 critical failures (2026-08-17). The runner now
   says so on stderr, and the warning is not the gate: the exit code is still computed over the
   flattened set.
2. **`--threshold 1.0` is still the gate setting, and since Round 4 a failed `critical` assertion
   exits 1 at any threshold.** Before that the exit code was only `pass_rate >= threshold` and
   `critical` was a label in the printed report — at the 0.95 default a case could fail its one
   critical assertion out of twenty and stay green. Now `critical: true` fails the run and
   `critical: false` only counts toward the rate; pass `1.0` so the non-critical ones cannot hide
   either. A case with nothing machine-checkable fails too — a gate cannot pass on manual review.
3. **A missing response under `--response-dir` is a failed case, never a skipped one.** Measured:
   nine responses grade 9/9 and exit 0; the same directory with one file removed exits 1 and names
   the path. A loop that skipped what it could not find reported green over the cases it never ran.
4. **An unknown assertion id is an error naming the id, exit 1.** Until Round 4 it was filtered
   silently, so a case whose ids were mistyped ran zero assertions and scored 0.0 over an empty
   table — indistinguishable at a glance from a real failure.
5. **An assertion with no `check` key, or a check with no colon, is a failed row labelled
   `INVALID`,** not a traceback. Until Round 4 both crashed the runner, which reads as a broken gate
   rather than a broken assertion.

## Trigger calibration

This skill's own cases live in `evals/evals.json` — positives that must fire, negatives that must
route elsewhere. They are the calibration; do not restate them in prose here, or the two copies
drift and the prose wins by being read first.

## References

- `references/authoring.md` — Mode A in full: the seven steps, the description formula, the
  assertion-design rules
- `references/harness-wiring-audit.md` — Mode B in full: phases 0 to 6, the four silent resolvers,
  the independent-judgement dispatch
- `references/testing-skills.md` — RED-GREEN-REFACTOR and pressure scenarios, the source for
  discipline-enforcing skills
- `references/persuasion-principles.md` — when authority language is the mechanism rather than an
  anti-pattern
- `references/anthropic-best-practices-summary.md` — the condensed validation rubric
- `${CLAUDE_PLUGIN_ROOT}/references/rubrics/skill-improver-rubric.md` — the D/W/L/E/S/C rubric the
  paired agent scores against
- `${CLAUDE_PLUGIN_ROOT}/agents/skill-improver.md` — the judge for Mode B, read-only by declared
  field
- `learning.md` — round history and the inherited failure patterns
- `scripts/` — `init_skill.py` scaffolds, `package_skill.py` zips for distribution,
  `quick_validate.py` checks structure, `run_evals.py` grades assertions

## Configuration

Mode B reads `.graph-powers/config.json` at the start and falls back to defaults when it is
absent — the Configuration section of `references/harness-wiring-audit.md` names them. It writes
only into `.claude/audit/`.
