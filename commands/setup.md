---
description: "Diagnose local Oxc, TypeScript 7, vtsls and Zed setup without changing the machine. Reports blockers and local install suggestions; never installs packages or edits settings."
workflow_type: augmented-llm
---

# /setup

**ARGUMENTS:** $ARGUMENTS. Diagnostic-only: read nearest `AGENTS.md`, config, lockfiles, `package.json` and `.zed/settings.json` when present; do not install, write config, alter global Zed, start a watcher, or run full-project analysis.

## 1. Inspect

Identify package manager from lockfile; report declared and installed local TypeScript, Oxlint and Oxfmt, their versions, PATH tools, Zed settings, competitors and test/runtime hints. Prefer `node_modules` and lockfile evidence over PATH. Report each as PASS, MISSING or NEEDS-WORK. TypeScript requires declared stable local major 7; PATH-only or prerelease is NEEDS-WORK. The final low-resource gate is `oxlint --type-aware --type-check --threads 1`, never an edit-loop/editor hook.

## 2. Zed and tests

If settings exist, require JavaScript/TypeScript/TSX to use exactly vtsls + Oxlint, one Oxfmt formatter with format-on-save, Oxfmt for JSON/JSONC/CSS, exclusions for generated/vendor paths, `typeAware=false`, and no competing formatter/linter/TypeScript provider. `vtsls.autoUseWorkspaceTsdk` stays false and no `tsdk` points to TypeScript 7: vtsls expects `tsserver.js`, which TS7 lacks. Missing/nonconforming settings print `${CLAUDE_PLUGIN_ROOT}/templates/zed/settings.json`; do not write it.

Preserve existing Vitest/Vite configuration. Recommend `vitest run --changed --maxWorkers=1 --no-file-parallelism`; use `bun test --smol --bail=1` only for a pure package that declares Bun Test. Never replace a configured `bun run test` with bare Bun Test.

## 3. Suggestions

Print only detected-package-manager local commands for an operator to run: `bun add -d`, `npm install -D`, `pnpm add -D`, or `yarn add --dev` with `oxlint oxfmt typescript@7`. Finish with unchecked local TS7/Oxfmt/Oxlint, one vtsls, one Oxlint diagnostic, one Oxfmt formatter, exclusions, preserved test config, and no competitors. Keep blockers visible even when packages exist.
