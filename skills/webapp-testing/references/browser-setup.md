# Browser setup — what this harness decides

The `agent-browser` CLI ships its own usage skill, versioned with the binary. **That is the command
reference; this file is not.** Load it once per browser task:

```bash
bunx agent-browser skills get core --full     # the full reference, matched to the installed version
bunx agent-browser skills list                # other bundled skills (electron, dogfood, …)
```

What follows is only what upstream cannot know: which environment to point at, how authentication
works here, what counts as a failure, and when to leave the CLI for Playwright.

## Contents

- [Prerequisites](#prerequisites)
- [Always use a named session](#always-use-a-named-session)
- [Mode selection](#mode-selection)
- [CDP attach — the canonical path for authenticated routes](#cdp-attach--the-canonical-path-for-authenticated-routes)
- [Writing to a staging environment](#writing-to-a-staging-environment)
- [Verdict rules](#verdict-rules)
- [Troubleshooting](#troubleshooting)
- [Playwright fallback](#playwright-fallback)

---

## Prerequisites

```bash
bunx agent-browser --version       # must print a non-empty version (>= 0.26.0)
```

Missing binary, install once:

```bash
bun add -d agent-browser           # at repo root, or the project's declared package manager
bunx agent-browser install         # downloads Chrome for Testing
```

`--version` works but pages fail to open → `bunx agent-browser doctor --fix`.

## Always use a named session

Mint one id at the start of the task, read the value, and pass it on every later command:

```bash
bunx agent-browser session id --scope worktree --prefix task
bunx agent-browser --session <the id it printed> open <url>
```

Substitute the id yourself rather than wrapping the first command in a shell variable — command
substitution is POSIX, and this plugin runs on Windows too.

The default session is a **single browser shared by every agent on the machine**, and it persists
across conversations. Working in it can navigate away from a page another agent is mid-task on, or
from something the person left open. Sessions sharing one Chrome over `--cdp` also want `--pin-tab`
so each stays on its own tab.

## Mode selection

| Mode | When | State |
|---|---|---|
| **Headless** | clean-room smoke, CI-style verification, post-fix evidence | none, ephemeral |
| **CDP attach** ← canonical for **any** authenticated route | anything behind auth; a bug tied to a session; real cookies and extensions | a browser the person signed into |
| **Persistent profile / auth vault** | a scripted sign-in that is repeated often | `--profile <name>`; **fragile** against consent banners and OAuth |

Pick the least stateful mode that still reproduces the bug — persistent state hides flakiness. The
exception is an authenticated route, where CDP attach is the first thing to try, not the last.

**Default target: `${project.stagingUrl}` from `.graph-powers/config.json`.** Never fall back to
`localhost` silently when staging is unreachable — stop and surface it. A hardcoded host in a
verification script is a script that only ever verified one repository.

## CDP attach — the canonical path for authenticated routes

**The person signs in; the agent attaches.** Never automate a login flow: it puts credentials in a
transcript, it breaks on every consent banner and OAuth redirect, and it is the most common way a
verification run becomes an account lockout.

```bash
# Find the binary first — it differs per machine:
#   for b in google-chrome google-chrome-stable chromium chromium-browser #     brave-browser microsoft-edge; do command -v $b; done
# Let the tool create its own profile directory, or pass one the platform actually has —
# on Windows that is under %LOCALAPPDATA%, not a POSIX cache path.
nohup <browser-binary> --remote-debugging-port=9222 --user-data-dir="$HOME/.cache/<project>-staging-chrome" --no-first-run --no-default-browser-check "${project.stagingUrl}/<the route you are verifying>" # (redirect + background: POSIX-only. On Windows use Start-Process -RedirectStandardOutput,
# and put the log somewhere the platform has — tempfile.gettempdir().)
```

Three details that are not optional:

- **A separate `--user-data-dir` is required.** Chrome refuses `--remote-debugging-port` on the
  default profile, and a dedicated directory keeps you out of the person's working browser.
- **Use a stable path**, not a session scratch directory: the profile persists, so the sign-in
  survives between sessions and nobody authenticates twice.
- **Pass the final URL on the command line.** The auth provider redirects to its sign-in page with a
  return parameter and lands the person on the right route afterwards.

Confirm the endpoint before anything else:

```bash
curl -s --max-time 5 http://127.0.0.1:9222/json/version    # must return the browser's JSON
```

No answer → the browser is not up: start it and **ask for the sign-in**. A tab whose title is the
sign-in page means the same thing. Never authenticate on your own.

Then attach — `bunx agent-browser --cdp 9222 <cmd>`, or `connect 9222` once and drop the flag.

**`[HARD]` Never `close` while attached over CDP.** It kills the person's real browser and their
session with it. Over CDP, cleanup is doing nothing.

## Writing to a staging environment

Assume a staging write reaches production data unless the project states otherwise — plenty of
setups share one database. On an authenticated route the default is to **observe**: open, snapshot,
read, cancel. Confirming a mutation — moving, saving, deleting — needs an explicit request from the
person in the current turn.

## Verdict rules

A run FAILS on any of these, and each needs a fix or a concrete explanation:

- any console message at error level;
- any uncaught page error;
- an unexpected 4xx/5xx from the application's own origins. A 401 from a session probe is acceptable
  only on a route that is deliberately unauthenticated.

A run that quietly skipped every authenticated route and reported success is worse than one that
reported half the surface honestly.

Evidence goes under `.graph-powers/logs/` with an absolute path — `network har` writes to disk and
will not create the directory for you.

## Troubleshooting

| Symptom | First step |
|---|---|
| `agent-browser: command not found` | `bun add -d agent-browser` at repo root |
| Chrome download fails behind a proxy | set `HTTPS_PROXY`, then `bunx agent-browser install`; or attach over CDP to an already-installed Chrome |
| `open` hangs | `bunx agent-browser doctor --fix`, then retry |
| Stale refs after a click | re-`snapshot -i` before the next ref-based action |
| Need to watch it happen | add `--headed`; `inspect` opens DevTools |

Everything else: `bunx agent-browser doctor` and the upstream skill.

## Playwright fallback

A devDependency where a project needs it — check `package.json` before assuming.
`bunx playwright install chromium --with-deps` is idempotent.

Reach for it only for what `agent-browser` does not do: multi-browser parity (Firefox, WebKit), the
structured test runner (fixtures, sharding, retries, reporters), `codegen` recording, the trace
viewer timeline, portable `storageState.json`, and video with audio. Request interception is **no
longer** a reason to switch — `network route … --body` and `--abort` cover it unless the rewrite has
to be a function of the original request.

**`[HARD]` Run Playwright scripts with `node`, never `bun run`.** Bun's Windows IPC has a known bug
with the `--remote-debugging-pipe` channel Playwright uses for `chrome-headless-shell`: the process
reports `<launched>`, the pipe never answers, and every launch dies at
`TimeoutError: launch: Timeout 180000ms exceeded`.

```bash
bunx playwright codegen ${project.stagingUrl}          # record interactions into a script
bunx playwright test e2e/<flow>.spec.ts --trace on     # run with a full timeline
bunx playwright show-trace test-results/trace.zip      # read one back
```

Automating a local HTML file needs no server: point the browser at a `file://` URL for the absolute
path. A project-specific smoke script belongs in that project's own `scripts/` — its selectors and
routes are not this plugin's to name.
