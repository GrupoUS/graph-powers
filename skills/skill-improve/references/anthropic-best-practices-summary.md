# Skill Validation Rubric

Strict policy anchors for skill compliance. Use with `quick_validate.py`.

---

## Frontmatter Requirements (MUST)

| Field         | Rule                                                             | Validation            |
| ------------- | ---------------------------------------------------------------- | --------------------- |
| `name`        | MUST be kebab-case (a-z, 0-9, hyphens only)                      | Regex: `^[a-z0-9-]+$` |
| `name`        | MUST be under 64 characters                                      | `len(name) < 64`      |
| `description` | MUST fit the shared listing entry cap of 1,536 characters        | `check_listing_budget.py` |
| `description` | MUST NOT contain angle brackets `<>` or `[]`                     | Grepped exclusion     |
| `description` | MUST start with "Use when..." or equivalent practical invocation | Pattern match         |

---

## Trigger Phrasing Quality (MUST)

- MUST start with "Use when...", "Use for...", "Use to...", or "Help with..."
- MUST describe triggering conditions, not workflow summary
- MUST include specific symptoms or contexts ("race conditions", "flaky tests")
- MUST NOT summarize what the skill does (agent will skip full reading)

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

- MUST keep SKILL.md body under 500 lines
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
2. Validate immediately (quick_validate.py or lint)
3. If validation fails: fix -> validate again
4. Only proceed when validation passes
```

**Required for**: Schema changes, API contracts, auth flows, security code.

---

## Quality Gates (MUST)

### Structure

- [ ] Frontmatter has only `name` and `description`
- [ ] `name` matches kebab-case regex
- [ ] `description` starts with approved trigger phrase
- [ ] SKILL.md body under 500 lines
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

Run `python3 ${CLAUDE_PLUGIN_ROOT}/skills/skill-improve/scripts/quick_validate.py <skill-path>`:

**Exit codes** — the script emits exactly two, whatever the category of the violation:

- `0`: every rule passes
- `1`: any violation, frontmatter or structure or content policy alike

The trigger-phrase rule is a warning on stderr and never changes the exit code, so a skill whose
description does not start with "Use when" still exits `0`.

**Auto-fixable**:

- Path separators (`\\` -> `/`)
- Trailing whitespace
- Missing newline at EOF
