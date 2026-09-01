# Audit agent prompts

> Loaded by `/debug audit`. The bounded prompts below are used **verbatim** — a prompt improvised at
> dispatch time produces findings that cannot be compared across runs.

Nine dimensions, one base Evaluator plus at most two surface specialists, one message. The batch is
small by design: assurance comes from distinct questions, not from sending many agents over the
same files.

| Agent | subagent_type | Dimensions |
|---|---|---|
| Base | `graph-powers:evaluator` | D1-D5 · D7-D9; always |
| Security | `graph-powers:security-reviewer` | exploitability and data boundaries; sensitive surfaces only |
| UX | `graph-powers:ui-ux-designer` | D6 UX; frontend surface only |

**Every dispatched role is read-only by frontmatter**, and that is the whole point of the column.
An audit is a review, and this repository has already paid for handing a review to a write-capable
agent: one "partitioned ownership" of the diff it was reviewing and reverted about eighty lines of
it to HEAD. The incident is recorded in
`${CLAUDE_PLUGIN_ROOT}/skills/debugger/references/anti-patterns.md`. Earlier slots named
`graph-powers:debugger` or `graph-powers:frontend-specialist`, both of which carry
`Write` and `Edit`, and the only thing standing between them and the diff was the prose line in the
preamble below — which is a request, not a permission.

D7 sits with the Evaluator rather than with UX because judging whether a gate would actually fail needs
`Bash`, and `graph-powers:ui-ux-designer` deliberately has none.

All applicable roles spawn with `run_in_background: true` in a single message. Resolve every `${…}` placeholder
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

## Base Evaluator — consolidated repository audit (D1-D5, D7-D9)

```
TASK: Adversarially audit the repository across every non-UX dimension below. Treat this as one
acceptance boundary: report each defect once and do not delegate or spawn refuters.

D1 Architecture — layer boundaries, dependency direction, cyclic imports, a module that knows about
   a layer it should not, a singleton re-instantiated in three places.
D2 Structure — directory layout against the declared layer map, files in the wrong layer, an entry
   index that does not export what the tree implies.
D3 Code quality — swallowed errors, live unchecked nullability, divergent duplication and functions
   doing unrelated jobs.
D4 Documentation — commands, flags, paths or prerequisites that do not match the tree or runtime.
D5 Missing flows — unhandled errors, retries, dead letters and first-run paths assumed but absent.
D7 Tests and CI — untested critical paths, assertions that assert nothing, gates that cannot fail and
   ignored CI failures.
D8 Dependencies — actionable advisories, abandoned or redundant packages and unjustified direct
   dependencies.
D9 Technical debt — stale TODO/FIXME, dead exports, commented-out blocks and expired shims.

Read ${CLAUDE_PLUGIN_ROOT}/skills/planning/references/layer-map.md for the ordering this is judged
against, then read the project's own layer map in ${rulesDir}/ if it has one — it wins.

A finding must name the import, path, command or runtime evidence that proves it. Rank by concrete
failure impact, not by aesthetics. "The architecture is unclear" is not a finding.
```

## Security specialist — sensitive surfaces only

```
TASK: Audit only the sensitive surfaces named by the controller for exploitable authorization,
tenant isolation, personal-data, payment, secret-handling, injection and unsafe-default defects.
Trace each finding to a reachable boundary and concrete failure scenario. Do not repeat general
quality findings the Evaluator owns.
```

## UX specialist — frontend surface only (D6)

```
TASK: Audit the user experience surface, by reading it.

D6 UX — loading, empty and error states; keyboard operability; focus handling; contrast; the
   smallest supported viewport; what happens on a slow connection.

You have no Bash and no browser here: judge from the source, and say plainly which findings would
need a running page to confirm. A UX claim you could not check is reported as unverified, never as
a finding.
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
