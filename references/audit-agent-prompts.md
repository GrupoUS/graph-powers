# Audit agent prompts

> Loaded by `/debug audit`. The four prompts below are used **verbatim** — a prompt improvised at
> dispatch time produces findings that cannot be compared across runs.

Nine dimensions, four agents, one message. Each agent gets a disjoint slice: two agents covering the
same files is wasted parallelism and produces duplicate findings the consolidator then has to
de-duplicate by hand.

| Agent | subagent_type | Dimensions |
|---|---|---|
| 1 | `graph-powers:evaluator` | D1 architecture · D2 structure |
| 2 | `graph-powers:debugger` | D3 code quality · D8 dependencies · D9 technical debt |
| 3 | `graph-powers:debugger` | D4 documentation · D5 missing flows |
| 4 | `graph-powers:frontend-specialist` | D6 UX · D7 tests and CI |

All four spawn with `run_in_background: true` in a single message. Resolve every `${…}` placeholder
from the project config **before** dispatching — a subagent inherits nothing and will otherwise
invent the paths.

---

## Severity classification

Applied by every agent, so the consolidated report is sortable.

| Level | Meaning | Examples |
|---|---|---|
| **P0** | Ships broken, or is already broken in production | Data loss path, auth bypass, secret in a tracked file, tenant leak |
| **P1** | Will break under a foreseeable condition | Unhandled failure on a live path, missing index on a growing table, dependency with a high-severity advisory |
| **P2** | Real cost, no immediate failure | Duplicated logic that has already diverged once, untested critical path, misleading documentation |
| **P3** | Worth knowing, not worth stopping for | Naming, dead code, stale comment |

Auto-flag thresholds — a finding that crosses one of these is at least P2, regardless of the
agent's own judgement:

- test coverage below 80% on a path the audit classified as critical
- cyclomatic complexity above 10 in a single function
- a dependency advisory scoring 7.0 or higher
- a file over 1000 lines that more than one agent flagged independently

---

## Shared prompt preamble

Every agent prompt opens with this block, filled in:

```
CONTEXT
  Repository: ${project.name} · stack: ${project.stack}
  Roots: backend=${paths.backendRoot} frontend=${paths.frontendRoot} schema=${paths.schemaRoot}
  Gates: ${tooling.commands.typeCheck} · ${tooling.commands.lint} · ${tooling.commands.test}
  Branch: <current> · diff base: <base ref, when scoped to a PR>

MANDATORY CONTEXT
  Read ${CLAUDE_PLUGIN_ROOT}/references/safety-floor.md before reporting anything.

MUST NOT DO
  Edit any file. Run any state-changing git command. Report a finding you have not opened the file for.

RETURN
  A findings table: severity | dimension | file:line | one-sentence defect | concrete failure scenario.
  No prose summary. No praise. Findings only, most severe first.
  Cap: 15 findings. If you have more, keep the 15 that would hurt most and say how many you dropped.
```

---

## Agent 1 — architecture and structure (D1-D2)

```
TASK: Audit architecture and structure.

D1 Architecture — layer boundaries, dependency direction, cyclic imports, a module that knows about
   a layer it should not, a singleton re-instantiated in three places.
D2 Structure — directory layout against the declared layer map, files in the wrong layer, an entry
   index that does not export what the tree implies.

Read ${CLAUDE_PLUGIN_ROOT}/skills/planning/references/layer-map.md for the ordering this is judged
against, then read the project's own layer map in ${rulesDir}/ if it has one — it wins.

A finding here must name the import or the path that proves it. "The architecture is unclear" is not
a finding.
```

## Agent 2 — code quality, dependencies, technical debt (D3, D8, D9)

```
TASK: Audit code quality, dependency health and technical debt.

D3 Code quality — error handling that swallows, unchecked nullability on a live path, duplicated
   logic that has already diverged, a function doing four things.
D8 Dependencies — advisories, abandoned packages, two libraries doing the same job, a direct
   dependency that is only used once.
D9 Technical debt — TODO/FIXME older than the last release, commented-out blocks, dead exports,
   a compatibility shim whose other side is gone.

Read ${CLAUDE_PLUGIN_ROOT}/skills/debugger/references/anti-patterns.md first.

Rank by what would actually fail, not by what is ugliest.
```

## Agent 3 — documentation and missing flows (D4-D5)

```
TASK: Audit documentation accuracy and find flows that were never finished.

D4 Documentation — a README command that does not run, a documented flag that does not exist, a
   path cited that is not there, a setup step that silently requires something undocumented.
   Verify by running or by opening the file. A doc claim you did not check is not a finding.
D5 Missing flows — an error state with no handler, a form with no failure path, a webhook with no
   retry, a queue with no dead letter, a first-run experience with nothing in it.

The most valuable finding in this slice is the flow everyone assumed existed.
```

## Agent 4 — UX and tests/CI (D6-D7)

```
TASK: Audit user experience and the test/CI surface.

D6 UX — loading, empty and error states; keyboard operability; focus handling; contrast; the
   smallest supported viewport; what happens on a slow connection.
D7 Tests and CI — critical paths with no test, tests that assert nothing, a gate that cannot fail,
   a CI job whose failure is ignored, a flaky test nobody has quarantined.

For D7, check that each declared gate would actually fail on a real defect. A gate that always
passes is worse than a missing gate, because the report line reads as covered.
```

---

## Consolidation report template

Written to `docs/AUDIT-REPORT-<YYYY-MM-DD>.md`:

```markdown
# Audit — <project> — <YYYY-MM-DD>

**Scope:** <full repository | diff against <base>>
**Gates at audit time:** <command → result, per gate>
**Repository shape:** <source files> source · <test files> test · <commits since last release>

## Findings

| # | Sev | Dimension | Location | Defect | Failure scenario |
|---|-----|-----------|----------|--------|------------------|

## What was dropped

<Every agent that hit its 15-finding cap, and by how much. A silent truncation reads as full
coverage, which is the one thing an audit must never do.>

## Not audited

<Dimensions skipped, and why. "No frontend in this repository" is a valid line; an absent line is not.>

## Recommended order

<P0s first, then the P1 that unblocks the most other findings. Not a restatement of the table —
a sequence, with the reason each step comes where it does.>
```

The two sections people delete are "What was dropped" and "Not audited". They are the only sections
that tell a reader how much to trust the rest.
