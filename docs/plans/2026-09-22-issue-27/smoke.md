# Issue 27 — runtime smoke evidence

User explicitly authorized synthetic Codex Astra/high and Luna/medium|max and at most one paid
Jev call. A later user request explicitly authorized storing the supplied gateway key and enabling local evaluation; fallback/retry remain forbidden.

Codex CLI 0.155.1; existing native installation and authentication, ephemeral sessions, disposable
working directory, read-only sandbox. Synthetic prompt asks for ISSUE27_SMOKE_OK without tools,
file reads, browsing or agents. No global model configuration was changed.

Command form: `codex exec --ephemeral --sandbox read-only --skip-git-repo-check --cd <temporary-directory> --model <model> -c 'model_reasoning_effort="<effort>"' <synthetic-prompt>`.

| Model | Effort | Exit | Observed |
|---|---|---|---|
| gpt-6-astra | high | 0 | Runtime header matches; response ISSUE27_SMOKE_OK |
| gpt-6-luna | medium | 0 | Runtime header matches; response ISSUE27_SMOKE_OK |
| gpt-6-luna | max | 0 | Runtime header matches; response ISSUE27_SMOKE_OK |

Logs: `.graph-powers/logs/issue-27/smoke/`. These prove the requested model/effort accepts a real
Codex turn; native/clone checker separately proves the twelve generated role resolutions. They
are not a benchmark or proof that a previously opened Desktop session reloaded its roles.

Jev integration: PASS on 2026-09-22, after explicit user authorization to configure the supplied
credential globally and enable evaluation locally. Credential exists only in the native Codex
shell environment settings (mode 0600); no value is stored in the repository or sent to GitHub.

One real adapter evaluation returned HTTP 200, model `typesafe-ai/jev`, choice `inspect`,
probabilities `inspect: 0.99`, `review: 0.01`, and generation `gen_01M35CX4EN28NX7R9VHKQ0XHCR`.
The gateway reported 422 input and 31 output tokens. This is observed usage, not a pricing promise.
Replay used an empty credential environment and a rejecting transport: same recorded result,
zero fetch calls. Real request count: exactly one. No chat endpoint, fallback, retry or automatic spawn.
Evidence: `.graph-powers/logs/issue-27/gateway-activation/live-result.json` and durable attempt marker.
Native-economic/Ultra runtime remains NOT RUN; those optional profiles were not activated.

## Full coordination smoke — 2026-09-22

A later explicit user authorization allowed two additional synthetic Jev evaluations, no retries.
Both returned HTTP 200 from `/v1/evaluate`, model `typesafe-ai/jev`:

1. `agent:verification` probability 1.0 vs frontend-specialist 0.0, generation
   `gen_01M35HCCHJT7QFYW5759CNJ6PP` (697 input /45 output tokens).
2. After the native agent returned and main independently verified the result, `finish` probability
   0.98 vs verification 0.02 and frontend-specialist 0, generation
   `gen_01M35HK5ZBGT7605T45DSSH5TG` (963 input /48 output tokens).

The selected native verification role loaded webapp-testing and drove a real Chrome browser on a
synthetic local counter: visible 0→1, keyboard focus visible, HTTP200, no page/console/network errors.
Main independently checked the rendered transition/focus and captured a screenshot, then recorded
the handoff; the originally approved `bun check.mjs` gate exited 0. Persistent status became
COMPLETED after Jev's second choice. Offline replay used no credential and a rejecting transport,
returned COMPLETED without execution permission, and retained exactly two attempt markers.

Evidence: `.graph-powers/logs/issue-27/coordination-live/` (request/response records, return,
replay and browser.png). No source/history/credential was sent; only synthetic request, canonical
choices and bounded result summary. This proves this real route/return cycle; it does not benchmark
speed or prove every plugin method, product UI or responsive viewport. Other skill/command routes,
failed gates, stale snapshots, linked plans, duplicate and resumed decisions use local fixtures.
