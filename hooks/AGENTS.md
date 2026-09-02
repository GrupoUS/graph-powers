# hooks/

Owns the guardrails: the Python hooks Claude Code, Codex, Cursor and Grok run around every tool
call, their one declaration `hooks.json`, the config reader `_config.py`, and `test_hooks.py`, the
suite that proves them. Does NOT own the config contract (`../schema/config.schema.json`), the
generators that carry the hooks to the other harnesses (`../codex/`, `../cursor/`, `../grok/`), or
the rules a host project keeps under its own `.claude/rules/`.

## Entry points

- `hooks.json` — event → matcher → script, sixteen entries across `PreToolUse`,
  `PermissionRequest`, `SessionStart`, `SubagentStart`, `PostToolUse`, `Stop` and `Notification`.
  Claude Code and Grok discover it natively; `../codex/install.mjs` merges it into `~/.codex/hooks.json`;
  `hooks-cursor.json` is generated from it by `../cursor/install.mjs` and never edited by hand.
- `_config.py` — the only file in the plugin that knows projects differ. It reads the project's
  `.graph-powers/config.json` over the operator's `~/.graph-powers/config.json`, and resolves the
  project from the payload `cwd`, then the environment, then the git root.
- `test_hooks.py` — the sandboxed suite, run from the plugin root: every guardrail's violating case
  and its mirrored legitimate case, two projects side by side, in temporary directories with an
  empty HOME.

## Contracts and invariants

- Fail-open, without exception: invalid payload, missing config, JSON with a typo, unreadable file
  — the defaults, exit 0, never a traceback. The accepted failure is letting something through;
  the unacceptable one is stopping the work through a fault of the hook's own.
- Nothing hardcoded: branch, protected branches, opt-in prefix and paths come from `_config`. No
  hook knows a project's name. The prefix is per project so an approval typed in one repository
  cannot release a gate in another.
- The payload goes through the `_config` helpers — `bash_command`, `canonical_tool`,
  `file_path_from_payload`, `project_dir` — never `payload["tool_input"]`. Claude exports
  `CLAUDE_PROJECT_DIR`; Codex and Cursor pass `cwd`; Grok sends camelCase and
  `GROK_WORKSPACE_ROOT`. A hook that resolves the wrong project denies and permits against
  somebody else's rules.
- Every prohibition has an escape, `<PREFIX>_ALLOW_<ACTION>=1` inline in the command, set by a
  person in the turn they approved it. A ceiling with no override is a wall.
- Every guardrail has its negative test, the mirrored positive, and the garbage-input case in
  `test_hooks.py` before the PR.
- Windows is a third of installs: `subprocess.run(..., encoding="utf-8")`, stdin reconfigured to
  UTF-8, no `select.select`, no `HOME` without `USERPROFILE`, paths compared as
  `PurePath(...).as_posix()`. `.github/check_portability.py` scans this directory for all of it.
- The declaration travels with the hook — `hooks.json`, with `${CLAUDE_PLUGIN_ROOT}` in the path.
  A hook on disk with no declaration never runs; a hook absent from the declaration may still be
  alive as a module imported by one that is present, so grep for an importer before calling it dead.
- `command_trust.py` is the machine-local trust boundary shared by `ultracite.py`, `stop_verify.py`
  and `commit_audit_gate.py`: it matches the canonical project/config identity and raw config
  digest. Missing, malformed or changed approval is `SKIP_UNTRUSTED` and launches no configured
  command. Use the active Python interpreter for `approve [PROJECT]`, `status [PROJECT]` or
  `revoke [PROJECT]`; hook responses never expose a path-bearing approval command.
- Model-facing responses are fixed summaries only: checker stdout/stderr, command text, local
  paths and exception text never cross the hook boundary. Commit enforcement is agent-issued Bash
  `git commit`/`git push` only: commit runs enabled declared core gates in the fixed order
  `typeCheck` → `lint` → `test` → `build`, then the legacy audit, under one combined commit budget;
  push runs the audit only under its audit timeout. `<PREFIX>_ALLOW_VERIFY=1` and
  `<PREFIX>_ALLOW_AUDIT=1` are separate opt-ins.
