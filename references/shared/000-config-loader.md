## Section 0: Config Loader

At start, read `.graph-powers/config.json` with the **`Read` tool**. Missing means "declares
nothing", not an error; defaults still apply. Do not use shell `test` or `cat` — they are not
portable. Only when a value must enter a shell rather than context, use:

```bash
python -X utf8 -c "import json,pathlib;p=pathlib.Path('.graph-powers/config.json');print(p.read_text(encoding='utf-8') if p.exists() else '{}')"
```

Each config placeholder resolves to the schema field it names;
`${CLAUDE_PLUGIN_ROOT}/schema/config.schema.json` owns the complete field list. The sole alias is
`${rulesDir}` = `paths.rulesDir`, default `.claude/rules`.

Project rules and supplements live only under `${rulesDir}`. Tier-2 rules auto-load through narrow
`paths:` frontmatter; `globs:` is invalid and makes a rule effectively unscoped. Commands and
skills read supplements explicitly when needed. Root `AGENTS.md` remains the Tier-1 source for
identity, cardinals and constraints; `.graph-powers/logs/` is unversioned runtime state.
