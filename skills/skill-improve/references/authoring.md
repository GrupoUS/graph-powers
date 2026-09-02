# Authoring and iterating one skill

Mode A of `skill-improve`, in full. Seven steps, in order. The SKILL.md body carries the routing
and the measured constraints; this file carries the method.

The loop is `Capture intent → Draft → Test → Evaluate → Improve → Repeat`. Do not skip to writing:
understand intent first, test after writing, and improve on evidence rather than intuition.

## About skills

### Skill types

| Type | What it is | Example |
|---|---|---|
| **Technique** | A concrete method with steps | condition-based waiting |
| **Pattern** | A way of thinking about a problem | flatten with flags |
| **Reference** | API surface, syntax, schemas | office docs, pptx API |
| **Discipline** | Rules that enforce compliance under pressure | TDD enforcement |

Classify early — the type determines the testing strategy in Step 5, and it is the one decision
that changes every later step.

### Anatomy

```
skill-name/
  SKILL.md        required — frontmatter plus body
  scripts/        optional — deterministic code, runs without entering context
  references/     optional — loaded on demand
  assets/         optional — templates and output files
  evals/          evals.json, the trigger and behaviour cases
  learning.md     the round history, for any skill in regular use
```

## Step 1 — Capture intent

Extract answers from the current conversation first: tools used, the sequence of steps,
corrections the user made, input and output formats. Then ask what the conversation did not answer:

1. What should this skill enable the agent to do?
2. When should it trigger — what phrases, contexts, symptoms?
3. What is the expected output format?
4. Should we set up test cases? Skills with objectively verifiable outputs benefit most.

Ask one question at a time and wait for confirmation before drafting.

## Step 2 — Plan and research

For each concrete use case:

1. Think through executing it from scratch.
2. Identify what scripts, references or assets would help when the work repeats.
3. Choose a file organisation pattern.

| Pattern | Structure | When to use |
|---|---|---|
| **Self-contained** | `SKILL.md` only | All content fits inline, no heavy reference |
| **With reusable tool** | plus `scripts/` | Code gets rewritten on every run |
| **With heavy reference** | plus `references/` and `scripts/` | Reference material over 100 lines |

Research before writing: check the available MCP servers — Tavily for best practices, Context7 for
library docs — and run subagents in parallel where the harness offers them.

## Step 3 — Initialize

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/skill-improve/scripts/init_skill.py <skill-name> --path <output-dir>
```

Creates the directory with a SKILL.md template and example resource directories. Customise or
delete what it generates; the example files are scaffolding, not a requirement.

## Step 4 — Write the skill

### The description field

The description is the **primary triggering mechanism**. Agents decide whether to load a skill on
this field alone.

Key principle: the description states *when to use*, meaning conditions and symptoms. It is not a
workflow summary — an agent that can read the workflow in the description will skip the body.

```yaml
# BAD: summarises the workflow, so the agent reads this instead of the skill
description: Skill for TDD — write test first, watch it fail, write minimal code

# BAD: too vague, does not match anything a user actually types
description: Helps with testing

# GOOD: specific conditions and symptoms, phrased the way users phrase them — and quoted
description: "Use when implementing any feature or bugfix, before writing implementation code. Trigger on write tests, add feature, fix bug, implement X."
```

**Make descriptions slightly pushy.** Agents undertrigger — they skip skills that would have
helped. Include synonyms, related terms and explicit trigger phrases. Instead of "for dashboard
creation", write "for dashboard creation — also trigger when the user mentions data visualisation,
internal metrics, or wants to display any kind of company data, even without saying dashboard."

Formula: `Use when [specific symptoms and contexts]. Trigger on: [phrases users actually type].`

**Two caps, two quantities.** `description` alone stays under **1,024 characters** — that is what
`quick_validate.py` holds it to, and the validator is the only gate that runs on a skill authored
outside the plugin. `description` plus `when_to_use` combined stays under **1,536 characters**,
enforced by `${CLAUDE_PLUGIN_ROOT}/.github/check_listing_budget.py`. That second budget is shared
across every skill and command in the plugin, so a long description spends headroom that belongs to
everyone.

Two frontmatter constraints that come from the validator rather than from taste, and that fail
silently if ignored:

- `name` must be **unquoted**. `quick_validate.py` captures the quotes as part of the value and
  fails the `^[a-z0-9-]+$` check.
- `description` must be a **quoted single-line scalar**. A folded block scalar written as `>-` is
  captured literally and rejected by the angle-bracket check, and a literal block written with a
  pipe passes while defeating the length measurement entirely — the validator only ever sees the
  first line. Keep `<`, `>`, `[` and `]` out of the text.

### Body structure

```markdown
---
name: skill-name
description: "Use when the conditions hold and the symptoms appear. Trigger on: the phrases users actually type."
---

# Skill Name

## Overview
Core principle in one or two sentences.

## When to Use
Symptoms and use cases, including "When NOT to use".

