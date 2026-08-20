---
name: skill-creator
description: "Authoring and iterating one skill: description tuning for reliable triggering, structure, progressive disclosure, and the eval loop that proves a change helped. Use for make a skill for X, improve this skill, my skill is not triggering. Auditing the whole harness is harness-audit."

---

> Derived from `skill-creator` in anthropics/skills (Apache-2.0, see `LICENSE.txt`). Modified by GrupoUS: harness-wiring questions are routed to `harness-audit`, and the iteration loop absorbed this repository's former `skill-improve` skill. Changes are listed in the NOTICE file at the root of the plugin.

# Skill Creator

Guide for creating effective, discoverable, and testable skills — and iterating on them until they work.

## The Core Loop

> **Every skill follows this cycle:** Capture Intent → Draft → Test → Evaluate → Improve → Repeat

Don't skip straight to writing. Understand the intent first, test after writing, and improve based on evidence — not intuition.

---

## About Skills

Skills are self-contained packages that extend AI agent capabilities with specialized knowledge, workflows, and bundled tools.

### Skill Types

| Type           | Purpose                                          | Example                              |
| -------------- | ------------------------------------------------ | ------------------------------------ |
| **Technique**  | Concrete method with steps to follow             | condition-based-waiting              |
| **Pattern**    | Way of thinking about problems                   | flatten-with-flags                   |
| **Reference**  | API docs, syntax guides, tool documentation      | office-docs, pptx-api                |
| **Discipline** | Rules/requirements that enforce compliance       | TDD enforcement                      |

Classify early — it determines testing strategy (see `references/testing-skills.md`).

### Anatomy of a Skill

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter: name, description (required)
│   └── Markdown instructions
└── Bundled Resources (optional)
    ├── scripts/     - Deterministic code; can run without loading into context
    ├── references/  - Documentation loaded as needed
    └── assets/      - Templates, files used in output
```

---

## Step 1: Capture Intent

Before writing anything, understand exactly what the skill should do. Extract answers from the current conversation first (tools used, sequence of steps, corrections, I/O formats). Then ask the user:

1. What should this skill enable Claude to do?
2. When should it trigger? (what phrases, contexts, symptoms)
3. What's the expected output format?
4. Should we set up test cases? (see Step 5 — skills with objectively verifiable outputs benefit most)

Ask one question at a time. Wait for confirmation before moving to drafting.

---

## Step 2: Plan & Research

For each concrete use case the user describes:

1. Think through how you'd execute it from scratch
2. Identify what scripts, references, or assets would help when repeated
3. Choose a file organization pattern:

| Pattern                  | Structure                                      | When to Use                             |
| ------------------------ | ---------------------------------------------- | --------------------------------------- |
| **Self-contained**       | `skill/SKILL.md` only                          | All content fits inline, no heavy refs  |
| **With reusable tool**   | `skill/SKILL.md` + `scripts/`                  | Code rewritten repeatedly across runs   |
| **With heavy reference** | `skill/SKILL.md` + `references/` + `scripts/`  | Reference material > 100 lines          |

Research before writing: check available MCPs (Tavily for best practices, Context7 for library docs) and run subagents in parallel if available.

---

## Step 3: Initialize

Run the init script to generate a template:

```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/skill-creator/scripts/init_skill.py <skill-name> --path <output-dir>
```

Creates the directory with SKILL.md template and example resource directories. Customize or delete generated files as needed.

---

## Step 4: Write the Skill

### Description Field (Critical for Triggering)

The description is the **primary triggering mechanism**. Agents decide whether to use a skill based solely on this field.

**Key principle:** Description = *When to use* (triggering conditions + symptoms). NOT a workflow summary.

```yaml
# ❌ BAD: Summarizes workflow — agent reads description instead of skill body
description: Skill for TDD — write test first, watch it fail, write minimal code

# ❌ BAD: Too vague — doesn't trigger on real user phrases
description: Helps with testing

