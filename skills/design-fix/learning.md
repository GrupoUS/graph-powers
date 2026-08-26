# learning.md — round history for `design-fix`

One entry per round: hypothesis, change, measurement, verdict. A round with no measured number is a
hunch with markdown around it. A round that changed nothing still gets an entry saying so.

## Round 1 — 2026-08-26 · extracting a host-neutral repair discipline

**Hypothesis:** combining the generic audit breadth of `redesign-existing-projects` with the
adaptive decision gate of an existing project command would produce a reusable repair skill, but a
direct merge would collide with `designer` and leak project-specific values and tooling.

**Change:** made `design-fix` the production-readiness discipline for implemented interfaces.
Project authority replaces hardcoded design values; surgical work gets one compact contract;
structural work reopens `designer` and waits for user selection. Existing `designer` craft passes
remain the single source for audit and implementation detail. Added four positive cases, including a
three-pressure discipline scenario, and four boundary-negative cases.

**Measurement:** `quick_validate.py` exited 0; an unquoted `description: Use when: ...` fixture
exited 1. The listing measured 10,721 / 10,752 characters, with 31 characters of headroom. Wiring
checked 287 routing references with 0 unresolved and 12 agents with 0 registration failures;
portability reported 0 problems, machine-path scanning reported none, and 158 artefacts used only
declared placeholders. The suite has 8 cases (4 positive, 4 negative): synthetic correct responses
scored 8/8 at threshold 1.0 and exited 0; removing one response scored 7/8 and exited 1. That first
run exposed one bad English spelling regex, which was fixed from `behavio.r` to `behaviou?r` before
the 8/8 result. Every repository gate exited 0, including the hook suite's final `EVERY GUARANTEE
HELD` verdict.

**Verdict:** kept. The structure, budget, wiring and eval mechanism are measured. Live with-skill
versus baseline behavior remains a separate calibration step because this repository forbids
unrequested subagent runs; the synthetic 8/8 proves the assertions, not model behavior.
