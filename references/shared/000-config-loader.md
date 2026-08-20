## Section 0: Config Loader

Every command reads `.graph-powers/config.json` at start to resolve project-specific values. Pattern:

```bash
# read config (commands invoke via Bash or Read)
test -f .graph-powers/config.json && cat .graph-powers/config.json
```

Substitution placeholders used in commands (resolve at runtime):

| Placeholder | Source field |
|---|---|
| `${project.name}` | `project.name` |
| `${project.stagingUrl}` | `project.stagingUrl` |
| `${project.locale}` | `project.locale` |
| `${paths.backendRoot}` | `paths.backendRoot` |
| `${paths.frontendRoot}` | `paths.frontendRoot` |
| `${paths.schemaRoot}` | `paths.schemaRoot` |
| `${paths.libRoot}` | `paths.libRoot` |
| `${paths.componentsRoot}` | `paths.componentsRoot` |
| `${tooling.packageManager}` | `tooling.packageManager` |
| `${tooling.buildTool}` | `tooling.buildTool` |
| `${tooling.typeChecker}` | `tooling.typeChecker` |
| `${tooling.linter}` | `tooling.linter` |
| `${tooling.testRunner}` | `tooling.testRunner` |
| `${gates.lighthouse.*}` | `gates.lighthouse.*` |
| `${gates.lcp/cls/inp/initialJsKb}` | `gates.*` |
| `${rulesDir}` | `paths.rulesDir` (defaults to `.claude/rules`) |

**Rule layer.** All project rules + supplements live under `${rulesDir}`. No overlay folder, no overlay-first resolution. Tier 2 rules auto-load via `paths:` frontmatter; supplements are read on demand, by explicit path, from the command or skill that needs them:

> The field is `paths:`, not `globs:` — a rule written with `globs:` has no `paths:` field, and **a rule with no `paths:` field loads unconditionally into every session**, at the same priority as `.claude/CLAUDE.md`. So the typo does not fail loudly; it silently converts a scoped rule into an always-on one, which is the opposite of what it was written for. Reading a supplement by explicit path works either way, so give every supplement a narrow `paths:` and let the command that needs it read it directly.

| File | Purpose |
|---|---|
| `${rulesDir}/routing-supplements.md` | Project-specific routing matrix rows (loaded by `/prime`, `/implement`) |
| `${rulesDir}/verify-supplements.md` | Project-specific smoke tests (loaded by `/verify`) |
| `Skill("debugger")` → `${CLAUDE_PLUGIN_ROOT}/skills/debugger/references/anti-patterns.md` | Project-specific bug patterns + Negative Constraints index |
| `Skill("planning")` → `${CLAUDE_PLUGIN_ROOT}/skills/planning/references/layer-map.md` | Project-specific layer map for sprint phase ordering |
| `Skill("senior-architect")` | Project orientation: architecture map, runtime shape, trade-off analysis |
| `.graph-powers/logs/` | Runtime state: session counters, write lease, progress log, learnings (never versioned) |

Project identity, cardinal rules, and constraints live in **root `AGENTS.md`** (always loaded as Tier 1).
