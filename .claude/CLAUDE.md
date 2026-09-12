# Claude Code — graph-powers

The rules for this repository are in `AGENTS.md`, at the root. Read it when the work touches a cardinal,
a gate, wiring or a harness artefact: it carries the eight cardinals, the gate owner and the ownership
map. A typo or a local fix follows the rule file already scoped by `paths:`.

Domain rules load on their own, per the `paths:` of each file in `.claude/rules/`.

One reminder that saves rework: **this repository is not a project, it is the single copy of a
harness installed in many.** Anything that only makes sense in one specific repository is in the
wrong place here — it becomes a parameter in `schema/config.schema.json`.