# ✅ GOOD: Specific conditions and symptoms that match what users actually type
description: Use when implementing any feature or bugfix, before writing implementation code. Trigger on: "write tests", "add feature", "fix bug", "implement X".
```

**Make descriptions slightly "pushy"**: Agents tend to undertrigger — they don't use skills when they'd be useful. Include synonyms, related terms, and explicit trigger phrases. Example: instead of "for dashboard creation", write "for dashboard creation — also trigger when the user mentions data visualization, internal metrics, or wants to display any kind of company data, even if they don't say 'dashboard'."

**Formula:**
```
Use when [specific symptoms/contexts]. Trigger on: [phrases users actually type].
```
Max 1024 characters. Start with "Use when". Include error messages, symptoms, tool names.

### SKILL.md Structure

```markdown
---
name: skill-name
description: Use when [conditions]. Trigger on: [phrases].
---

# Skill Name

## Overview
Core principle in 1-2 sentences.

## When to Use
Bullet list of symptoms and use cases. Include "When NOT to use."

## Core Pattern (for techniques/patterns)
Before/after comparison.

## Quick Reference
Table or bullets for common operations.

## Implementation
Inline code for simple patterns. Link to file for heavy reference.

## Common Mistakes
What goes wrong + fixes.
```

### Token Efficiency

The context window is shared. Every SKILL.md line competes with conversation history.

- **Target**: SKILL.md body < 500 lines
- Move details to `references/` — keep SKILL.md as an overview with pointers
- Cross-reference instead of duplicating
- One excellent example beats three mediocre ones
- Challenge each paragraph: "Does the agent need this, or is it common knowledge?"

### Progressive Disclosure

| Level | Content | Budget |
|-------|---------|--------|
| 1 — Metadata | `name` + `description` | ~100 words, always loaded |
| 2 — SKILL.md body | Core instructions | < 500 lines, loaded on trigger |
| 3 — Bundled resources | Scripts, references, assets | Unlimited, loaded on demand |

Point to bundled resources clearly from SKILL.md with guidance on when to read them.

### Writing Style

- Imperative form: "Validate input before calling the API" not "You should validate..."
- Explain the *why* behind rules, not just the rule. Agents with good theory of mind follow reasoning better than commandments.
- Avoid ALL CAPS MUST/NEVER — if you find yourself reaching for them, that's a signal to explain the reasoning instead.
- Don't put content in both SKILL.md and references — pick one home.

---

## Step 5: Test & Evaluate

**Test before deploying. Always. Even reference skills.**

### 5a. Write Test Cases

Come up with 2-3 realistic prompts — the kind a real user would actually type. Save to `evals/evals.json`:

```json
{
  "skill_name": "example-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "User's realistic task prompt",
      "expected_output": "Description of what success looks like",
      "assertions": [
        { "id": "A01", "description": "Output contains X", "check": "contains: X", "critical": true }
      ]
    }
  ]
}
```

Share with the user for review before running.

### 5b. Run With-Skill vs. Baseline

For each test case, spawn two subagents in the same turn — one with the skill loaded, one without (or with the old version if iterating):

```
With-skill run:
- Skill path: <path-to-skill>
- Task: <eval prompt>
- Save outputs to: <workspace>/iteration-N/eval-<id>/with_skill/outputs/

Baseline run (same prompt):
- No skill (or old skill snapshot)
- Save to: without_skill/outputs/ (or old_skill/outputs/)
```

**Don't spawn with-skill first and baselines later** — launch both together so they finish concurrently.

### 5c. Draft Assertions While Runs Complete

While subagents are running, draft quantitative assertions. Good assertions are:
- **Objectively verifiable** — not "output looks good"
- **Discriminating** — would fail without the skill
- **Named descriptively** — someone reading results immediately understands what each checks

Skip quantitative assertions for subjective skills (writing style, design quality). Focus on qualitative review instead.

### 5d. Review Results

After runs complete:

1. Run `scripts/run_evals.py` to grade assertions against outputs
2. Show the user results for qualitative review (outputs side by side)
3. Capture their feedback — specific complaints per test case

For discipline-enforcing skills, see `references/testing-skills.md` for the full RED-GREEN-REFACTOR pressure testing methodology.

---

## Step 6: Improve & Iterate

This is the heart of the loop. Improve the skill based on evidence, not intuition.

### How to Think About Improvements

1. **Generalize from feedback.** The skill will be used across many prompts and contexts, not just the test cases. Make changes that address the underlying pattern, not just the specific example.

2. **Keep the skill lean.** Remove instructions that aren't pulling their weight. Read the transcripts — if the skill is causing the agent to waste time on unproductive detours, cut the parts causing that.

3. **Explain the why.** Replace rigid rules ("ALWAYS do X") with reasoning ("Do X because Y — without it, Z breaks"). Agents with context follow reasoning better than commandments, and can handle edge cases the rules don't cover.

4. **Bundle repeated work.** If multiple test runs independently wrote the same helper script, that script belongs in `scripts/`. Write it once, reference it in SKILL.md.

### Iteration Loop

After improving:
1. Rerun all test cases into `iteration-N+1/` including baselines
2. Review results with the user
3. Read feedback, improve again, repeat

Stop when: user is satisfied, all feedback is empty, or you're not making meaningful progress.

---

## Step 7: Optimize the Description

After the skill body is stable, optimize the description for triggering accuracy.

Generate 20 eval queries — a mix of should-trigger and should-not-trigger — and verify the description reliably picks the right ones. The most valuable negative cases are near-misses: queries that share keywords with the skill but need something different.

Score the description against that set with the bundled runner:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/skill-creator/scripts/run_evals.py" --skill-path <path-to-skill> --evals-path <path-to-skill>/evals.json --response-file <captured-response>.txt --test-case <case-id> --threshold 1.0
```

