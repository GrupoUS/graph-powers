# Recovery protocol

> Loaded by `/debug recover`. Executed verbatim, in order, when a task has failed **two or more
> times** and the third attempt would otherwise be a blind retry.

The reason this file exists: the third attempt at a failing task is almost never a better version
of the second. It is the same attempt with more conviction. This protocol replaces conviction with
a reset.

---

## Step 0 — Clear stale state, before anything else

A phantom error that survives a correct fix is usually a cache, and a recovery protocol run against
a stale build reaches confident wrong conclusions.

```bash
# Only what this project declares, and one command per line: `&&` is not a statement
# separator in Windows PowerShell 5.1, and a cache path this plugin guessed would be wrong
# somewhere. Check each exit code before running the next.
${tooling.packageManager} install
${tooling.commands.typeCheck}
${tooling.commands.build}
```

If the project's build tool keeps a cache directory, it is named in `${rulesDir}/` — this plugin
does not know where it is, and inventing a path is how a recovery step deletes the wrong directory.

---

## Step 1 — Stop and state the loop

Before anything else, write down:

- what was attempted, each time, in one line per attempt;
- what changed between attempts (if nothing changed, say that — it is the finding);
- the exact error, quoted, from the most recent attempt;
- whether the error text changed between attempts. **An identical error across attempts means the
  fixes never reached the failing code path.**

Do not skip to a fix. This step is not overhead; it is the only step that distinguishes recovery
from a fourth attempt.

---

## Step 2 — Invalidate the assumption

Every repeated failure rests on an assumption nobody checked. Name it explicitly, then check it:

| Common assumption | How to check it in one command |
|---|---|
| "The code I edited is the code that runs" | Add a unique marker, run, confirm it appears |
| "The test failure means the feature is broken" | Read the test; confirm it asserts what you think |
| "The environment matches what the config declares" | Print the resolved values, do not infer them |
| "This dependency version has the API I am calling" | Open the installed package, not the docs |
| "The gate that passed proves this works" | Confirm the gate would fail if you broke it deliberately |

One of these is usually it. The check is cheap; the assumption has already cost two attempts.

---

## Step 3 — Reduce to the smallest failing case

Strip the reproduction until removing anything else makes the failure disappear. Not "a smaller
test" — the smallest one.

The reduction is itself the diagnosis more often than not: the step where the failure vanishes is
where the bug lives.

If it cannot be reduced, say so and go to Step 5 — an irreducible failure is a signal that the
model of the system is wrong, not that the reduction was done badly.

---

## Step 4 — Escalate the reasoning, not the effort

For an L5+ task, or a third attempt on any task, invoke
`mcp__sequential-thinking__sequentialthinking` **before** writing any fix. Decompose:

1. the error surface — everything that could produce this symptom;
2. why the previous fixes missed — for each attempt, which branch of the surface it addressed;
3. the candidate paths not yet taken, ranked by what would falsify them fastest.

Then take the fastest-to-falsify path first, not the most likely one. A wrong hypothesis you can
kill in a minute beats a probable one that takes an hour to test.

If the decomposition keeps returning the same branch, the problem may be the session rather than
the bug: by the third attempt the thread has spent many turns justifying one reading, and every
further hypothesis is generated inside it. Spawn `graph-powers:evaluator` in **Mode 5**, the second
opinion: an agent that starts from its prompt and nothing else, on a question written to carry the
case and not the argument. How to write that question, the two engines, and the dollar ceiling
only the headless one has are in `${CLAUDE_PLUGIN_ROOT}/references/rubrics/evaluator-rubric.md`,
Mode 5. It is slow and it costs money, which is why it belongs here — at the point where a fourth
wrong attempt costs more.

---

## Step 5 — Stop and hand back

Recovery has a floor. When Steps 1-4 leave the cause unknown, **stop** and produce a handoff rather
than a fifth attempt:

```markdown
## Blocked — <task>

**Symptom:** <exact error, quoted>
**Attempts:** <one line each, with what changed>
**Ruled out:** <what was falsified, and by which check>
**Still open:** <the branches of the error surface not yet eliminated>
**Needs:** <the access, decision or information that would unblock this>
```

Write it to `.graph-powers/HANDOFF.md` and say it out loud in the response.

A `BLOCKED` handoff is a successful outcome of this protocol. Burning the spawn ceiling on retries
that share a hypothesis is not.

**Before declaring anything unrecoverable**, every declared gate has run in this session and its
exit code is on screen:

- [ ] `${tooling.commands.typeCheck}` — ran here, exit code shown
- [ ] `${tooling.commands.build}` — ran here, exit code shown
- [ ] `${tooling.commands.lint}` — ran here, exit code shown
- [ ] The invariants in `${rulesDir}/` matching the touched paths still hold

A remembered pass is not a pass. It is the same rule `/verify` enforces, and it matters more here:
recovery exists precisely because the previous attempts were confident and wrong.

Anti-patterns this protocol exists against: looping past two attempts · skipping the write-up in
Step 1 · reverting without showing the diff · escalating with a question too vague to answer.

Stack-specific hints do not live here. A recovery hint about a framework's hydration, its router or
its content loader belongs in the project's `${rulesDir}/`, or in the framework skill the project
declares — never in a protocol that ships to every repository.
