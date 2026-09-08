# hooks/

Owns the Python guardrails, `hooks.json`, configuration reader and sandbox tests. The schema
belongs to `../schema/config.schema.json`; client projections belong to their generators.

## Entry points

- `hooks.json` is the only event/matcher/script declaration. Claude Code and Grok consume it;
  Codex and Cursor project it. Generate `hooks-cursor.json` through `../cursor/install.mjs`.
- `_config.py` resolves project payload → environment → git root → cwd and merges project
  configuration over the permitted operator defaults. Use its `bash_command`, `canonical_tool`,
  `file_path_from_payload` and `project_dir` helpers across client payload shapes.
- `test_hooks.py` exercises hooks in temporary projects with an empty home, including two projects
  with different configuration. Never let a fixture read the operator's real settings.

## Contracts

- Fail open on malformed payload/config, missing files and internal errors: safe defaults, exit 0,
  no traceback. A deliberate policy denial is different from a hook failure.
- Branches, protected paths and opt-in prefixes come from `_config.py`. No project-specific values.
- Every prohibition retains its explicit, project-scoped opt-in. Hooks do not grant authorization;
  the user authorizes the action before its opt-in is set.
- Preserve UTF-8 input/subprocess decoding, bounded waits and Windows path handling. Compare paths
  with `PurePath(...).as_posix()`; support `USERPROFILE` as well as `HOME`.
- Every changed guardrail needs a violating case, a legitimate case and malformed-input coverage.
  A file absent from the hook manifest may still be an imported module; check callers before removal.

## Automatic commands and output

`command_trust.py` is the trust boundary for `ultracite.py`, `stop_verify.py` and
`commit_audit_gate.py`. Approval matches canonical project/config identity and raw config digest.
Missing, malformed or changed approval yields `SKIP_UNTRUSTED` and launches no configured command.
Its operator interface is `approve [PROJECT]`, `status [PROJECT]` or `revoke [PROJECT]`, using the
active Python interpreter. Never put a path-bearing approval command in a hook response.

Checker output is fixed summaries only: never expose checker stdout/stderr, command text, local
paths or exception text. Agent-issued Bash commit runs enabled declared core gates in order
`typeCheck` → `lint` → `test` → `build`, then the legacy audit within one total budget. Push runs
only the audit under its timeout. Keep verify and audit opt-ins separate.

Only fresh matching green results are cached. Failures, timeouts, missing tools and internal errors
never become green entries. Exclude only the exact precommit-verification cache artifact from its
own worktree fingerprint.

## Lifecycle boundaries

- `ultracite.py` formats after edits; `stop_verify.py` owns changed-JS/TS final lint. Exit status
  decides; unavailable tooling is an explicit fail-open skip, never a passing check.
- Claude can block Stop. Cursor uses its generated client marker and bounded follow-ups (limit 5).
  Codex has a Stop schema contract; Desktop/exec/UX/blocking parity is **NOT CONFIRMED**. Grok Stop
  remains passive. No Git-native dispatcher or staged-snapshot execution is active.
- `session_context.py` supplies gate discovery and short conditional pointers. `subagent_context.py`
  supplies the solution ladder to children; it never waits indefinitely for stdin. Keep their
  output bounds and mirrors consistent with the canonical references.
- `graph_guardrails.py` counts spawns over the configured rolling window, not the session lifetime.
- `auto_update.py` records its throttle before checking, including failures. Native cache replacement
  never kills a process; a new session or full Desktop restart remains the apply boundary.

## Change and verify

1. Change the owning hook through `_config.py` helpers. Preserve interpreter/script-specific
   approvals; never allow an arbitrary interpreter command.
2. Update the canonical registration only when wiring changes; generate client projections.
3. Add focused regression coverage, using the exact quoted command emitted by the real caller.
4. Run `python3 hooks/test_hooks.py` and `python3 .github/check_portability.py`; for package/wiring
   changes also run the client checks in `../CONTRIBUTING.md`.
5. Update `../references/shared/110-guardrails-index.md` only when the enforced contract changes.

`turbo --dry=json` through a captured pipe remains prohibited; use the existing helper at
`../skills/debugger/scripts/turbo_dry_json.py`. Shared repository rules and final gates are in
`../AGENTS.md`; skill-script contracts are in `../skills/AGENTS.md`.
