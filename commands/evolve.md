---
description: "Turn what this session learned into something the next one inherits — updates the project's rules and AGENTS.md so a mistake does not recur. Use when the user says to capture the learning, make sure this does not happen again, or write the convention down. Do not use for a personal preference, which belongs in memory rather than in the repository."
workflow_type: prompt-chaining
---

# /evolve — Learning Capture

**ARGUMENTS**: $ARGUMENTS

> **Read before step 0 — never reconstruct these from memory:** `${CLAUDE_PLUGIN_ROOT}/references/shared/000-config-loader.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/005-superpowers-bootstrap.md`
> Read `${CLAUDE_PLUGIN_ROOT}/references/shared/060-skill-domain-matrix.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/100-autoresearch-loop.md`

---

## 0. Mode detection

| Token in `$ARGUMENTS` | Behavior |
|---|---|
| (none) | Manual capture flow (§ 1-5) |
| `auto` | Skip § 1-5, run AutoResearch Loop per `${CLAUDE_PLUGIN_ROOT}/references/shared/100-autoresearch-loop.md`. Target skill is second arg (e.g. `/evolve auto debugger`). Default: all skills carrying `evals/evals.json`. |
| `handoff` | Write session state to `.graph-powers/HANDOFF.md` (§ 6) |

---

## 1. First action

```typescript
Skill("superpowers:using-superpowers"); // meta — bootstrap (per `${CLAUDE_PLUGIN_ROOT}/references/shared/005-superpowers-bootstrap.md`)
```

---

## 2. Capture flow

### 2.1 Gather session context

Analyze the current conversation to identify:

```markdown
## Session Context

### Task completed
[brief description]

### Problem found
[bug/error/issue]

### Root cause
[identified root cause]

### Solution applied
[code or specific changes]

### Validation
[commands run: type-check, lint, test, etc.]
```

### 2.2 Append to the project log

Append the block above to `.graph-powers/logs/learnings.md`, newest last, under a dated heading.

Plain markdown, on purpose. A learning store with a database behind it is a store that stops working
the day the script moves, and this file has to survive being read by a person six months from now
with no tooling at all.

Skip the append when the learning is already recorded there — a log that repeats itself stops being
read.

---

## 3. Skill selection

Based on modified file paths + `${CLAUDE_PLUGIN_ROOT}/references/shared/060-skill-domain-matrix.md` (Skill-to-Domain Matrix), identify affected skills.

Generic mapping (the project overrides it in `${rulesDir}/` when it has its own routing):

- `${paths.backendRoot}` → `graph-powers:debugger`
- `${paths.schemaRoot}` → `graph-powers:debugger` + host database skill if configured
- `${paths.frontendRoot}` → `graph-powers:debugger` + the project's design rule (if styling/design)
- Performance changes → `performance-optimization`
- Skill files themselves, or harness wiring → `skill-improve`

Ask user which skills to update if multiple are relevant and not obvious.

---

## 4. Improve skills

If this learning calls for editing or creating a SKILL.md (skill body change, new reference doc, frontmatter `description:` update), invoke `Skill("skill-improve")` first. Its Mode A owns the authoring loop, and `${CLAUDE_PLUGIN_ROOT}/skills/skill-improve/references/testing-skills.md` carries the RED-GREEN-REFACTOR discipline — pressure-test the skill against a subagent before committing. Skip if the learning only adds a new entry to an existing `references/` markdown without changing the SKILL.md body.

For each selected skill, add to `references/` or the relevant SKILL.md section:

```markdown
## Case: [Bug/Problem Name]

**Symptom:** [user-perceived]
**Root cause:** [technical]
**Fix:** [solution applied]
**Files:** [file list]
**Validation:** [gates run]

### Anti-pattern discovered

// ❌ WRONG
[problematic code]

// ✅ CORRECT
[correct code]
```

Categorize:

| Type | Where | When |
|---|---|---|
| Stability rule | dedicated section | Rules to prevent crashes |
| Anti-pattern | existing section | Problematic patterns |
| Known case | `references/` | Complex documented cases |
| Quick reference | existing table | Quick tips |

---

## 5. Improve AGENTS.md (project-level)

Identify the target AGENTS.md from the modified file path:

- Edits in `${paths.backendRoot}/**` → backend AGENTS.md if it exists
- Edits in `${paths.frontendRoot}/**` → frontend AGENTS.md if it exists
- Edits in `${paths.schemaRoot}/**` → schema AGENTS.md if it exists
- Otherwise → root `AGENTS.md`

Load `Skill("graph-powers:intent-layer")` first only when the subtree the learning belongs to has no
`AGENTS.md`, or the node it would land in is past 4k tokens — that skill decides whether the subtree
earns a node and keeps the root's downlinks in step. A learning that fits an existing node is
appended below without it.

Add a new section:

```markdown
### [YYYY-MM-DD] [Learning Title]

> Added after bug fix in `[file]`.

**Problem:** [description]
**Cause:** [root cause]
**Solution:** [fix applied]
```

---

## 6. Handoff mode (`/evolve handoff`)

Write `.graph-powers/HANDOFF.md`, overwriting it. One file, always the same path, because a handoff
nobody can find is a handoff nobody wrote:

```markdown
# Handoff — <YYYY-MM-DD HH:MM>

## Where this stopped
<the last thing that was true: what works, what does not, what was mid-flight>

## Next action
<the single next step, concrete enough to start without re-deriving anything>

## Do not repeat
<what was already tried and ruled out, with why>

## Open questions
<what needs a person, and who>

## State
- Branch: <branch> · working tree: <clean | files listed>
- Gates last run: <command → result>
- Files touched this session: <list>
```

A handoff that says "continue the work" is not a handoff. The test: could someone with no memory of
this session take the next action from this file alone?

`/prime` reads this file first when it exists.

---

## 7. Summary

```
Learning captured.

Log:        .graph-powers/logs/learnings.md
Skills:     [list, or none]
AGENTS.md:  [list, or none]
```

---

## References

- `skill-improve` skill — for any change to a SKILL.md body, and for harness-wiring questions
- AutoResearch Loop: `${CLAUDE_PLUGIN_ROOT}/references/shared/100-autoresearch-loop.md`
