# Browser Setup — agent-browser CLI (primary) + Playwright (advanced fallback)

Two browser stacks live side by side:

| Stack | Use for | Invocation |
|---|---|---|
| **agent-browser CLI** (primary) | Quick smoke, ref-based interaction, Bash-driven verification, live debugging via CDP attach, screenshots/console/errors/network capture | `bunx agent-browser <cmd>` |
| **Playwright** (advanced fallback) | Multi-browser (Firefox/WebKit), full test runner with fixtures + assertions + sharding, codegen/recorder, video recording with audio, full traces with timeline, request interception with body rewrites, parallel test files | `node <script>` (NOT `bun run`) |

Default to agent-browser. Reach for Playwright only when you need a feature it lacks (multi-browser parity, structured test files, fixtures).

> Use the project's declared package manager (`tooling.packageManager`) to install, and `bunx`/`npx` to run agent-browser. Run Playwright scripts with `node`, **not** `bun run` — Bun has a known subprocess-pipe bug on Windows that times out Playwright's `chrome-headless-shell` launch at 180s.

---

## Prerequisites

Verify before any browser-driven phase (Phase 0 of the debugger skill):

```bash
bunx agent-browser --version       # must print non-empty version (>= 0.26.0)
```

If the binary is missing, install once:

```bash
bun add -d agent-browser           # at repo root
bunx agent-browser install         # downloads Chrome for Testing into ~/.agent-browser/
```

If `--version` works but pages fail to open, run `bunx agent-browser doctor --fix`.

---

## Mode selection

| Mode | When to use | Profile / state |
|---|---|---|
| **A. Default headless** | Clean-room smoke, CI-style verification, Phase 6 evidence in `frontend-debug` | None — fresh ephemeral session |
| **B. CDP attach** ← **canonical for ANY authenticated route** | Anything behind auth; a bug tied to a session; real cookies and extensions | A dedicated browser with `--remote-debugging-port=9222` plus `bunx agent-browser --cdp 9222` |
| **C. Persistent profile / auth vault** | Scripted sign-in; **fragile** against cookie banners and OAuth screens | `--profile <name>` / `agent-browser auth login` |

Pick the least stateful mode that still reproduces the bug — persistent state hides
flakiness. **Exception:** an authenticated route. There, Option B is the first thing to try rather
than the last; Option C is documented below but fails often against providers with consent screens
or OAuth.

---

## Option A — Default headless (canonical)

The whole loop is `open → snapshot → act on @ref → re-snapshot`. Refs (`@e1`, `@e2`, ...) are recomputed every snapshot — they go stale the moment the page mutates.

### Navigate + read

```bash
bunx agent-browser open ${project.stagingUrl}
bunx agent-browser snapshot -i -c              # interactive elements only, compact
bunx agent-browser get url                     # current URL
bunx agent-browser get title                   # page title
```

### Interact

```bash
bunx agent-browser click @e3                   # click by ref from snapshot
bunx agent-browser fill  @e4 "user@test.com"   # clear + type
bunx agent-browser type  @e4 " more"           # append without clearing
bunx agent-browser press Enter
bunx agent-browser select @e5 "option-value"
bunx agent-browser scroll down 500
bunx agent-browser drag @e1 @e2
```

When refs are awkward, use semantic locators instead:

```bash
bunx agent-browser find role button click --name "Submit"
bunx agent-browser find text "Sign In" click --exact
bunx agent-browser find label "Email" fill "user@test.com"
bunx agent-browser find testid "submit-btn" click
```

### Wait (read this — bad waits cause more failures than bad selectors)

```bash
bunx agent-browser wait @e1                    # until element appears
bunx agent-browser wait --text "Success"       # until text appears
bunx agent-browser wait --url "**/dashboard"   # until URL matches glob
bunx agent-browser wait --load networkidle     # post-navigation network quiet
bunx agent-browser wait --fn "window.app.ready === true"
```

Avoid bare `wait 2000` outside of debugging.

### Evidence capture

```bash
bunx agent-browser screenshot .graph-powers/logs/<flow>.png
bunx agent-browser screenshot .graph-powers/logs/<flow>.png --annotate
bunx agent-browser console                     # JS console messages collected since open
bunx agent-browser errors                      # uncaught page errors
bunx agent-browser network requests            # full request log with status codes
bunx agent-browser network requests --filter "api-staging" # filter
bunx agent-browser network har start .graph-powers/logs/<flow>.har
bunx agent-browser network har stop
```

`console` and `errors` are continuous since `open` — call `console --clear` / `errors --clear` between flows if you want isolation.

### Viewport / device emulation

