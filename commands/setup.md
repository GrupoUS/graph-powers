---
description: "Diagnose the local Oxc (Oxlint/Oxfmt), TypeScript 7, vtsls and Zed setup without changing the machine. Use when the user asks to configure or check project toolchain, editor diagnostics, format-on-save or competing linters and formatters. Reports missing tools and compatibility blockers, then prints local package-manager commands and a portable project-settings example. Never installs packages or edits global editor settings."
workflow_type: augmented-llm
---

# /setup — Oxc, TypeScript 7 and Zed diagnostics

**ARGUMENTS**: $ARGUMENTS

This command is diagnostic-only. Do not install packages, write a config, modify global Zed
settings, start a watcher, or run a whole-project lint/type analysis. Read the repository's nearest
`AGENTS.md`, `.graph-powers/config.json`, lockfile names, `package.json` and `.zed/settings.json` if
they exist. Use the project root from the current session; do not assume a package manager.

## 1. Collect one bounded local report

Run one read-only probe. It may inspect files and versions but must not invoke an install:

```text
python -X utf8 -c "import json,platform,shutil; from pathlib import Path; root=Path.cwd(); locks={'bun':['bun.lock','bun.lockb'],'pnpm':['pnpm-lock.yaml'],'yarn':['yarn.lock'],'npm':['package-lock.json','npm-shrinkwrap.json']}; pm=next((name for name,names in locks.items() if any((root/n).is_file() for n in names)), 'unknown'); p=root/'package.json'; raw=json.loads(p.read_text(encoding='utf-8')) if p.is_file() else {}; pkg=raw if isinstance(raw,dict) else {}; dep_groups=[pkg.get('dependencies',{}),pkg.get('devDependencies',{})]; deps={k:v for group in dep_groups if isinstance(group,dict) for k,v in group.items()}; paths={'typescript':root/'node_modules/typescript/package.json','oxfmt':root/'node_modules/oxfmt/package.json','oxlint':root/'node_modules/oxlint/package.json'}; local={name:path.is_file() for name,path in paths.items()}; versions={name:(json.loads(path.read_text(encoding='utf-8')).get('version') if path.is_file() else None) for name,path in paths.items()}; tools={name:shutil.which(name) is not None for name in ('bun','node','oxlint','oxfmt','vtsls','zed')}; competitor_markers=('eslint','prettier','dprint','stylelint'); competitors=sorted(name for name in deps if any(marker in name.lower() for marker in competitor_markers)); print('OS:', platform.system(), platform.release()); print('package-manager:', pm); print('declared:', {name:deps.get(name,'NOT DECLARED') for name in paths}); print('local package manifests:', local); print('local versions:', versions); print('PATH tools:', tools); print('Zed project settings:', (root/'.zed/settings.json').is_file()); print('possible competing packages:', competitors or []); print('tooling configs:', sorted(str(p.relative_to(root)) for p in root.glob('*.config.*') if p.name.startswith(('vite.','vitest.','astro.','next.','svelte.','nuxt.')))); print('test/runtime hints:', {name:any(name in deps for name in names) for name,names in {'jsdom':('jsdom',),'happy-dom':('happy-dom',),'playwright':('@playwright/test','playwright'),'turbo':('turbo',),'vitest':('vitest',)}.items()})"
```

Interpret each item as `PASS`, `MISSING` or `NEEDS-WORK`. A PATH binary is not proof of the
project-local version: prefer `node_modules` and the lockfile. A declared package with no local
install is `MISSING`; do not repair it automatically.

For TypeScript, require the declared stable local major version 7 package. A pre-release or PATH-only
tool is `NEEDS-WORK`. The canonical low-resource final gate is:

```text
oxlint --type-aware --type-check --threads 1
```

When memory is constrained, keep the single Oxlint worker and narrow the project command. A missing
package is a setup problem, never a reason to fall back to a global tool or network launcher.

Zed currently defaults TypeScript, TSX and JavaScript to `vtsls`. Its adapter expects `tsserver.js`
when using a workspace SDK, while TypeScript 7 no longer ships that entrypoint. Keep
`vtsls.autoUseWorkspaceTsdk` set to `false`, report `BLOCKED: vtsls + local TypeScript 7`, and do not
add a second TypeScript server. The local TypeScript 7 package remains available to the explicit
Oxlint final gate.

