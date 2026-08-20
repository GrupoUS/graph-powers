## Section 1: Quality Gates

| Timing | Gates |
|---|---|
| After each task | type-check |
| After each phase | type-check + lint |
| Final | type-check + lint + tests |

```bash
# Resolve from config
${tooling.packageManager} run ${tooling.typeChecker}    # or `bunx tsgo`, `npx tsc --noEmit`, etc.
${tooling.packageManager} run lint                       # or direct: `bunx biome check`, `eslint .`
${tooling.packageManager} run test                       # only when test runner configured
```

> **Pre-commit:** run formatter+linter on every manually edited file. Most linters (`biome`, `eslint`) treat errors as build-breaking — they fail CI immediately.
