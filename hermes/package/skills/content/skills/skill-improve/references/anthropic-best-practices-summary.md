> Hermes auxiliary: `content/` paths are `file_path` values relative to the registered-document parent. Apply the loaded graph-engineering mapping and host policy; this file is served without template expansion.

# Skill Validation Rubric

Policy anchors for skill compliance, split into what `content/skills/skill-improve/scripts/quick_validate.py` fails, what it only warns about, and what stays convention. The shared listing cap belongs to `content/.github/check_listing_budget.py`.

---

## Frontmatter Requirements (MUST)

| Field         | Rule                                                             | Validation            |
| ------------- | ---------------------------------------------------------------- | --------------------- |
| `name`        | MUST be kebab-case (a-z, 0-9, hyphens only)                      | Regex: `^[a-z0-9-]+$` |
| `name`        | SHOULD be under 64 characters                                    | convention; not validated |
| `description` | MUST be at most 1,024 characters                                  | `content/skills/skill-improve/scripts/quick_validate.py` Rule 1 (fails) |
| listing entry | MUST fit 1,536 characters of `name`, `description` and `when_to_use` combined — the client's listing entry, a different object from the frontmatter field | `content/.github/check_listing_budget.py` ENTRY_CAP (fails) |
| `description` | MUST NOT contain `<` or `>`; `[` and `]` stay out by convention      | `content/skills/skill-improve/scripts/quick_validate.py` (fails on `<` `>`) |
| `description` | SHOULD start with "Use when...", "Use for...", "Use to..." or "Help with..." | `content/skills/skill-improve/scripts/quick_validate.py` warns on stderr; exit code unchanged |
| `description` | MUST be quoted when it contains `: ` (an unquoted value is invalid YAML and the skill never registers) | `content/skills/skill-improve/scripts/quick_validate.py` (fails) |

---

## Trigger Phrasing Quality (policy; the validator only warns, never fails)

- SHOULD start with "Use when...", "Use for...", "Use to...", or "Help with..."
- MUST describe triggering conditions, not workflow summary
- MUST include specific symptoms or contexts ("race conditions", "flaky tests")
- MUST NOT summarize what the skill does (agent will skip full reading)
- SHOULD be short with a narrow when: the symptom or context that selects the skill, not an itinerary of steps

**BAD**: "Skill for TDD: write test first, watch it fail..." (workflow summary)
**GOOD**: "Use when implementing any feature before writing implementation code" (trigger)

---

## Section Structure (SHOULD)

| Section                             | Requirement                                 |
| ----------------------------------- | ------------------------------------------- |
| `When to Use`                       | SHOULD list SYMPTOMS and use cases          |
| `When NOT to Use`                   | SHOULD clarify boundaries and anti-triggers |
| `Anti-Patterns`                     | SHOULD document common mistakes with fixes  |
| `Validation` or `Quality Checklist` | SHOULD provide verification steps           |

---

## Content Policies

### Token Efficiency (MUST)

- MUST keep the SKILL.md body at or under 500 non-empty lines (blank lines are not counted — `content/skills/skill-improve/scripts/quick_validate.py` Rule 2)
- MUST move details >100 lines to `references/*.md`
- MUST challenge each paragraph: "Does the agent need this?"

### Naming (MUST)

- MUST NOT use generic labels: `helper`, `utils`, `tools`
- MUST match the directory name exactly, unquoted in the frontmatter

A gerund form (`creating-skills`) reads well upstream but is not a rule here: no skill this plugin
ships uses it, and enforcing it would condemn every name in the repository including this one.

### Progressive Disclosure (SHOULD)

- SHOULD use self-contained structure for <100 lines
- SHOULD use references/ directory for heavy docs
- SHOULD use scripts/ for deterministic operations
- SHOULD keep SKILL.md a minimal router: trigger, minimum method, stop condition and conditional references, never the full recipe

---

## Degrees of Freedom

| Level      | When                      | Style                                   |
| ---------- | ------------------------- | --------------------------------------- |
| **High**   | Multiple valid approaches | Text guidance, heuristics               |
| **Medium** | Preferred pattern exists  | Pseudocode, parameterized scripts       |
| **Low**    | Fragile/error-prone ops   | Exact scripts, "do not modify" warnings |

---

## Verification Loops (MUST for L4+)

```
1. Make edits
2. Validate immediately (content/skills/skill-improve/scripts/quick_validate.py or lint)
3. If validation fails: fix -> validate again
4. Only proceed when validation passes
```

**Required for**: Schema changes, API contracts, auth flows, security code.

The script is the check; asking the model to "double-check" its own work adds no evidence.

---

## Quality Gates (MUST)

### Structure

- [ ] Frontmatter has `name` and `description`; client-honoured keys such as `argument-hint`, `user-invocable` and `license` are allowed and not rejected
- [ ] `name` matches kebab-case regex
- [ ] `description` starts with an approved trigger phrase (the validator only warns)
- [ ] SKILL.md body at or under 500 non-empty lines
- [ ] No Windows-style paths (`\\`)

### Content

- [ ] Description is specific with key terms
- [ ] Includes when to use (triggers), not what it does
- [ ] Consistent terminology throughout
- [ ] Concrete examples (not abstract concepts)
- [ ] No time-sensitive information

### Code & Scripts

- [ ] Scripts solve problems deterministically
- [ ] Error handling is explicit and helpful
- [ ] Required packages listed
- [ ] No hardcoded secrets or credentials

### Testing (Discipline Skills)

- [ ] At least 3 evaluation scenarios created
- [ ] Pressure scenarios test compliance under load
- [ ] Baseline behavior documented without skill

---

## Anti-Patterns (MUST NOT)

| Pattern                          | Why Blocked                                         |
| -------------------------------- | --------------------------------------------------- |
| Workflow summary in description  | Agent skips SKILL.md body                           |
| Windows-style paths              | Cross-platform breakage                             |
| Over-explaining common knowledge | Wastes tokens                                       |
| Multi-language examples          | Maintenance burden; one excellent example is enough |
| Time-sensitive info              | Creates outdated guidance                           |
| Generic section labels           | Poor discoverability                                |

---

## Quick Validation

Run `python3 content/skills/skill-improve/scripts/quick_validate.py <skill-path>`:

**Exit codes** — the script emits exactly two, whatever the category of the violation:

- `0`: every rule passes
- `1`: any violation, frontmatter or structure or content policy alike

The trigger-phrase rule is a warning on stderr and never changes the exit code, so a skill whose
description does not start with "Use when" still exits `0`.

**Auto-fixable**:

- Path separators (`\\` -> `/`)
- Trailing whitespace
- Missing newline at EOF
