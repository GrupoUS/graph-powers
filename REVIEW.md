# REVIEW.md — the spec for the host project's review contract

> **This file is not a document about Graph Powers.** It is the specification the agent applies when
> it creates or improves the `REVIEW.md` of the project the plugin is installed into.
>
> Read by: `AGENT_SETUP.md § 5`, `/pr-review`, `/verify`, `evaluator`, `security-reviewer`.

---

## What the project's `REVIEW.md` is for

One question, answered once: **what does this project refuse to merge?**

The generic review protocol comes from the plugin — parallel independent paths, consolidation, the
structural approval bar. What the plugin cannot know is what has actually broken *this* repository,
which gates are real here, and who has to approve what. That is this file.

It is **not** a copy of the plugin's review process. If a section of it describes how to run a
review, it is duplicating `/pr-review` and the two will diverge.

**Where it lives:** `REVIEW.md` at the project root, or merged into an existing `CONTRIBUTING.md` if
the project has one. Do not create a second review document.

---

## Required sections

### 1. The gates, and what each proves

Not a list of commands — the plugin already has that in `tooling.commands`. What each gate is
*evidence of*, and what it does not cover.

```markdown
| Gate | Command | Proves | Does not cover |
|---|---|---|---|
| Type check | <cmd> | Shapes line up at the boundary | Runtime nullability from external data |
| Tests | <cmd> | The paths with tests still work | Anything with no test — list what that is |
| Build | <cmd> | It compiles and bundles | It works |
```

**The "does not cover" column is the one that matters.** A green gate read as full coverage is how
a broken change ships looking verified.

### 2. Blocking findings — this project's list

The classes of defect that mean *request changes*, not *note for later*. Each one exists because it
already happened here, and each says so.

```markdown
| # | Blocking finding | Why it is blocking |
|---|---|---|
| B1 | A write to shared state outside a transaction | Left records half-applied for three days in <month> |
| B2 | A new foreign key with no index | Turned a 40 ms query into a table scan |
```

Generic severity comes from the plugin. **This table is the project's own scar tissue**, and it is
the most valuable thing in the file. A blocking finding with no incident behind it is a preference
wearing a severity label — write it down anyway, but say it is a preference.

### 3. Mechanical checks

The greps, scripts and probes that catch this project's recurring defects before a human looks. Each
with its exact command and what a hit means.

```markdown
| Check | Command | A hit means |
|---|---|---|
| Colour literal outside tokens | <grep> | Blocking — see DESIGN.md |
| Debug logging in shipped code | <grep> | Blocking |
```

These are what `/pr-review § 1` runs before any judgement path. The plugin ships none of its own: a
check that does not match the repository is a line that reads as coverage.

### 4. Surfaces that raise the bar

Which parts of this codebase get a harder review, and what to demand extra when they change:
authentication, payments, personal data, schema, deploy configuration, anything with a webhook.

```markdown
| Surface | Paths | Demand extra |
|---|---|---|
| Auth | <paths> | The negative test: does the wrong user get denied? |
| Schema | <paths> | The rollback path, written down, before merge |
```

### 5. Approval authority

Who decides what — by role, not by name, so the file survives people leaving.

```markdown
| Change | Who approves |
|---|---|
| Within an existing pattern | The reviewer |
| New dependency or new pattern | <role> |
| Schema, auth, payment, personal data | <role>, always |
| Anything visible outside the repository | The person who owns the deploy |
```

### 6. What this project does not review for

Explicitly out of scope: formatting handled by the formatter, preferences already settled in
`DESIGN.md`, style opinions. A review that relitigates settled decisions trains people to skim
reviews.

---

## How the agent builds it

**The valuable content comes from history, not from the code.**

1. **Read the gates that genuinely exist.** From `tooling.commands` and the CI config. A command
   that is not there does not go in the table.
2. **Mine the git history for the blocking list.** `git log --grep=fix --oneline`, revert commits,
   hotfix branches, anything tagged as an incident. A fix that had to ship urgently is a candidate
   blocking finding, and the commit message usually says why.
3. **Read the existing review artefacts** — PR templates, `CONTRIBUTING.md`, a checklist in the
   wiki, comments that repeat across PRs.
4. **Ask about approval authority.** It is never in the code, and getting it wrong is how a change
   reaches production without the person who needed to see it.
5. **Never invent a blocking finding.** A rule with no incident behind it, presented as one, makes
   the whole table untrustworthy. Mark preferences as preferences.

---

## Improving a `REVIEW.md` that already exists

1. `diff` against the required sections.
2. **Every existing blocking rule stays.** It is there because of something, and the something may
   not be written down. Ask about any rule you cannot trace — the answer is usually the best line in
   the file.
3. Where a rule references a gate, path or script that no longer exists, **report it as drift.**
   Removing it silently deletes an incident nobody documented elsewhere.
4. Fold in what the plugin now provides: if the existing file explains how to run a parallel review,
   how to consolidate findings, or how to write a verdict, that comes from `/pr-review` now — replace
   it with a pointer.
5. Show the diff before writing.

---

## Quality bar

- [ ] Every gate in the table has a "does not cover" entry
- [ ] Every blocking finding names an incident, or is explicitly labelled a preference
- [ ] Every mechanical check has a command that was run, with its real output
- [ ] Approval authority is by role, not by name
- [ ] Nothing duplicates the plugin's review process — it points at it
- [ ] Under 150 lines

---

## What follows from it

- `/pr-review § 1` runs the mechanical checks and treats a hit as a blocker;
- `/pr-review § 5` raises the floor for any diff touching a listed surface;
- `/verify § 3` reads the blocking list as the project-specific half of its checklist;
- `evaluator` and `security-reviewer` cite the blocking IDs instead of re-arguing severity.
