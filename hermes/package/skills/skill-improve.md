---
name: skill-improve
description: "Use when authoring or iterating one skill, or when auditing how a whole harness is wired. Trigger on make a skill for X, improve this skill, my skill is not triggering, description tuning, the eval loop — and on are my agents, skills and commands connected, audit my harness, this skill fires at the wrong time, the subagent is not found, what part of .claude no longer earns its place. Proactively for skill authoring; agent registration/call-site changes; and a plugin or model upgrade that impacts this harness. Agent-prompt drafting is senior-prompt-engineer; agent selection is the execution floor."
user-invocable: true
argument-hint: "[skill-path | --all | --phase N] — a skill path picks Mode A, no argument audits .claude/ in Mode B"
---

> Hermes: first load `skill_view("graph-powers:graph-engineering")` for native calls and host-policy limits. `content/` paths are `file_path` values relative to the common registered-document parent. Source tools/model frontmatter is not host enforcement.

# Skill Improve

## Proactive lifecycle

For a material skill change use Mode A; for registration, call-site, shadowing, or impacted
harness wiring use Mode B. Report only the deciding evidence at close. This is a routing bridge,
not a required response prefix or an automatic audit.

| Mode | Owns | Method | Stop |
|---|---|---|---|
| A — Author | one skill body, description, reference or its eval | `content/skills/skill-improve/references/authoring.md` | focused proof is sufficient |
| B — Audit | wiring, registration, shadowing or changed integration edge | `content/skills/skill-improve/references/harness-wiring-audit.md` | report-only verdict |

Use A for one weak description; escalate A → B only with an evidenced second claimant or edge. Use
`senior-prompt-engineer` for an agent prompt/body. A harness-impacting plugin/model upgrade needs B;
an ordinary package or product failure does not. Two similar observed misses require a focused A
regression before another wording tweak.

Start from the changed edge and existing evidence. Do not read `content/skills/skill-improve/learning.md` unless the current
failure matches a named past pattern, and do not run a full inventory, isolated judge, or broad eval
set unless `--all`, a collision, or evidence makes it necessary. Mode A validates the changed skill
with `content/skills/skill-improve/scripts/quick_validate.py` and a focused case when behaviour changes. Mode B traces caller → resolver
→ target, reports uncertainty, and checks only affected registration/parity edges. Comprehensive
audits remain available on explicit request or observed collision.

Mode B never patches. Never delete an orphan in its discovery round: classify it `DOCUMENT`,
`DIRECT_INVOCATION_OK`, or `REMOVAL_CANDIDATE` and leave removal to the user. Keep secrets masked
and never commit or push autonomously.

Run the smallest relevant gate and report actual output. `content/skills/skill-improve/scripts/run_evals.py` is honest only per case
(`--test-case`) or one response file per case (`--response-dir`) with `--threshold 1.0`; details,
including validator/runner traps, are in `content/skills/skill-improve/references/authoring.md#validator-and-runner-edge-cases`.
Read `content/skills/skill-improve/references/testing-skills.md` only when a process rule needs RED/GREEN, and the other
references only for their named subject. The read-only Mode B judge is
`content/agents/skill-improver.md`.
