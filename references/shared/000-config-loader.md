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

`codeGraph.provider` is project-only: absent/invalid → `code-review-graph`, explicit `graft` →
Graft, `none` → text. Ignore user/global selection; selection starts nothing. Only for unanswered
structural retrieval, read `${CLAUDE_PLUGIN_ROOT}/references/shared/115-code-graph.md` Selection and
evidence, HARD limits and the selected provider's cookbook. For selected/explicitly requested Graft
diagnosis (even missing), read only its Static readiness diagnosis and Effects gate. Reuse loaded
sections; consumers do not reload the full cookbook.
