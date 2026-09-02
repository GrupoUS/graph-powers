# Closed — skill-improve lifecycle entry

**Historical symptom:** the fresh run-7 Codex response began with `I couldn’t create the skill because the workspace is read-only and approval escalation is disabled.`; the first-line probe exited `1`, and the tagged candidate grader scored Codex `0/3`. The fresh Claude response also missed `senior-prompt-engineer` and scored `1/2`.

**Attempts:**

- Run 6 corrected discovery/routing and the Codex event oracle; static gates passed, but the loaded Codex response began with a read-only blocker and scored `0/3`.
- Run 7 added a deterministic blocker-before-entry RED, moved one `[HARD] Entry protocol` before the matrix, and passed all local/static gates; the fresh live pair still violated the first-line contract (Codex `0/3`, Claude `1/2`).
- Run 8 tested the SessionStart bridge; polarity was correct, but Codex remained `0/3`.
- Run 9 made the smallest final-response wording correction; Codex and Claude both passed.

**Ruled out:**

- The edited candidate is the executed candidate: the run-7 Codex trace is `observed=load`, owner `graph-powers:skill-improve`, digest `847fb4c720b0cd0a224e83d9a64bf0546d16398eaa64acc1c8a1941e6ffb2a98`.
- Parser, hook routing, prompt selection, sandbox contract and A01-A03 assertions are green and unchanged in run 7.
- The deterministic test detects the ordering defect: the preserved run-6 blocker-first fixture fails and a synthetic entry-before-blocker response passes.
- The environment is not stale: the declared dependency install completed without a lockfile; this repository declares no typecheck, build or lint command.

**Resolved:** the remaining seam was consumer-visible final-response ordering. The final rule now repeats the lifecycle line as the first non-empty line of the final response.

**Disposition:** `R10-F1` is closed after the bounded run-9 candidate satisfied the first-line probe and both tagged graders.

## 6. Context handoff (final)

Run 9 changed only the existing entry-protocol wording in `skills/skill-improve/SKILL.md` and appended
the closure in `skills/skill-improve/learning.md`; the hook, parser, producer, prompts, sandbox and
run-7 control remain frozen. The final candidate pair is in
`.claude/audit/skill-improve-proactivity/run-9/green`.

## Run 8 result (historical) — 2026-09-02

The single candidate capture completed with exit `0`; both traces are clean (`child_exit=0`), share
candidate digest `2bec76ea4f396d664cc258cb67963fb8d94a00445176c977b574c35739e0252f` over 270 files,
and preserve polarity (`codex load/load`, `claude skip/skip`). The tagged grader then exited `1`:
Codex `pro-precreate-skill` scored `0/3` because the first non-empty line was still the read-only
blocker; Claude `bound-agent-prompt-draft` scored `2/2` and selected
`graph-powers:senior-prompt-engineer`.

**Disposition at Run 8:** `NEEDS_WORK`; `R10-F1` was still OPEN at that point. No retry, final evaluator, learning closure or
full final verification was run after the provider-output failure. The next correction must address
the Codex first-line consumer-visible seam before another user-authorized live sample.

## Run 9 result — 2026-09-02

The single final candidate capture completed with exit `0`; both traces are clean (`child_exit=0`),
share candidate digest `0b55ec3bcf19cf499a2831a68bb165af382d5571d580644c52a1430542b91a8a` over 270
files, and preserve polarity (`codex load/load`, `claude skip/skip`). The tagged `proactive-live`
grader exited `0`: Codex `3/3`, Claude `2/2`. The Codex response begins exactly with
`skill-improve Mode A — skill-authoring: RED established by evidence`; `R10-F1` is `CLOSED`.
