# skill-improver — recurring patterns

Pasted verbatim into the auditor's prompt at `skill-improve` Mode B Phase 5. The agent declares
no `memory:` field on purpose (that would grant `Write` and `Edit`), so this paste is the only
path by which what a round learned reaches the next one. Written by the caller after the user's
approval, never by the agent. Keep under 200 lines and 25 KB.

## Patterns

1. **A hook regex and its test written from the same unquoted string.** The call site quotes the
   path — `python -X utf8 "$PLUGIN/skills/<skill>/scripts/x.py" state .` — and `\S*x\.py(\s|$)`
   stops at the space *after* the closing quote, so the allow entry asked on every real invocation
   while its test, which used the bare spelling, stayed green. The same defect sat in the skill's
   eval assertions the same day. Always match an approver pattern and an assertion against the
   literal line the playbook or command emits, then add that spelling as a test case.
   (Round of 2026-08-26, `hooks/smart_bash_approver.py`, `skills/intent-layer/evals/evals.json`.)

2. **Never call a runner's internals directly.** `run_eval_suite` bypasses `normalize_evals`, so a
   valid `evals.json` raised `KeyError('assertions')` and read as a schema defect. Go through the
   loader (`load_json`) or the CLI, and report an E1 failure only after the documented entry point
   fails. (Same round, `skills/skill-improve/scripts/run_evals.py`.)

3. **A caller-supplied inventory drifts within the hour on a live working tree.** Every
   `AGENT_SETUP.md` edge in the attached graph was nine lines past the disk by the time it was
   read, and two byte counts were stale. Re-check the byte count of two files before trusting any
   line number in an attached inventory; report the drift as a finding rather than citing the
   stale coordinate. (Same round, `.claude/audit/graph.json`.)
