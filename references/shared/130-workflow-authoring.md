## Section 13: Authoring a workflow script

Applies when you write a script yourself and hand it to `Workflow({ script })`. Invoking a workflow
the plugin already ships — `Workflow({ name: 'graph-powers:ultra-plan' })` — needs none of this.

### The failure this exists to prevent

```
Error: Invalid workflow script: Script parse error: Unexpected token (156:63)

0 lines per rule. Note: this project uses `globs:` not `paths:` in frontmatter —
                                           ^
```

The caret is on a backtick, and the line is prose. A workflow script is mostly agent prompts, agent
prompts are written as template literals, and a prompt about code is full of backticks — so the
first `` ` `` inside the prompt ends the literal and everything after it is parsed as JavaScript.

Nothing catches this before the call. The script reaches the runtime as text, fails at parse, and
whatever it was orchestrating has to be written again from a blank page.

### Write it to a file, check it, then run it

```bash
node "${CLAUDE_PLUGIN_ROOT}/.github/check_workflows.mjs" <path-to-script.js>
```

It applies the same wrapper the runtime applies — these scripts use a top-level `return`, so
`node --check` rejects correct ones — then executes the body against stubbed `agent()`, `parallel()`
and `pipeline()`. Nothing spawns and nothing costs anything. It catches the parse error above, and
also the class the parse cannot: a helper used before it is defined, a destructure of a field the
schema never returns, a typo in a variable name — each of which otherwise surfaces mid-run, after
agents have been paid for.

`Workflow` persists every inline script and returns its `scriptPath`, so this is also how you iterate:
edit that file, re-check, re-invoke with `{ scriptPath }` rather than resending the whole script.

### Quoting, which is the whole problem

| Situation | Do |
|---|---|
| Prose that names a field, flag or file | Drop the backticks. `paths:` reads the same to an agent as `` `paths:` `` and cannot break the parse |
| A backtick is genuinely required | Escape every one: `` \` `` |
| Interpolating a value into a prompt | Template literal with `${…}`, and re-read the interpolated text for backticks it might carry |
| A prompt heavy with code punctuation | Build it from single-quoted strings joined with `+`, or `[...].join('\n')` |

The middle two are where it goes wrong, and it goes wrong in one specific way: the text is
*harvested* — a description, a rule excerpt, an error message — so it looks like data rather than
code, and nobody re-reads it as JavaScript. Harvested text is exactly where a backtick is most
likely and least expected.

### What is not JavaScript here

- **Plain JavaScript only.** Type annotations, interfaces and generics do not parse. `const x: string[]`
  is a syntax error, and it is the second most common cause after quoting.
- **`Date.now()`, `Math.random()` and argless `new Date()` throw.** They would break resume. Pass a
  timestamp in through `args`, or vary a prompt by its index.
- **No filesystem and no Node APIs.** An agent reads files; the script orchestrates.
- **`export const meta` must be a pure literal** — no variables, no calls, no spreads, no template
  interpolation. `name` and `description` are required, and `phases` should match the `phase()`
  calls in the body.

### Before you reach for one at all

A script that runs one agent, or several that each read the previous one's output, is a chain with
extra machinery around it — every node re-derives context the last one had, and none sees the whole.
Workflows earn their cost when work genuinely fans out: independent items, or the same item judged
through several lenses. Say so plainly when it does not, and do the work in the thread.
