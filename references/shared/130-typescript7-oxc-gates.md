# JavaScript/TypeScript gates: Oxc + Zed

This is the single shared policy for JavaScript and TypeScript repositories. `/verify`, commit,
CI, the debugger and the setup diagnostics read this contract.

## One owner per editor concern

- `vtsls` is the only TypeScript language server. It owns types, completion, navigation, aliases,
  project references, JSX and TSX support.
- `oxlint --lsp` is the only JavaScript/TypeScript diagnostic provider. Its type-aware mode stays
  off during editing.
- `oxfmt --lsp` is the only formatter for JavaScript (including JSX), TypeScript, TSX, JSON, JSONC
  and CSS.
  Zed uses the formatter language server from the official Oxc extension.
- These tools are project-local. Hooks, editor settings and package scripts never fetch packages at
  startup, on save or while an edit is in progress.

## TypeScript 7 and the vtsls compatibility boundary

The project declares stable `typescript@7` for the local final toolchain. Current Zed's vtsls
adapter, however, selects a workspace SDK only when it exposes the legacy `tsserver.js` entrypoint;
TypeScript 7 no longer ships that file. The portable template therefore keeps vtsls as the sole
provider but leaves `autoUseWorkspaceTsdk` disabled and does not point it at the TypeScript 7
directory. This is an explicit compatibility blocker, not a reason to add a second server:

```text
BLOCKED: vtsls + local TypeScript 7 — the current Zed adapter requires tsserver.js.
```

`/setup` must report this state honestly. When the adapter supports the TypeScript 7 SDK, the one
vtsls setting can be changed; until then, vtsls uses its bundled compatible SDK and the local
TypeScript 7 package is reserved for the final Oxc gate.

## Oxc diagnostics and final typed lint

Oxlint's editor LSP is the fast syntax and correctness signal. Do not run typed analysis in Zed,
PostToolUse, Stop or a repair loop. Type-aware Oxlint is a bounded final signal only:

```text
oxlint --type-aware --type-check --threads 1
```

It may run at `/verify`, commit or CI. It must receive the project's declared configuration and
never a whole-tree fallback from an interactive hook.

## Hook boundary

- PostToolUse runs one local `oxfmt --write` operation for the edited JS/TS/JSON file only. It has a
  short timeout, no watcher, no daemon and no persistent result cache; failures are fail-open.
- Stop runs local Oxlint only for existing changed JS/TS paths. It never runs a full-tree command,
  typed Oxlint, a package-fetching launcher or an unbounded fallback; failures are fail-open.
- Package scripts may provide the final typed gate, but the hook must inspect the script before
  launching it and reject type-aware commands outside `/verify`, commit or CI.

## Zed project settings

Use the template at `templates/zed/settings.json`:

- exclude `.git`, dependency, build, cache, coverage and generated directories;
- use exactly `vtsls` and `oxlint` for JavaScript and TypeScript diagnostics;
- use exactly one `oxfmt` formatter with `format_on_save: "on"`;
- disable automatic TypeScript acquisition and competing formatters;
- do not add another TypeScript language server or an external package-fetching formatter.

Official references:

- Oxlint: https://oxc.rs/docs/guide/usage/linter
- Oxfmt: https://oxc.rs/docs/guide/usage/formatter.html
- Oxlint LSP: https://oxc.rs/docs/guide/usage/linter/editors.html
- Oxfmt editors: https://oxc.rs/docs/guide/usage/formatter/editors.html
- Zed TypeScript: https://zed.dev/docs/languages/typescript
- Zed language settings: https://zed.dev/docs/configuring-languages
- TypeScript 7 announcement: https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/
