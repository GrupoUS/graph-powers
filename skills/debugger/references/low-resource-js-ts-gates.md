# Low-resource JavaScript/TypeScript gates

Use this guide when configuring a host repository or explaining why the debugger's JS/TS gate
resolver rejected a command. It is the rationale behind
`${CLAUDE_PLUGIN_ROOT}/references/shared/130-bun-tsgo-gates.md`; that resolver owns execution
policy, while this file owns setup and migration detail.

## Supported default

Install the native preview locally and pin the version the project has verified:

```bash
bun add --dev --exact @typescript/native-preview@7.0.0-dev.20260707.2
```

The version above was the last `latest` native-preview build observed on 2026-08-25. It is frozen
because TypeScript 7 stable moved the native compiler back to the executable name `tsc`. Graph
Powers deliberately keeps `tsgo` as the unambiguous no-legacy channel; do not upgrade this pin
without checking the registry and the project's diagnostics.

Type-check with one checker worker and no network fallback:

```bash
bunx --bun --no-install --package @typescript/native-preview tsgo --noEmit -p tsconfig.json --checkers 1
```

Every flag is intentional:

- `--bun` ignores the package's `#!/usr/bin/env node` shebang and runs its launcher with Bun;
- `--no-install` prevents a verification gate from fetching code from the registry;
- `--package @typescript/native-preview` disambiguates the `tsgo` executable;
- `--checkers 1` avoids TypeScript 7's default pool of four checker workers and duplicated work.

For a machine under severe pressure, `--singleThreaded` is stricter than `--checkers 1`, but it is
an explicit project choice: it also serializes parsing and emit and can increase wall-clock time.

## Tests

Use one process and ask Bun to trade some throughput for a smaller heap:

```bash
bun test --smol
```

During an edit/fix loop, run only tests reachable from Git changes and stop on the first failure:

```bash
bun test --changed --bail=1 --smol
```

Run the serial full suite once at the phase or final boundary. Do not repeat it after every task.

`bun test --parallel` is not a low-resource default. Bun 1.4 starts up to one worker process per CPU
core and implies per-file isolation. If a measured suite genuinely benefits, cap it explicitly:

```bash
bun test --parallel=2
```

Likewise, `--concurrent` needs `--max-concurrency=2`. That flag controls async tests inside a file;
it does not cap `--parallel` worker processes.

## Commands the plugin refuses

- `node --test` and `node.exe --test`;
- direct `tsc`, `npx tsc`, `bunx tsc`, package scripts named `tsc`, and Node launchers into
  `node_modules/typescript/bin/tsc`;
- bare `tsgo`, because the npm package launcher has a Node shebang;
- unbounded `bun test --parallel` or a bound above two;
- `bun test --concurrent` without `--max-concurrency=2`, or with a higher bound.

A missing local package is `NEEDS-WORK`. Never replace it with a network install during the gate,
legacy `tsc`, or Node's test runner.

Graph Powers' verification gates run ESM installers and static workflow checkers through Bun 1.4.
The installer remains Node-compatible for users who need that runtime, but agents and CI do not use
Node as a test executor.

## Compatibility boundary

As of TypeScript 7.0 (2026-07-08), the native compiler is production-ready for CLI type-checking,
but the stable programmatic API was not yet available. Framework checkers that embed TypeScript —
including Astro, Vue, Svelte, MDX and Angular tooling — may still require their own declared command.
Do not silently replace a framework checker with tsgo; run the declared framework gate through Bun
and use tsgo only where its CLI diagnostics are a valid proof for that project.

## Official sources

- TypeScript 7 release, performance, memory and `--checkers`/`--singleThreaded`:
  https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/
- Native-preview package and `tsgo` status: https://github.com/microsoft/typescript-go
- Bun test runner: https://bun.com/docs/test
- Bun parallel workers and isolation: https://bun.com/docs/test/parallel
- Bun test memory flag: https://bun.com/docs/test/runtime-behavior
- Bun shebang behavior and `bunx --bun`: https://bun.com/docs/pm/bunx