- The cache accepts only fresh matching green results; failures, timeouts, unavailable tools and
  internal failures are never cached. The exact `.graph-powers/cache/precommit-verification.json`
  artifact is excluded from its own worktree fingerprint.
- Cursor gets only the generated `--graph-powers-client cursor` marker and loop limit `5`; Claude
  blocks Stop. Codex has a Stop schema contract but Desktop/`exec`/UX/loop parity is
  `NOT CONFIRMED`; Grok remains passive/unsupported. The Windows benchmark is report-only, not
  telemetry; no dispatcher, Git-native hooks or staged snapshot is active, and the one lifecycle
  event added since is the advisory `SubagentStart`.

## The usual change

Adding a guardrail:

1. the script, reading the payload through `_config`, deciding, and exiting 0 whatever happens;
2. its entry in `hooks.json` — and nothing by hand in `hooks-cursor.json`, which
   `node ../cursor/install.mjs --emit-only` regenerates;
3. both test cases and the garbage-input case in `test_hooks.py`, under a `###` heading that names
   the incident the guardrail answers;
4. `python3 hooks/test_hooks.py`, `python3 .github/check_portability.py`, and the Codex, Cursor and
   Grok dry-runs `../CONTRIBUTING.md § 5` names;
5. the row in `../references/shared/110-guardrails-index.md`, so the map matches the code.

## Anti-patterns — each one shipped once

- A blanket interpreter allow: `^py\s+-3(\s|$)` made `py -3 -c "<anything>"` an allow. What runs
  is the argument; a safe entry names a script path or a `--version`.
- An approver regex written from the unquoted test fixture: the playbook quotes the path, `\S*`
  stops at the space after the closing quote, and the entry asked on every real invocation while
  its test stayed green. Match the literal line the call site emits.
- `turbo --dry=json` on the Bash pipe: turbo panics on EPIPE and Node and bun abort. The approver
  denies it and names `../skills/bun-verify/scripts/turbo_dry_json.py` instead.
- `str.strip("./")` as a prefix remover: it is a character set, and it deleted the leading dot of
  every protected dotfile. `removeprefix` and `removesuffix`.
- A frontmatter reader anchored on `\n`: a CRLF checkout installed zero agents and reported
  success.
- A recursive-delete guard written `(^|/)`: on Windows it never fired.

## Pitfalls

- `smart_bash_approver.py` serves two events from one file: `PreToolUse` decides, and
  `PermissionRequest` answers the prompt under `autonomous`. Codex has no `ask`, so a hook that
  wants the normal approval flow there declines to decide and lets `PermissionRequest` own it.
- `graph_guardrails.py` counts spawns over a rolling window (`graphGuardrails.spawnWindowMinutes`),
  not since session start — a lifetime quota made a long session refuse to fan out.
- `ultracite.py` only formats after edits. `stop_verify.py` owns final lint: exit code decides,
  unavailable tooling is an explicit fail-open skip, and a skipped gate is never reported covered.
- `subagent_context.py` never waits on stdin: a PowerShell wrapper can swallow the piped payload so
  EOF never fires, and a hook that blocks on every spawn is worse than none. Its paragraph is a
  mirror of `../references/shared/025-solution-ladder.md`, bounded by `test_hooks.py`; change the
  file first, then the mirror.
- `auto_update.py` records the throttle before it checks, so a failed check backs off instead of
  retrying every session. It owns only Claude and the stable Codex clone route; native Codex, Cursor
  and Grok caches are foreground-only because an open process may retain the replaced hook path.
- The suite creates its own empty HOME. A case that reads the real `~/.graph-powers/config.json`
  fails as six unrelated guarded-default failures, not as one honest one.

## Related

- `../.claude/rules/hooks.md` — the contract, loaded on any edit here
- `../references/shared/110-guardrails-index.md` — which rules deny in code and which are convention
- `../AGENTS.md` — cardinals 3 and 8, and the gate list
- `../skills/AGENTS.md` — the scripts the approver allows by name
