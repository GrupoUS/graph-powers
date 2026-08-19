# Recovery protocol

> Loaded by `/debug recover`. Executed verbatim, in order, when a task has failed **two or more
> times** and the third attempt would otherwise be a blind retry.

The reason this file exists: the third attempt at a failing task is almost never a better version
of the second. It is the same attempt with more conviction. This protocol replaces conviction with
a reset.

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
