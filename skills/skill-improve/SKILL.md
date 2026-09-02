---
name: skill-improve
description: "Use when authoring or iterating one skill, or when auditing how a whole harness is wired. Trigger on make a skill for X, improve this skill, my skill is not triggering, description tuning, the eval loop — and on are my agents, skills and commands connected, audit my harness, this skill fires at the wrong time, the subagent is not found, what part of .claude no longer earns its place. Proactively for skill authoring; agent registration/call-site changes; and a plugin or model upgrade that impacts this harness. Agent-prompt drafting is senior-prompt-engineer; agent selection is the execution floor."
user-invocable: true
argument-hint: "[skill-path | --all | --phase N] — a skill path picks Mode A, no argument audits .claude/ in Mode B"
---

# Skill Improve

> Derived from `skill-creator` (Apache-2.0; `LICENSE.txt`). GrupoUS merged the measured authoring
> and wiring-audit boundary; NOTICE records modifications.

| Mode | Question | Writes? | Detail |
|---|---|---|---|
| **A — Author** | What should this one skill say, and does it trigger? | Yes | `references/authoring.md` |
| **B — Audit** | Do the artefacts resolve to each other? | No | `references/harness-wiring-audit.md` |

## Before either mode

Read `learning.md`; in Mode B Phase 5 read and paste
`.claude/agent-memory/skill-improver/MEMORY.md`, because `memory:` adds `Write` and `Edit`.

## Which mode

**Mode A** owns one skill's body, description or evals. **Mode B** owns links between artefacts:
missing registration, overlap, orphan or undeclared hook. A weak single description stays A; a
second evidenced claimant escalates A → B.

## Proactive lifecycle

**[HARD] Entry protocol.** For an owned row, the first user-visible line — the first non-empty line
of the final response — is `skill-improve Mode A — <slug>: RED <pending|established by evidence>` or
`skill-improve Mode B — <slug>: changed-edge baseline <pending|established by evidence>`. Repeat or prepend
it to the final response even if an earlier update emitted it. Put blocker/refusal, permission/tool observation,
clarification, plan, draft or edit after it, even when tools or Write permission are unavailable. Rows owned by
another skill emit neither; task-boundary evidence stays separate.

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

Agent prompts use `Skill("senior-prompt-engineer")`; agent selection uses the execution floor;
production-code review uses `/pr-review` or `graph-powers:evaluator`.

## Hard rules

- **Mode B is report-only.** No patch is applied without the user's explicit approval in the turn.
  Writing is permitted in `.claude/audit/` freely — those are scan artefacts — and in `learning.md`
  and the auditor's memory file **only after approval**, carrying the record of the round and the
  failure pattern, never patch content. Every other file in the harness is approval territory, not
  this skill's.
- **A skill cannot restrict its own tools.** `allowed-tools` is additive; the paired agent enforces
  Mode B with `disallowedTools: Write, Edit`.
- **`[HARD]`** Never `git commit` or `git push` on your own initiative —
  `${CLAUDE_PLUGIN_ROOT}/references/safety-floor.md § 1`, which also covers checking out a protected
  branch, merging and rewriting history.
- **`[HARD]`** A secret you find is never printed in the clear. Report `path:line` plus the kind,
  masked. A secret in the harness is P0 and ships in its own batch, before any other fix.
- An orphan is never deleted in the round that found it. Classify it `DOCUMENT` /
  `DIRECT_INVOCATION_OK` / `REMOVAL_CANDIDATE`; the last needs double evidence and the user's
  decision.

## Measured constraints

| Constraint | Limit | Enforced by |
|---|---|---|
| `description` | 1,024 alone; 1,536 with `when_to_use` | validator; listing budget |
| All entries | shared listing ceiling | listing budget |
| Body and `name` | 500 non-empty lines; directory match | validator and CI |

Validator edge cases and runner traps have one canonical home in `references/authoring.md`.

## Gates

Run every gate verbatim plus one direction it must fail; expected exit text is not evidence.

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

Directory gates; response-file iterates. Replace placeholders; edge cases are in
`references/authoring.md#validator-and-runner-edge-cases`.

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
