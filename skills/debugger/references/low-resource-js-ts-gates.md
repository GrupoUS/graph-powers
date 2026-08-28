# Low-resource JavaScript/TypeScript gates

Use this guide when configuring a host repository or explaining why an interactive JavaScript or
TypeScript gate was rejected. The executable policy lives in
`${CLAUDE_PLUGIN_ROOT}/references/shared/130-typescript7-oxc-gates.md`.

## Editor and final boundaries

- `vtsls` is the only TypeScript language server. Current Zed cannot use the TypeScript 7 workspace
  SDK because its adapter requires `tsserver.js`; keep its bundled compatible SDK and report the
  blocker instead of adding another server.
- `oxlint --lsp` is the only interactive diagnostic provider, with type-aware mode disabled.
- `oxfmt --lsp` is the only formatter and runs on save; PostToolUse runs one local `oxfmt --write`
  operation for one edited file.
- Type-aware Oxlint is a final signal only:

  ```text
  oxlint --type-aware --type-check --threads 1
  ```

  Run it only at `/verify`, commit or CI. Hooks and fix loops never run it.

## Hook resource floor

PostToolUse and Stop are changed-file-only, single-process, short-timeout and fail-open. They do not
start watchers or daemons, fetch packages, run whole-tree fallbacks or keep a persistent result
cache. A missing local executable is reported as unavailable; installing it is never a hook side
effect.

Preserve the project's declared test runner and its configuration. Run focused tests during a fix
loop and the full suite once at the final boundary. Do not replace a project's runner merely to
reduce resource use.

## Sources

- TypeScript 7: https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/
- Zed TypeScript: https://zed.dev/docs/languages/typescript
- Zed language settings: https://zed.dev/docs/configuring-languages
- Oxlint LSP: https://oxc.rs/docs/guide/usage/linter/editors.html
- Oxfmt formatter: https://oxc.rs/docs/guide/usage/formatter/editors.html