```bash
bunx agent-browser set viewport 1280 720       # desktop
bunx agent-browser set viewport 375 667        # mobile
bunx agent-browser set device "iPhone 15 Pro"  # full device emulation
bunx agent-browser set media dark              # color scheme
```

`set viewport` is the canonical resize — there is no bare `resize` command.

### Visual diff

```bash
bunx agent-browser diff snapshot               # current vs last snapshot
bunx agent-browser diff screenshot --baseline .graph-powers/logs/baseline.png
```

### Close

```bash
bunx agent-browser close                       # current session
bunx agent-browser close --all                 # every session
```

The browser stays alive between commands until `close`. Leaving it open between flows is the default and intended pattern.

---

## Option B — CDP attach to an existing browser  ← **the canonical path for authenticated routes**

For any probe that has to get past authentication. More reliable than a credential vault
(Option C): a scripted `auth login` runs into cookie banners and OAuth buttons, whereas here the
person signs in once and the session lives in the profile.

### Start the browser (the agent may do this; the sign-in is the person's)

```bash
# Find the binary first — it differs per machine:
#   for b in google-chrome google-chrome-stable chromium chromium-browser \
#     brave-browser microsoft-edge; do command -v $b; done
mkdir -p ~/.cache/<project>-staging-chrome
nohup <browser-binary> \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/.cache/<project>-staging-chrome" \
  --no-first-run --no-default-browser-check \
  "${project.stagingUrl}/<the route you are verifying>" \
  >/tmp/browser-cdp.log 2>&1 &
```

Three details that are not optional:

- **A separate `--user-data-dir` is required.** Chrome refuses `--remote-debugging-port` on the
  default profile. A dedicated directory also keeps you out of the person's working browser.
- **Use a stable path** (`~/.cache/…`, not the session scratchpad in `/tmp`): the profile persists,
  so the sign-in survives between sessions and the person does not authenticate again next time.
- **Pass the final URL on the command line.** The auth provider redirects to its sign-in page with a
  return parameter and lands the person on the right route afterwards, removing a navigation step.

### Confirm the endpoint is up, before anything else

```bash
curl -s --max-time 5 http://127.0.0.1:9222/json/version    # must return the browser's JSON
curl -s http://127.0.0.1:9222/json/list | python3 -c "
import json,sys
for t in json.load(sys.stdin):
    if t.get('type')=='page': print(t.get('title','')[:60],'|',t.get('url','')[:90])"
```

A tab whose title is the sign-in page means the person has not signed in yet — **stop and ask**;
do not try to authenticate on your own.

### Attach

```bash
bunx agent-browser --cdp 9222 get url      # must NOT be the sign-in URL
bunx agent-browser --cdp 9222 snapshot -i -c
bunx agent-browser --cdp 9222 screenshot <abs-path>.png
```

Or `bunx agent-browser connect 9222` once, then commands without the flag.
`agent-browser get cdp-url` prints the live endpoint of the current session.

### `[HARD]` Never `close` while attached over CDP

`bunx agent-browser close` / `close --all` kills the person's real browser and their signed-in
session with it. Over CDP, cleanup is **doing nothing** — the browser stays up for the next
verification. That holds even in step 6 of the verification protocol below, which assumes Option A.

### Writing to a staging environment

Assume a staging write reaches production data unless the project states otherwise — plenty of
setups share one database. On an authenticated route the default is to **observe**: open, snapshot,
read, cancel. Confirming a mutation — moving, saving, deleting — needs an explicit request from the
person in the current turn.

---

## Option C — Persistent profile

```bash
bunx agent-browser --profile <project>-staging open ${project.stagingUrl}
# subsequent runs reuse cookies + localStorage from that profile
```

For credentials, use the auth vault rather than profile state.

### Authenticated routes — the rule that matters

**The person signs in; the agent attaches.** Never automate a login flow: it puts credentials into
a transcript, it breaks on every consent banner and OAuth redirect, and it is the single most
common way a verification run turns into an account lockout.

The working pattern, in order of preference:

1. **CDP attach** (Option B) — the person opens a browser with a debug port and signs in once; the
   agent attaches for the rest of the session. This is the canonical path for anything behind auth.
2. **Persistent profile** (Option C) — a named profile that keeps the session between runs. Useful
   when the same flow is verified repeatedly. The project names the profile in its own rules; this
   plugin does not invent one.
3. **Unauthenticated coverage only** — when neither is available, say so and verify what is
   reachable. A run that quietly skipped every authenticated route and reported success is worse
   than a run that reported half the surface honestly.

