---
name: webapp-testing
description: "Driving a real browser for evidence: E2E flows, screenshots, console and page errors, network traces. The stack is the agent-browser CLI, with local Playwright as fallback. Loaded by /verify and /debug frontend. Not for unit tests."
license: Complete terms in LICENSE.txt
---

> Derived from `webapp-testing` in anthropics/skills (Apache-2.0, see `LICENSE.txt`). Modified by GrupoUS: the target URL is read from `project.stagingUrl` instead of being hardcoded, and the browser stack is the `agent-browser` CLI. Changes are listed in the NOTICE file at the root of the plugin.

# Web Application Testing

Primary browser stack: **`bunx agent-browser`** (the vercel-labs CLI, invoked through Bash). Full command reference, headless versus `--cdp` attach for authenticated routes, snapshot and ref semantics, and troubleshooting: `references/browser-setup.md`.

Default target: `project.stagingUrl` from `.graph-powers/config.json` (`${project.stagingUrl}`). Use localhost only when explicitly requested.

**Authenticated routes:** when the target sits behind authentication, the path that works is a CDP
attach — start a browser with its own profile on a debug port, the person signs in once, and the
session persists between runs. The exact command and the three traps are in
`references/browser-setup.md § Option B`. If `curl -s http://127.0.0.1:<port>/json/version` does not
answer, the browser is not up: start it and **ask for the sign-in** — never try to authenticate on
your own.

## When to Use

- Verifying a UI/user-flow change actually works in a browser (post-implementation E2E)
- Capturing evidence: screenshots, console errors, uncaught page errors, failed network requests
- Debugging rendered-DOM behavior that unit tests can't reach (hydration, focus, viewport, reduced-motion)

**Not for:** unit/integration tests (vitest via `bun run test`), static code review, API-only probes (`curl`).

## Quick Reference

Pre-flight: `bunx agent-browser --version` — STOP and escalate if it fails.

| Task | Command |
|---|---|
| Open page | `bunx agent-browser open <url>` (add `--headless` for public pages) |
| **Several commands at once** | `bunx agent-browser batch "get url" "snapshot -i -c" "screenshot <path>"` — one process instead of N. The single biggest time saving available; `--bail` stops at the first failure |
| Read content only, no interaction | `bunx agent-browser read <url>` — far cheaper than `snapshot` |
| Accessibility / Core Web Vitals audit | `a11y --json` · `vitals --json` (axe-core and CWV built in) |
| React re-render profile | `open --enable react-devtools` → `react renders start` … `react renders stop --json` |
| Authenticated route — **the canonical path** | Start the browser once, the person signs in, then `bunx agent-browser --cdp <port> <cmd>`. Full recipe: `references/browser-setup.md § Option B`. **Never `close` while attached over CDP.** |
| Inspect interactive elements | `bunx agent-browser snapshot -i -c` (re-snapshot before EVERY ref action — refs go stale on DOM change) |
| Interact | `click @eN` · `fill @eN "..."` · `type @eN "..."` · `select @eN "v"` · `press Tab` |
| Wait | `wait @ref` · `wait --text "..."` · `wait --url "**/glob"` · `wait --load networkidle` (avoid bare `wait <ms>`) |
| Evidence | `screenshot <path>` · `console` · `errors` · `network requests --filter "api-staging"` |
| Viewport / media | `set viewport 375 667` (mobile) · `set media reduce-motion` |
| Cleanup | `close --all` (headless sessions only) |

## Canonical smoke flow

One `batch`, not six calls — each invocation pays the startup cost of both `bunx` and the CLI.

```bash
bunx agent-browser batch --bail "open ${project.stagingUrl}/<route>" "snapshot -i -c" "screenshot .graph-powers/logs/<flow>.png" "console" "errors" "network requests --filter api-staging"
bunx agent-browser close --all       # headless sessions ONLY — never over CDP
```

Verdict: any console message at error level → FAIL · any uncaught page error → FAIL · an unexpected
4xx/5xx from the application → FAIL (a 401 on an auth probe is acceptable only on a route that is
deliberately unauthenticated).

On an authenticated route, swap `open` for `--cdp 9222` and **drop the `close`**.
A `@ref`-based action never goes in the same batch as the snapshot that produced it — refs go stale
on every DOM mutation.

## Local apps (server lifecycle)

`scripts/with_server.py` starts/stops dev servers around any automation command (browser-agnostic). Run `--help` first; use as black box:

```bash
python scripts/with_server.py --server "bun dev" --port 5173 -- bunx agent-browser open http://localhost:5173
```

## Playwright fallback (advanced only)

Playwright, installed as a devDependency where the project needs it, covers what agent-browser can't: multi-browser parity (Firefox/WebKit), structured test runner with fixtures, codegen, traces. **Run scripts with `node`, never `bun run`** (Bun Windows IPC bug times out chrome-headless-shell). The `examples/*.py` here are Python-Playwright patterns kept as a fallback reference, not the default path. Details: `references/browser-setup.md § Playwright fallback`.

## Common Pitfalls

- Acting on a stale `@ref` after DOM mutation → re-snapshot first
- Inspecting a SPA before `wait --load networkidle` → empty/partial DOM
- `close` in CDP mode → kills the user's real Chrome session
- Falling back to localhost silently when staging is unreachable → STOP and escalate instead
