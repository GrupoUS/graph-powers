# Agent Handoff Contracts

> Canonical structured handoff schema returned by every Claude Code subagent.
> Loaded by `senior-prompt-engineer` skill. Cited by `references/shared-context.md § 7.5`.

---

## 1. Spawn template (5 mandatory context fields)

Every `Agent()` / `Task()` invocation MUST inject these fields into the prompt. Promoted from `orchestrator.md` to skill SSOT — do not re-declare in command bodies.

```markdown
## MANDATORY CONTEXT
**Original request:** <verbatim user message that started this session>
**User decisions:** <approach choices made so far — e.g., "user chose Option B for the hero layout">
**Prior agent findings:** <1-2 sentence summary from each completed agent — key facts only>
**Current plan state:** <phase N, task X of Y — what has already been done>
**Do NOT redo:** <what prior agents already covered — skip to avoid duplication>
```

**Why:** agents without context rediscover what the parent already knows. Wastes tokens, conflicts with prior decisions, multiplies parallel-spawn overhead. The 5-field block is the minimum viable handoff for any spawn.

**Edge cases:**
- L1-L2 direct fix (no prior agent): leave `Prior agent findings` and `Do NOT redo` empty (`—`).
- First spawn of a session: `User decisions` is `—`.
- **Never omit the section.** Empty fields signal "fresh start"; missing section signals "broken contract".

---

## 2. Context Handoff (return schema)

Every agent returns this block at the end of its response. Single canonical shape — no variants per agent type.

### Markdown form (default)

```markdown
## Context Handoff
- **Status:** COMPLETED | BLOCKED | REVISION_REQUIRED
- **Confidence:** 1-5
- **Artifacts:**
  - `<path>:<lines>` — <action: created | modified | deleted | inspected>
  - …
- **Quality gates:**
  - <name>: PASS | FAIL — <evidence: command output, file ref, screenshot path>
  - …
- **Decisions:**
  - <what>: <why>
  - …
- **Risks:**
  - <desc> → <mitigation>
  - …
- **Next agent:** <agent-name> | NONE
- **Resume hint:** <one sentence telling the next agent where to pick up>
```

### JSON form (for `/verify` consolidator + tooling)

```json
{
  "status": "COMPLETED",
  "confidence": 4,
  "artifacts": [
    { "path": "<src>/<module>/<file>.<ext>", "lines": "12-45", "action": "modified" }
  ],
  "qualityGates": [
    { "name": "<type-check command>", "status": "PASS", "evidence": "0 errors" }
  ],
  "decisions": [
    { "what": "<decision>", "why": "<rationale>" }
  ],
  "risks": [
    { "desc": "<risk>", "mitigation": "<how it was or will be mitigated>" }
  ],
  "nextAgent": "verification",
  "resumeHint": "<one sentence telling the next agent where to pick up>"
}
```

---

## 3. Status semantics + invariants

| Status | Meaning | Required fields |
|---|---|---|
| `COMPLETED` | Task done. All listed quality gates PASS. | `artifacts[]` non-empty (or `[]` if read-only); all `qualityGates[].status == PASS` |
| `BLOCKED` | Cannot proceed without external input or escalation. | `risks[]` non-empty AND every entry has a `mitigation` (or `mitigation: "ESCALATE"` to flag for parent) |
| `REVISION_REQUIRED` | Returned by reviewer agents (`evaluator`, `code-reviewer`, `codex:rescue`) when output fails its rubric. | `decisions[]` lists each failed criterion + the threshold it missed |

**Invariants:**
1. `confidence < 3` on a **critical** finding → status MUST be `BLOCKED` (per `CLAUDE.md § Stopping conditions`).
2. `BLOCKED` cannot omit `risks[].mitigation`. A blocker without an escalation path is a defect.
3. `REVISION_REQUIRED` is reviewer-only. Implementer agents return `BLOCKED` instead.
4. `nextAgent: NONE` is valid only when `status: COMPLETED` and the task is terminal in its phase.

---

## 4. Coordinator failure recovery

When an agent-team coordinator (`/implement § 6`) receives `REVISION_REQUIRED` from a specialist:

1. **Iteration 1:** coordinator forwards reviewer's failures back to the responsible specialist with explicit fix list. Specialist resubmits.
2. **Iteration 2:** if specialist returns `REVISION_REQUIRED` again, coordinator forwards once more — last attempt.
3. **Iteration 3 (would be):** coordinator does NOT retry. Coordinator returns to main agent:
   ```
   BLOCKED: <criterion>
   Specialist <name> failed 2 consecutive revisions on this criterion.
   Last evidence: <reviewer output>
   ```
4. Main agent invokes `/debug recover`. Do **not** escalate to user mid-loop — `/debug recover` triages first.

**Why a hard limit:** without it, REVISION_REQUIRED loops can burn the 5-spawn cap silently and leave the user with no signal except a stalled task tree.

---

## 5. Parallel batch override

When ≥2 agents run in a single message (parallel spawn pattern, `shared-context.md § 7`), each agent returns the standard Context Handoff PLUS the shared findings table from `parallel-batch-contracts.md`. The parent consolidates by:

1. Concatenating all `artifacts[]` entries (deduped by `path`).
2. Merging `qualityGates[]` — a single FAIL across batch members → batch FAIL.
3. Taking max severity / max confidence per finding when row keys overlap.
4. Aggregate `status` rule: `COMPLETED` only if ALL members `COMPLETED`; otherwise the worst status wins (`BLOCKED` > `REVISION_REQUIRED` > `COMPLETED`).

---

## 6. What NOT to put in the handoff

- ❌ Verbose narrative ("So I started by reading the file, then I noticed…"). Use `Decisions` for the why, not the journey.
- ❌ Re-listing the original prompt. The parent has it.
- ❌ Skill content dumps. Reference the skill name; don't paste its body.
- ❌ Speculation without evidence. If `confidence ≤ 2`, mark it `BLOCKED` and ask.
- ❌ "Done" without `qualityGates[]`. A claim of completion without evidence is the most common defect this schema prevents.

---

## 7. Migration note

This schema **replaces** ad-hoc `## Context Handoff` blocks scattered through `debugger.md`, `frontend-specialist.md`, `mobile-developer.md`. Those files reference this schema rather than re-declaring it.

Owner: `senior-prompt-engineer` skill.
