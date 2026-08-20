---
name: hooks-block-own-probes
description: In gpus-harness, an agent's own Bash probe is judged by smart_bash_approver — inline heredocs containing floor strings get denied; put probes in a scratchpad file.
metadata:
  type: project
---

Probe scripts for `hooks/smart_bash_approver.py` must be written to a scratchpad **file** and
run as `python3 <path>`, never pasted into an inline `bash <<'PY'` heredoc.

**Why:** the session runs the harness it is editing. The approver reads the whole Bash command
string, so a heredoc carrying a fixture like `rm -rf /` is itself denied — the guardrail firing
on its own test data. This bit during the seven-defect P0 pass on 2026-08-20, and the segment
splitter fixed that day made it *stricter*: pipes, newlines, `$( )` and backticks are now each
classified separately, so far more inline probe text reaches the floor than before.

**How to apply:** when reproducing or verifying anything in `hooks/`, write the probe to the
session scratchpad and invoke it by path. If a fixture string must contain a floor pattern,
assemble it (`"rm -" + "rf /"`) the way `hooks/test_hooks.py` already assembles `GIT_WRITE` for
exactly this reason.

Related: [[harness-gate-is-test-hooks]]
