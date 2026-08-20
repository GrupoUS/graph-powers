# Testing Skills — TDD for Process Documentation

> **Core principle:** If you didn't watch an agent fail without the skill, you don't know if the skill prevents the right failures.

## TDD Mapping

| TDD Phase | Skill Testing | Action |
|-----------|---------------|--------|
| **RED** | Baseline test | Run scenario WITHOUT skill, watch agent fail |
| **Verify RED** | Capture rationalizations | Document exact failures verbatim |
| **GREEN** | Write skill | Address specific baseline failures |
| **Verify GREEN** | Pressure test | Run scenario WITH skill, verify compliance |
| **REFACTOR** | Plug holes | Find new rationalizations, add counters |
| **Stay GREEN** | Re-verify | Test again, ensure still compliant |

---

## When to Test

**Test skills that:**
- Enforce discipline (TDD, verification requirements)
- Have compliance costs (time, effort, rework)
- Could be rationalized away ("just this once")
- Contradict immediate goals (speed over quality)

**Don't test:**
- Pure reference skills (API docs, syntax guides)
- Skills without rules to violate
- Skills agents have no incentive to bypass

---

## Testing by Skill Type

### Discipline-Enforcing Skills
**Test with:** Academic questions → Pressure scenarios → Multiple pressures combined
**Success:** Agent follows rule under maximum pressure

### Technique Skills
**Test with:** Application scenarios → Edge cases → Missing information tests
**Success:** Agent successfully applies technique to new scenario

### Pattern Skills
**Test with:** Recognition scenarios → Application scenarios → Counter-examples
**Success:** Agent correctly identifies when/how to apply pattern

### Reference Skills
**Test with:** Retrieval scenarios → Application scenarios → Gap testing
**Success:** Agent finds and correctly applies reference information

---

## RED Phase: Baseline Testing

**Goal:** Run pressure scenarios WITHOUT the skill. Document exact behavior.

### Writing Pressure Scenarios

Create realistic scenarios combining 3+ pressure types:

| Pressure Type | Effect | Example |
|--------------|--------|---------|
| **Time** | Creates urgency to skip steps | "It's 6pm, dinner at 6:30pm" |
| **Sunk cost** | Makes deletion painful | "You spent 4 hours on this" |
| **Authority** | Creates pressure to comply with bad practice | "Team lead says skip tests" |
| **Exhaustion** | Reduces willpower for discipline | "This is the 5th iteration" |

### Scenario Template

```markdown
IMPORTANT: This is a real scenario. Choose and act.

[Context with sunk cost pressure]
[Time pressure]
[Situation requiring the skill's discipline]

Options:
A) [Correct but costly option]
B) [Tempting shortcut]
C) [Compromise that still violates the rule]

Choose A, B, or C.
```

### Process

1. Create pressure scenarios (3+ combined pressures)
2. Run WITHOUT skill — give agent realistic task with pressures
3. Document choices and rationalizations **word-for-word**
4. Identify patterns — which excuses appear repeatedly?
5. Note effective pressures — which scenarios trigger violations?

**NOW you know exactly what the skill must prevent.**

---

## GREEN Phase: Write Minimal Skill

Write skill addressing the SPECIFIC baseline failures documented. Don't add content for hypothetical cases.

Run same scenarios WITH skill. Agent should now comply.

If agent still fails: skill is unclear or incomplete. Revise and re-test.

---

## REFACTOR Phase: Close Loopholes

Agents are smart and will find workarounds when under pressure. For each new rationalization found:

### 1. Explicit Negation in Rules

Don't just state the rule — forbid specific workarounds:

```markdown
# ❌ Insufficient
Write code before test? Delete it.

# ✅ Bulletproof
Write code before test? Delete it. Start over.

**No exceptions:**
- Don't keep it as "reference"
- Don't "adapt" it while writing tests
- Delete means delete
```

### 2. Rationalization Table

Every excuse agents make goes in the table:

```markdown
| Excuse | Reality |
|--------|---------|
| "Too simple to test" | Simple code breaks. Test takes 30 seconds. |
| "I'll test after" | Tests after = "what does this do?" not "what should this do?" |
| "Tests after achieve same goals" | Different question ≠ same goals |
```

### 3. Red Flags List

Make it easy for agents to self-check:

```markdown
## Red Flags — STOP and Start Over
- Code before test
- "I already manually tested it"
- "Tests after achieve the same purpose"
- "This is different because..."
```

### 4. Update Description

Add symptoms of when the agent is ABOUT to violate the rule to the ASO description.

### 5. Re-verify

Run pressure scenarios again. If new rationalizations appear, repeat the REFACTOR loop.

---

## Common Rationalizations for Skipping Testing

| Excuse | Reality |
|--------|---------|
| "Skill is obviously clear" | Clear to you ≠ clear to other agents. Test it. |
| "It's just a reference" | References can have gaps. Test retrieval. |
| "Testing is overkill" | Untested skills have issues. Always. 15 min saves hours. |
| "I'll test if problems emerge" | Problems = agents can't use skill. Test BEFORE deploying. |
| "Too tedious to test" | Less tedious than debugging bad skill in production. |
| "I'm confident it's good" | Overconfidence guarantees issues. Test anyway. |

**All of these mean: Test before deploying. No exceptions.**

---

## Checklist

- [ ] Skill type identified (Discipline / Technique / Pattern / Reference)
- [ ] Pressure scenarios created (3+ combined pressures for discipline skills)
- [ ] Baseline behavior documented WITHOUT skill (RED)
- [ ] Specific rationalizations captured verbatim
- [ ] Skill written addressing those exact failures (GREEN)
- [ ] Agent complies WITH skill present (Verify GREEN)
- [ ] Rationalization table built from all test iterations (REFACTOR)
- [ ] Red flags list created
- [ ] Re-tested until bulletproof (Stay GREEN)