## Core Pattern
Before and after, for techniques and patterns.

## Quick Reference
Table or bullets for common operations.

## Implementation
Inline for simple patterns; a pointer to a file for heavy reference.

## Common Mistakes
What goes wrong, and the fix.
```

### Token efficiency

The context window is shared. Every line of a SKILL.md body competes with conversation history.

- Target a body under 500 non-empty lines. That is what the validator counts — a 900-line file that
  is half blank passes, which makes the number weaker than it looks. Aim well under it.
- Move detail to `references/`. A command that loads a skill is charged the SKILL.md bytes and not
  the references, so this is a real budget difference, not a stylistic one.
- Cross-reference rather than duplicate.
- One excellent example beats three mediocre ones.
- Challenge each paragraph: does the agent need this, or is it common knowledge?

### Progressive disclosure

| Level | Content | Budget |
|---|---|---|
| 1 — metadata | `name` and `description` | roughly 100 words, always loaded |
| 2 — body | Core instructions | under 500 non-empty lines, loaded on trigger |
| 3 — bundled resources | Scripts, references, assets | unlimited, loaded on demand |

Point at bundled resources explicitly, and say when to read them. A reference nothing points at is
an orphan.

### Writing style

- Imperative: "Validate input before calling the API", not "You should validate".
- Explain the *why*, not only the rule. Agents follow reasoning further than commandments, and
  reasoning covers edge cases the rule did not anticipate.
- Mark a genuinely non-negotiable rule `[HARD]` and give the reason beside it. Reaching for ALL CAPS
  is a signal that the reasoning is missing. The exception is a discipline skill under adversarial
  pressure, where authority language is the mechanism — `persuasion-principles.md` covers when that
  applies.
- Do not put the same content in both the body and a reference.

## Step 5 — Test and evaluate

Test before deploying. Always, including reference skills.

### Lifecycle-triggered evidence

When the `skill-authoring`, `repeated-skill-miss`, `trigger-collision`, or `proactive-routing`
lifecycle event applies, establish lifecycle RED before changing behaviour, then retain the focused
GREEN evidence. Two materially similar misses of the same rule are the threshold for a regression;
one isolated application/product failure belongs to its domain owner.

Unprimed trials preserve the user prompt byte-for-byte, run in a fresh temporary project with no
prior transcript or local rule, and record the selected owner plus load/skip trace. Reject prompts
that name this skill, Mode A, Mode B, a skill-load instruction, evals, or probes. A missing CLI,
authentication failure, timeout, non-zero child exit, malformed/incomplete stream, missing response,
or wrong required owner is failed evidence, never a skipped success.

Structured follow-ups are append-only: create `**Follow-up `R<round>-F<ordinal>` — OPEN:**`, name
the literal applicable path or one of `skill-authoring`, `skill-wiring`, `agent-wiring`,
`harness-upgrade`, `repeated-skill-miss`, `trigger-collision`, or `proactive-routing`, and later
append a dated `CLOSED`, `DEFERRED`, or reactivated `OPEN` disposition. Close only with the named
command or trace; legacy “Next round should measure” prose is not a follow-up.

### 5a. Write the cases

Three different purposes need three different sample sizes. Collapsing them into one number loses
the distinction that makes each worth running:

| Purpose | Sample | Measures |
|---|---|---|
| Behaviour | 2-3 realistic prompts | Does the skill produce the right output? |
| Trigger collision | at least 3 positive and 3 negative | Does it fire when it should, and stay quiet otherwise? |
| Description tuning | roughly 20 mixed queries | Does the wording discriminate at the margin? |

Save to `evals/evals.json`, in the shape the bundled runner reads:

```json
{
  "skill_name": "example-skill",
  "evals": [
    {
      "id": "pos-realistic-task",
      "polarity": "positive",
      "prompt": "The prompt a real user would type",
      "expected_output": "What success looks like",
      "assertions": [
        { "id": "A01", "description": "Output contains X", "check": "contains: X", "critical": true }
      ]
    }
  ]
}
```

Negative cases are worth most **at the border with the real competitor**, not in distant territory.
A negative case against something nobody would confuse proves nothing.

Share the cases with the user for review before running them.

### 5b. Run with-skill against baseline

Run the with-skill case once. Baseline only the smallest discriminating sample: at least one
representative positive and one nearest-boundary negative, plus any case whose assertion or trigger
changed in this iteration. Reuse a valid prior baseline for unchanged cases and record its source;
do not spawn a second agent for every case merely to recreate the same control.

Launch the selected with-skill and baseline cases in bounded waves, consolidating cases that share
one skill/listing into the same evaluation package when isolation is not the variable under test.
Count every run against `graphGuardrails.maxSpawnsPerWorkflow`, reserve the final
`graph-powers:skill-improver` verdict, and checkpoint remaining cases instead of opening another
workflow. Parallelism improves wall-clock only inside that total; it is not permission to double the
entire suite.

### 5c. Draft assertions while the runs complete

Good assertions are objectively verifiable, discriminating — they would fail without the skill —
and named so a reader knows what each one checks.

Four assertion-design rules, each learned by measurement rather than by reasoning:

1. **A short token needs a word boundary.** `contains: ls` matches inside "skills", "aliases" and
   "false", so it fires on responses that contain no `ls` at all. Use a regex with `\b`.
2. **Fixing that with a narrower pattern can invert the error.** A regex written as `ls -` misses
   the real report, which writes `ls .claude/skills/...` with no flag. Test both directions:
   samples that must match, and samples that must not.
3. **Express a prohibition as a positive check of the desired behaviour.** `not_contains: "patch
   applied"` fails the *correct* report, because "no patch applied" contains the forbidden string.