## 2. Inspect project settings without writing

If `.zed/settings.json` exists, parse it and check:

- `languages.JavaScript` (including JSX), `languages.TypeScript` and `languages.TSX` list
  exactly `vtsls` and `oxlint`, with no second TypeScript provider;
- those language blocks use exactly one Oxfmt language-server formatter and `format_on_save: "on"`;
- JSON, JSONC and CSS also use the Oxfmt language-server formatter;
- `lsp.vtsls.settings.vtsls.autoUseWorkspaceTsdk` is `false` and no `tsdk` points at the local TypeScript 7 package;
- `lsp.oxlint.initialization_options.settings.typeAware` is `false` and `run` is `onSave` or `onType`;
- `file_scan_exclusions` includes `node_modules`, `.git`, `dist`, `build`, `.build`, `.turbo`,
  `.cache`, `.bun`, `.next`, coverage and generated artifacts;
- no competing formatter, second linter or second TypeScript server is active in those blocks.

If it is absent or fails a check, print the portable project example at
`${CLAUDE_PLUGIN_ROOT}/templates/zed/settings.json`. Do not write it. It is a project file, not a
global Zed change. The Oxc Zed extension launches the project-local `oxfmt --lsp` formatter and
`oxlint --lsp`; no package-fetching command belongs in editor settings.

## 3. Inspect test compatibility

If `vite.config.*`, `vitest.config.*`, `vitest`, `jsdom`, `happy-dom`, Playwright, aliases, mocks,
snapshots, browser mode or Vite plugins are present, preserve Vitest and its project configuration.
The low-resource edit loop is:

```text
vitest run --changed --maxWorkers=1 --no-file-parallelism
```

Do not add `threads`, `forks`, `--no-isolate` or global parallelism without a measured compatibility
need. Use Bun Test only for a pure unit-test package that explicitly declares it:

```text
bun test --smol --bail=1
```

The final Bun gate is `bun test --smol`; concurrent tests must state `--max-concurrency=2`. Do not
replace `bun run test` with a bare `bun test` when that would ignore a Vitest config, aliases, setup,
mocks, snapshots or plugins. Check the installed Bun version before depending on `--changed`.

## 4. Print only local install suggestions

Use the detected lockfile. The explicit `--setup-oxc` helper may install these project-local
packages once after the operator chooses it; this diagnostic command never installs them:

```text
Bun:   bun add -d oxlint oxfmt typescript@7
npm:   npm install -D oxlint oxfmt typescript@7
pnpm:  pnpm add -D oxlint oxfmt typescript@7
Yarn:  yarn add --dev oxlint oxfmt typescript@7
```

Zed's `vtsls` and the Oxc extension are editor integrations; do not add a second TypeScript server
just to make the local gate runnable. Type-aware Oxlint is a final signal only:

```text
oxlint --type-aware --type-check --threads 1
```

Run it only at `/verify`, commit or CI, never in Zed, PostToolUse, Stop or an edit loop. Oxfmt is
the sole formatter; Oxlint is the interactive syntax/correctness diagnostic provider.

Finish with this checklist:

```text
[ ] local TypeScript 7 package
[ ] local oxfmt
[ ] local oxlint
[ ] one vtsls TypeScript provider
[ ] one Oxlint diagnostic provider with typeAware=false
[ ] one Oxfmt language-server formatter with format_on_save
[ ] Zed exclusions
[ ] Vitest configuration preserved when present
[ ] no competing formatter or lint provider
```

State every unchecked item and its suggested local command. A compatibility blocker stays visible
even when all packages are present.

## References

- `${CLAUDE_PLUGIN_ROOT}/references/shared/130-typescript7-oxc-gates.md`
- `${CLAUDE_PLUGIN_ROOT}/templates/zed/settings.json`
- Zed TypeScript: https://zed.dev/docs/languages/typescript
- Zed language configuration: https://zed.dev/docs/configuring-languages
- Oxlint: https://oxc.rs/docs/guide/usage/linter
- Oxfmt: https://oxc.rs/docs/guide/usage/formatter.html
- Oxlint editor setup: https://oxc.rs/docs/guide/usage/linter/editors.html
- Oxfmt editor setup: https://oxc.rs/docs/guide/usage/formatter/editors.html