Whatever the path, `${project.stagingUrl}` comes from the config. A hardcoded host in a verification
script is a script that only ever verified one repository.

## Efficiency — what the CLI already does that most runs never use

Check each flag against the installed version's `--help` rather than trusting this list — the CLI
moves fast and a flag that vanished is a failed run.

### `batch` — by far the biggest win

Every `bunx agent-browser <cmd>` pays both the bunx and the CLI startup cost. A verification run is
8-15 invocations; `batch` runs them all in one process.

```bash
# Instead of 4 separate Bash calls:
bunx agent-browser --cdp 9222 batch \
  "get url" \
  "snapshot -i -c" \
  "screenshot .graph-powers/logs/flow.png" \
  "console"

# --bail stops at the first failure (default: runs them all and reports each)
# --json returns a JSON array, convenient for parsing result by result
```

The real limit: `batch` is sequential, not conditional. A `@ref`-based action only
goes into a batch **after** the snapshot that produced that ref — refs are invalidated by
every DOM mutation. The pattern that works: one batch to observe, read the refs,
then a second batch to act.

### `--auto-connect` — attach without knowing the port

```bash
bunx agent-browser --auto-connect get url     # finds the running Chrome and reuses its session
```

Useful when the browser was started by someone else and the port is unknown.

### Audits that are usually done by eye, and should not be

```bash
bunx agent-browser a11y --json          # axe-core: WCAG violations with selector and fix
bunx agent-browser vitals --json        # LCP/CLS/TTFB/FCP/INP plus a hydration summary
```

AA contrast is a hard floor (`safety-floor.md §8`) and used to be checked by eye. `a11y` does not
replace the Lighthouse run in `/perf`, which measures the deployed route — but it catches structural
violations immediately, on the page already open.

### React — for re-render defects

Requires `open --enable react-devtools`.

```bash
bunx agent-browser react renders start
# ... drive the interaction ...
bunx agent-browser react renders stop --json    # per-component re-render profile
bunx agent-browser react tree                   # component tree
bunx agent-browser react suspense --only-dynamic
```

This is the fastest way to confirm a suspected `memo()` or polling defect. Check the project's own
frontend notes in `${rulesDir}/` for the failure modes it has already recorded.

### Cheap reads

```bash
bunx agent-browser read <url>     # agent-readable text — far cheaper than a snapshot
bunx agent-browser get text <sel> # a single element
```

Use `read` when the question is about CONTENT. `snapshot -i -c` only when you need refs to
interact.

### Mocking without Playwright

```bash
bunx agent-browser network route "**/api/trpc/*" --body '{"result":{"data":null}}'
bunx agent-browser network route "**/analytics/*" --abort
bunx agent-browser network unroute
```

### The official skill, matched to the installed version

```bash
bunx agent-browser skills get core --full
```

Prefer that to guessing flags: it ships with the binary, so it never drifts out of sync. This file
covers what a project has to decide — which environment, how authentication works, the CDP path, and
its own write policy; everything else is upstream.

---

## Verification protocol (canonical, used by `verification`)

Per flow:

```bash
# 1. Navigate
bunx agent-browser open <url>

# 2. Baseline
bunx agent-browser snapshot -i -c
bunx agent-browser screenshot <log-dir>/<flow>-initial.png

# 3. Drive the flow (snapshot before every interaction)
bunx agent-browser click @eN
bunx agent-browser snapshot -i -c
bunx agent-browser fill @eM "..."
bunx agent-browser wait --url "**/<expected>"

# 4. Evidence
bunx agent-browser screenshot <log-dir>/<flow>-final.png
bunx agent-browser console            # any error-level message → FAIL
bunx agent-browser errors             # uncaught errors → FAIL
bunx agent-browser network requests   # unexpected app 4xx/5xx → FAIL

# 5. Mobile breakpoint
bunx agent-browser set viewport 375 667
bunx agent-browser screenshot <log-dir>/<flow>-mobile.png
bunx agent-browser set viewport 1280 720

# 6. Cleanup
bunx agent-browser close
```

---

## Constraints

- **Snapshot before any ref-based interaction.** Refs invalidate on every DOM mutation (click that navigates, form submit, dialog open, dynamic re-render).
- **`set viewport` not `resize`.** There is no `resize` subcommand.
- **`console` / `errors` are continuous.** Call with `--clear` when you want per-flow isolation.
- **`network har` writes to disk.** Always pass an absolute path under `.graph-powers/logs/`.
- **Public routes:** a 401 from a session-probe request is allowed only when the page is intentionally unauthenticated; all other app 4xx/5xx need a concrete explanation or a fix.
- **Default target:** `${project.stagingUrl}` (from `.graph-powers/config.json::project.stagingUrl`). Never silently fall back to `localhost` when staging is unreachable — STOP and surface the error.
- **Auth:** prefer the auth vault (`agent-browser auth ...`) over passing credentials in shell args (shell history leaks).
- **Concurrent sessions:** use `--session <name>` to isolate parallel runs. Default session is `default`.

