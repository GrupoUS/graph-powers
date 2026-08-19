---
paths:
  - "hooks/**"
  - ".claude-plugin/plugin.json"
  - "codex/**"
---

# The hook contract

The hooks run in every project that installs the plugin. A defect here is a defect in all of them at
once — hence the rigidity of the rules below.

## Fail-open, without exception

Invalid payload, missing config, JSON with a typo, unreadable file: all of it falls back to the
defaults and exits `0`. A hook that takes the session down when **it** has the bug teaches people to
switch hooks off, and then there is no guardrail at all.

In practice: every `json.load` and every disk access inside `try/except`, and never `raise`.

## Nothing hardcoded

Branch, protected branches and the opt-in prefix come from `_config.py`, which reads the project
config. No hook knows a project's name.

The opt-in prefix is per project on purpose: with the same key in two repositories, an approval
given in one starts counting in the other.

## Both harnesses, same bytes

Claude Code exports `CLAUDE_PROJECT_DIR`; Codex CLI does not, and passes `cwd` in the payload.
`_config.project_dir()` resolves payload `cwd` → env var → git root → cwd, and every hook that reads
the payload passes it in. A guardrail that resolves the wrong project denies and permits against
somebody else's rules, which is worse than not running.

## Every prohibition has an escape

Every block needs an explicit opt-in path — `<PREFIX>_ALLOW_<ACTION>=1` inline in the command. A
ceiling with no override is not a guardrail, it is a wall, and walls get knocked down.

## Every guardrail has a negative test

A guardrail never seen denying is an assumption. `hooks/test_hooks.py` covers each one with the case
that violates **and** the mirrored legitimate case — because a gate that fails the correct case
trains people to ignore gates.

When adding a hook: add both cases, plus the garbage-input case, and run `python3 hooks/test_hooks.py`
before the PR.

## The wiring travels with it

The hook is declared in `.claude-plugin/plugin.json`, with `${CLAUDE_PLUGIN_ROOT}` in the path, and
the Codex side is generated from that same declaration by `codex/install.mjs`. A hook on disk with
no declaration never runs — two of the audited projects had nine each in exactly that state.
