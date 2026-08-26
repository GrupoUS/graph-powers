# Turbo `--dry=json` on a pipe aborts Node and bun

A captured stdout pipe is not a file. turbo 2.x treats EPIPE as a panic.

## Case: SIGABRT cascade from `turbo --dry=json`

**Symptom:** systemd-coredump (or the desktop crash notice) reports SIGABRT on `node …/turbo`,
then bun, sometimes turbo itself. Command line is `turbo run test --dry=json` or
`bun run test --dry=json` / `bun run test -- --dry=json`. Node's `si_code` is `SI_USER`;
turbo's is `SI_TKILL`.

**Root cause:** turbo finished the dry-run and panicked writing the JSON:

```
panicked at library/std/src/io/stdio.rs:1165:9:
failed printing to stdout: Broken pipe (os error 32)
```

Rust `abort()` dumps turbo. The JS launcher in `turbo/bin/turbo` then does
`process.kill(process.pid, signal)` from `ProcessWrap::OnExit`, so Node dies of SIGABRT
on purpose (`uv_kill` in frame 1). bun forwards the same way.

The Bash tool of an agent harness **is** a pipe. Size limits, timeouts, and hung-up
readers close it. `| head` is the same class, not a different one.

**Fix:** never put `--dry=json` / `--dry-run` on bun, turbo, or the node wrapper in the
shell tool. Run the bundled script, then Read the file it printed:

```
python -X utf8 ${CLAUDE_PLUGIN_ROOT}/skills/debugger/scripts/turbo_dry_json.py --task test
```

Declared `${tooling.commands.test}` is unchanged. That string runs the tests. This script
only inspects the graph.

**Files:** `skills/debugger/scripts/turbo_dry_json.py` · `hooks/smart_bash_approver.py`
(`_turbo_dry_json_denial`) · `skills/debugger/references/anti-patterns.md` (catalogue item 37)

**Validation:** `python3 hooks/test_hooks.py` — the deny cases for `--dry=json` and the
allow cases for `bun run test` / `turbo run test --filter=…`. Script with no turbo
installed: non-zero, stdout is not a JSON object.

### Anti-pattern discovered

```
# WRONG — Bash capture is a pipe; turbo panics; Node/bun abort
turbo run test --dry=json
bun run test --dry=json
bun run test -- --dry=json
node node_modules/.bin/turbo run test --dry=json

# CORRECT — stdout is a file; the script prints a path of a few lines
python -X utf8 ${CLAUDE_PLUGIN_ROOT}/skills/debugger/scripts/turbo_dry_json.py --task test
```

A node SIGABRT with `SI_USER` and `uv_kill` in frame 1 is signal forwarding until proven
otherwise. Do not raise `--max-old-space-size`, reinstall Node, or re-run the same Bash
line.
