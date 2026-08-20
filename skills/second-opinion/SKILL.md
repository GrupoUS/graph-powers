---
name: second-opinion
description: "A verdict from a Claude session that never saw this conversation, with a dollar ceiling. Use when a fix keeps not sticking, or a decision feels right mainly because you have been staring at it. Withholding the history is the point, so not for anything that needs it — and not for routine review, which is /verify and /pr-review."

---

# Second opinion — review from a session that never saw this one

## Why this exists

An advisor that reads the current chat inherits the current chat's conviction. By the time you
want a second opinion, the thread has usually spent twenty turns justifying one approach, and a
reviewer given those twenty turns will grade the justification, not the work. The fix is not a
better prompt — it is a reviewer with no access to the argument.

This is also the only place in the harness with an enforceable spend ceiling. Measured on CLI
2.1.235: `--max-budget-usd` exists in **print mode only**, and `--max-turns` does not exist at
all. An interactive session has no budget ceiling to set. A headless one does.

## The invocation

```bash
timeout 900 claude -p --model opus --max-budget-usd 1.50 --permission-mode plan --disallowedTools Write Edit "<the question, self-contained — see below>"
```

Every flag earns its place:

| Flag | Why |
|---|---|
| `-p` | non-interactive, and the only mode where the budget ceiling applies |
| `--model opus` | explicit, never inherited. The node that judges is where saving tokens costs the most: a weak reviewer produces confident false positives that other nodes then "fix", and the origin of the error is lost |
| `--max-budget-usd` | the review is bounded in dollars, not in trust |
| `--permission-mode plan` + `--disallowedTools` | the reviewer reports; it never edits. A reviewer that can patch what it dislikes stops being a reviewer |
| `timeout` | a headless session that hangs is invisible — nothing prints until it ends |

Do **not** pass `--continue`, `--resume`, or `--session-id` of the current session. Any of them
restores exactly the context this skill exists to withhold.

## Writing the question

The reviewer starts blind, so the prompt must carry the case with it — but only the case, never
the argument for a side:

- **The artifact**, by path. It reads the repo, so `${paths.planDir}/<file>.md` or
  `git diff main...HEAD` is enough; do not paste content you can point at.
- **The decision to judge**, stated neutrally. "Is splitting X into two services right here?" —
  not "we decided to split X, confirm that this is right".
- **The constraint that is real**, so the reviewer does not solve a different problem: the branch,
  the surfaces touched, what is out of scope and why.
- **What a useful answer looks like**: a verdict, the strongest argument against it, and the one
  check that would settle it.

Leave out: what the current thread already concluded, who proposed what, and how much work is
already done. All three are pressure, not evidence.

## Reading the answer back

The reviewer is blind, and blindness cuts both ways: it has no thread bias, and no idea what was
already ruled out. So treat a disagreement as a question, not a verdict — if it flags something
the thread explicitly decided against for a stated reason, the reason still stands, and what you
learned is that the reason is not visible in the artifact. That is a finding about the artifact.

Record the outcome in `PROGRESS.md` under `## Verdicts` with the invocation as evidence, so the
next session can see the review happened without paying for it twice.

## Cost

One call is a full session — slow and far from free, which is why it is capped. Reach for it when
the decision is expensive to get wrong, not as a habit. If the question would be settled by a
grep, a type-check, or a test, run that instead: this skill buys independence of judgment, and
independence is worthless on a question that has a mechanical answer.
