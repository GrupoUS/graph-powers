# Issue 27 — runtime smoke evidence

User explicitly authorized synthetic Codex Astra/high and Luna/medium|max and at most one paid
Jev call. This does not authorize credential changes or fallback/retry.

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

Jev integration: NOT RUN — AI_GATEWAY_API_KEY absent from the process environment. Zero paid
requests sent. Do not discover credentials automatically or substitute a chat endpoint. A future
single authorized synthetic evaluation must use the public adapter; local replay must send no
network request. Native-economic and native-ultra runtime activation are NOT RUN; no top-level
profile was installed.