Iterate the description, re-score, and report the before/after numbers. A description change with no
score attached is a preference, not an improvement.

---

## Degrees of Freedom

Match instruction specificity to the task's fragility:

| Level              | When to Use                                 | Style                             |
| ------------------ | ------------------------------------------- | --------------------------------- |
| **High freedom**   | Multiple valid approaches, context-dependent| Text guidance, heuristics         |
| **Medium freedom** | Preferred pattern exists, variation OK      | Pseudocode, parameterized scripts |
| **Low freedom**    | Fragile operations, consistency critical    | Exact scripts, "do not modify"    |

---

## Anti-Patterns

| Anti-Pattern                                | Why Bad                                                        |
| ------------------------------------------- | -------------------------------------------------------------- |
| Narrative storytelling ("In session X...")  | Too specific, not reusable across contexts                     |
| Multi-language examples (JS + Py + Go)      | Mediocre quality, maintenance burden. One excellent > three OK |
| Workflow summary in description             | Agent shortcuts reading the full skill body                    |
| Content in both SKILL.md and references     | Token waste, maintenance drift when they diverge               |
| Over-explaining common knowledge            | Agent knows what a JSON object is                              |
| ALL CAPS rules without reasoning            | Brittle compliance; agents find workarounds under pressure     |

---

## Quality Checklist

### Structure
- [ ] Name: letters, numbers, hyphens only (no special chars)
- [ ] YAML frontmatter with `name` and `description` only (max 1024 chars)
- [ ] Description starts with "Use when…", includes trigger phrases, no workflow summary
- [ ] SKILL.md body under 500 lines; details in `references/` if needed

### Content
- [ ] Skill type classified (Technique / Pattern / Reference / Discipline)
- [ ] Description includes synonyms, error messages, and near-miss exclusions
- [ ] Clear overview with core principle
- [ ] Rules explained with reasoning, not just directives
- [ ] No content duplicated between SKILL.md and references

### Testing
- [ ] At least 2-3 realistic test cases written and run
- [ ] With-skill vs. baseline comparison done
- [ ] Results reviewed (quantitative assertions + user qualitative review)
- [ ] Improvements made based on observed failures, not assumptions

### Discipline-Enforcing Skills (additional)
- [ ] Pressure scenarios created (3+ combined pressures)
- [ ] Baseline behavior documented verbatim WITHOUT skill
- [ ] Rationalization table built
- [ ] Red flags list created
- [ ] Verified compliant WITH skill under pressure

---

## Resources

| Resource | Purpose |
|----------|---------|
| `references/testing-skills.md` | TDD-for-skills: RED/GREEN/REFACTOR cycle, pressure scenarios |
| `references/persuasion-principles.md` | Techniques for discipline-enforcing skills |
| `references/anthropic-best-practices-summary.md` | Condensed official Anthropic skill authoring guidance |
| `scripts/init_skill.py` | Initialize new skill directory with template |
| `scripts/package_skill.py` | Package skill for distribution as `.skill` file |
| `scripts/quick_validate.py` | Validate skill structure against quality checklist |
| `scripts/run_evals.py` | Run binary assertion evals against skill responses |
