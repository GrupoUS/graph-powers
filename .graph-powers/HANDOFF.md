# Blocked — skill-improve lifecycle entry

**Symptom:** the fresh run-7 Codex response still began with `I couldn’t create the skill because the workspace is read-only and approval escalation is disabled.`; the first-line probe exited `1`, and the tagged candidate grader scored Codex `0/3`. The fresh Claude response also missed `senior-prompt-engineer` and scored `1/2`.

**Attempts:**

- Run 6 corrected discovery/routing and the Codex event oracle; static gates passed, but the loaded Codex response began with a read-only blocker and scored `0/3`.
- Run 7 added a deterministic blocker-before-entry RED, moved one `[HARD] Entry protocol` before the matrix, and passed all local/static gates; the fresh live pair still violated the first-line contract (Codex `0/3`, Claude `1/2`).

**Ruled out:**

- The edited candidate is the executed candidate: the run-7 Codex trace is `observed=load`, owner `graph-powers:skill-improve`, digest `847fb4c720b0cd0a224e83d9a64bf0546d16398eaa64acc1c8a1941e6ffb2a98`.
- Parser, hook routing, prompt selection, sandbox contract and A01-A03 assertions are green and unchanged in run 7.
- The deterministic test detects the ordering defect: the preserved run-6 blocker-first fixture fails and a synthetic entry-before-blocker response passes.
- The environment is not stale: the declared dependency install completed without a lockfile; this repository declares no typecheck, build or lint command.

**Still open:** whether the Codex provider emits the refusal before consuming the loaded skill body, or whether the entry rule needs an earlier consumer-visible seam (for example, the lifecycle pointer/description boundary). The Claude owner-token miss is also provider-output variability, not a trace-selection defect.

**Needs:** a new user-authorized bounded run with an independent evaluator/reasoning pass before any further provider sample. Keep run-7 traces immutable, do not retry this run, and do not close `R10-F1` until a fresh candidate satisfies the first-line probe and both tagged graders.

## 6. Context handoff

Run 8 reopens only the `SessionStart` bridge in `hooks/session_context.py`; the body, description,
parser, producer, prompts, sandbox and run-7 traces stay frozen. The writer must run the focused hook
RED/GREEN checks, then the controller may launch exactly one Codex/Claude candidate pair in
`.claude/audit/skill-improve-proactivity/run-8/bridge-candidate` against the immutable run-7 control.
