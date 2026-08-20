---
name: webapp-testing
description: "Driving a real browser for evidence: E2E flows, screenshots, console and page errors, network traces. The stack is the agent-browser CLI, with local Playwright as fallback. Loaded by /debug frontend and by the verification agent. Not for unit tests."
license: Complete terms in LICENSE.txt
---

> Derived from `webapp-testing` in anthropics/skills (Apache-2.0, see `LICENSE.txt`). Modified by GrupoUS: the target URL is read from `project.stagingUrl` instead of being hardcoded, the browser stack is the `agent-browser` CLI, and the command reference is delegated to the CLI's own bundled skill instead of being mirrored here. Changes are listed in the NOTICE file at the root of the plugin.

# Web application testing

Primary stack: **`bunx agent-browser`**, invoked through Bash.

**The command reference is the CLI's own skill, not this file** — it ships with the binary and never
drifts out of sync:

```bash
bunx agent-browser skills get core --full
```

What this harness decides — target environment, named sessions, the CDP path for authenticated
routes, the staging-write policy, what counts as a failure, and when Playwright earns its place —
is in `references/browser-setup.md`.

## When to use

- Verifying a UI or user-flow change actually works in a browser (post-implementation E2E)
- Capturing evidence: screenshots, console errors, uncaught page errors, failed network requests
- Debugging rendered-DOM behaviour unit tests cannot reach — hydration, focus, viewport, reduced motion

**Not for:** unit or integration tests (`${tooling.commands.test}`), static code review, API-only
probes.

## The four things to get right

1. **Pre-flight.** `bunx agent-browser --version` — STOP and escalate if it fails.
2. **Your own session.** `bunx agent-browser session id --scope worktree --prefix task`, then pass
   `--session <that id>` on every command. The default session is shared with every agent on the
   machine, and working in it hijacks whatever page someone else left open.
3. **The core loop.** `open` → `snapshot -i -c` → act on `@eN` → **re-snapshot**. Refs are assigned
   fresh on every snapshot and die on any DOM change. A `@ref` action never shares a `batch` with
   the snapshot that produced it.
4. **One process, not six.** `bunx agent-browser batch --bail "open <url>" "snapshot -i -c" "screenshot <path>" "console" "errors" "network requests"` —
   each separate invocation pays the startup cost of both `bunx` and the CLI. `batch` is sequential,
   not conditional.

**Target:** `${project.stagingUrl}` from `.graph-powers/config.json`. Localhost only when asked, and
never as a silent fallback when staging is unreachable.

**Authenticated route:** the person signs in once into a browser with a debug port, the agent
attaches over `--cdp`. Never automate the sign-in. Recipe and the three traps:
`references/browser-setup.md § CDP attach`.

**`[HARD]` Never `close` over CDP** — it kills the person's real browser and their session. Headless
sessions end with `close --all`; a CDP session ends by doing nothing.

## Verdict

Any console message at error level, any uncaught page error, or an unexpected 4xx/5xx from the
application fails the run. Full rules, including the one acceptable 401:
`references/browser-setup.md § Verdict rules`.

## Local apps

`scripts/with_server.py` starts and stops a dev server around any automation command, browser-agnostic.
Run `--help` first and use it as a black box:

```bash
python scripts/with_server.py --server "bun dev" --port 5173 -- bunx agent-browser open http://localhost:5173
```

## Common pitfalls

- Acting on a stale `@ref` after a DOM mutation → re-snapshot first
- Inspecting a single-page app before `wait --load networkidle` → empty or partial DOM
- `close` in CDP mode → kills the person's Chrome session
- Falling back to localhost silently when staging is unreachable → stop and escalate
- Running in the default session → you are sharing a browser with every other agent on the machine