---

## Troubleshooting

| Symptom | First step |
|---|---|
| `agent-browser: command not found` | `bun add -d agent-browser` at repo root |
| Chrome download fails (corporate proxy) | Set `HTTPS_PROXY` env then `bunx agent-browser install`; or fall back to Option B with already-installed Chrome |
| `open` hangs | `bunx agent-browser doctor --fix` then retry |
| Stale refs after click | Always `snapshot -i` before the next ref-based action |
| Want to see the browser window | Add `--headed` |
| Need to debug page state | `bunx agent-browser inspect` opens DevTools |

---

## Loading the canonical agent-browser skill

The agent-browser CLI ships its own usage skill — load it for the full reference (covers tabs, auth vault, parallel sessions, cloud providers, etc.):

```bash
bunx agent-browser skills get core --full
bunx agent-browser skills list
```

These are version-matched to the installed binary, so prefer them over external docs.

---

## Playwright fallback (advanced features)

Playwright is a devDependency where a project needs it — check `package.json` before assuming it is
there. `bunx playwright install chromium --with-deps` downloads the browsers into the Playwright
cache (`~/.cache/ms-playwright` on Linux, `~/Library/Caches/ms-playwright` on macOS,
`%LOCALAPPDATA%\ms-playwright` on Windows) and is idempotent.

### When to reach for Playwright (not agent-browser)

- **Multi-browser parity** — agent-browser is Chrome/Lightpanda/iOS Safari only. Playwright covers Chromium + Firefox + WebKit.
- **Full test runner** — `playwright test` with fixtures, parallel sharding, retry, expect/assert, HTML reporter, JUnit/JSON output.
- **Codegen** — `bunx playwright codegen <url>` records human interaction into a script.
- **Trace viewer** — full timeline (DOM snapshots + network + console + actions) via `--trace on` + `bunx playwright show-trace trace.zip`.
- ~~Request interception with body rewrite~~ — **no longer a reason to switch**: agent-browser has `network route <url> --body <json>` and `--abort`. Go to Playwright only if you need to rewrite the body as a function of the original request.
- **Cross-context auth state** — `storageState.json` portable across runs and processes.
- **Video recording with audio** + frame-rate control.

For all other browser tasks, agent-browser is faster and more token-efficient.

### Critical Windows constraint

**Run Playwright scripts with `node`, not `bun run`.** Bun's Windows IPC has a known bug with the `--remote-debugging-pipe` channel Playwright uses for `chrome-headless-shell`, causing `TimeoutError: launch: Timeout 180000ms exceeded` on every launch. Symptom: process is `<launched>` but the pipe never returns. Fix: use Node.

```bash
# WRONG on Windows — hangs 180s then times out
bun run <your-playwright-script>.mjs

# RIGHT
node <your-playwright-script>.mjs
```

### Smoke script shape

A programmatic smoke worth keeping does four things and nothing else: launch headless, navigate to
`${project.stagingUrl}`, collect `consoleErrors[]` + `pageErrors[]` + `failedRequests[]` filtered to
the project's own origins, and write desktop + mobile screenshots into `.graph-powers/logs/`. It
exits with JSON so the caller can assert on it.

Keep it in the project's own `scripts/`, not here — the selectors and routes it touches belong to
that repository.

### Common tasks

```bash
# Install browsers (idempotent — skips if cached)
bunx playwright install chromium --with-deps

# Codegen — record interactions into a script
bunx playwright codegen ${project.stagingUrl}

# Run a test file with full trace
bunx playwright test e2e/auth.spec.ts --trace on

# View a saved trace
bunx playwright show-trace test-results/trace.zip

# Show browser version
bunx playwright --version
```

### Decision flow

```
Need to interact with a browser?
├─ Quick smoke / Bash-driven / ref-based?              → agent-browser CLI
├─ Session-bound bug (real cookies / extensions)?      → agent-browser --cdp <port> (Option B)
├─ Multi-browser parity (Firefox / WebKit)?            → Playwright (node)
├─ Structured test file with fixtures + assertions?    → Playwright test runner (bunx playwright test)
├─ Record interactions into a script?                   → bunx playwright codegen
└─ Full timeline trace for postmortem?                 → Playwright with --trace on
```
