## Section 0: Config Loader

Every command reads `.graph-powers/config.json` at start to resolve project-specific values. Pattern:

Read it with the **`Read` tool**, on `.graph-powers/config.json`. A file that is not there is the
"declares nothing" case, not an error — every default below still applies.

`test` and `cat` are the spelling this line used to carry, and cardinal 8 bans both: neither exists
on cmd.exe or PowerShell, so on Windows the config never loaded and every `${…}` resolved to
nothing, silently. Where a command genuinely needs the value inside a shell rather than in context:

```bash
python -X utf8 -c "import json,pathlib;p=pathlib.Path('.graph-powers/config.json');print(p.read_text(encoding='utf-8') if p.exists() else '{}')"
```

Substitution placeholders resolve at runtime by identity: `${project.name}` is `project.name`,
`${database.commands.status}` is `database.commands.status`, and so on for every field
`${CLAUDE_PLUGIN_ROOT}/schema/config.schema.json` declares. That schema is the list — a table of the
same names here is a second copy that stops matching it the first time a field is added. One
exception, because it is not identity: **`${rulesDir}` is `paths.rulesDir`**, defaulting to
`.claude/rules`.

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