4. **A regex over prose needs `(?i)`.** Responses capitalise sentence-initially and `re.search` is
   case-sensitive.

Skip quantitative assertions for subjective skills — writing style, design quality — and do
qualitative review instead.

### 5d. Review results

1. Run the grader, per case. The exact command and its traps are in the SKILL.md body.
2. Show the user the outputs side by side for qualitative review.
3. Capture specific complaints per case.

For discipline-enforcing skills, `testing-skills.md` carries the full RED-GREEN-REFACTOR pressure
methodology. That file is the source for pressure testing — this step does not restate it.

## Step 6 — Improve and iterate

Improve on evidence, not intuition.

1. **Generalise from feedback.** The skill runs across many prompts, not only the test cases.
   Address the underlying pattern rather than the specific example.
2. **Keep it lean.** Read the transcripts. If the skill sends the agent on unproductive detours,
   cut the lines causing that.
3. **Explain the why.** Replace "always do X" with "do X because Y — without it, Z breaks".
4. **Bundle repeated work.** If several runs independently wrote the same helper, it belongs in
   `scripts/`.

Then rerun every case into `iteration-N+1/`, baselines included, and review with the user. Stop when
the user is satisfied, the feedback comes back empty, or progress has stalled.

## Step 7 — Optimise the description

After the body is stable, tune the description for triggering accuracy. Generate roughly 20 queries
mixing should-trigger and should-not-trigger. The valuable negatives are near-misses: queries that
share keywords with the skill but need something else.

Score, iterate the wording, re-score, and report the before and after numbers. **A description
change with no score attached is a preference, not an improvement.**

If the false-positive rate stays above 20%, the overlap is with another skill rather than inside
this one — that is a wiring problem, and `harness-wiring-audit.md` Phase 4 is where it gets
measured across the whole harness.

## Degrees of freedom

Match instruction specificity to how fragile the task is.

| Level | When | Style |
|---|---|---|
| **High** | Several valid approaches, context-dependent | Text guidance, heuristics |
| **Medium** | A preferred pattern exists, variation is fine | Pseudocode, parameterised scripts |
| **Low** | Fragile operations, consistency critical | Exact scripts, marked do-not-modify |

## Anti-patterns

| Anti-pattern | Why it hurts |
|---|---|
| Narrative storytelling: "In session X we…" | Too specific to reuse across contexts |
| Multi-language examples: JS plus Python plus Go | Mediocre in each; one excellent example is worth more |
| A workflow summary in the description | The agent reads it and skips the body |
| The same content in body and references | Token waste, and the two drift apart |
| Over-explaining common knowledge | The agent knows what a JSON object is |
| ALL CAPS rules with no reasoning | Brittle; agents route around them under pressure |

## Quality checklist

**Structure**
- [ ] Name is letters, numbers and hyphens; unquoted in the frontmatter
- [ ] `description` is a quoted single-line scalar, free of `<`, `>`, `[`, `]`
- [ ] `name` matches the directory name exactly
- [ ] Description states when to use, carries trigger phrases, summarises no workflow
- [ ] Body under 500 non-empty lines, detail in `references/`
- [ ] The listing budget gate passes, and the entry has not grown without a reason

**Content**
- [ ] Skill type classified: technique, pattern, reference or discipline
- [ ] Description carries synonyms, error messages and near-miss exclusions
- [ ] Overview states the core principle
- [ ] Rules explained with reasoning
- [ ] Nothing duplicated between body and references
- [ ] Every bundled reference is pointed at from the body

**Testing**
- [ ] Behaviour cases written and run
- [ ] With-skill against baseline compared
- [ ] Every gate line run verbatim, plus one run it must fail
- [ ] Improvements made from observed failures, not assumptions
- [ ] The round recorded in `learning.md`, with measured numbers

**Discipline-enforcing skills, additionally**
- [ ] Pressure scenarios built with three or more combined pressures
- [ ] Baseline behaviour documented verbatim without the skill
- [ ] Rationalisation table built
- [ ] Red-flags list written
- [ ] Compliance verified with the skill, under pressure
