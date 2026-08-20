---
description: Failure recovery protocol for post-failure handling. Use after 2+ failed fix attempts.
workflow_type: routing
---

# /recover — structured failure recovery

**ARGUMENTS**: $ARGUMENTS

The protocol is one file, and this command runs it:

```
Read ${CLAUDE_PLUGIN_ROOT}/references/recovery-protocol.md and execute its five steps in order.
```

That file is the only copy. This command used to carry a second version of the same five steps —
different steps, under the same numbers, ending at an agent that does not exist — while `/debug
recover` pointed at the real one. Two protocols is worse than none: whichever the agent happened to
read, it could cite the other as its authority.

## What this command adds

Nothing to the protocol. Two things around it:

**Before Step 1, clear stale state.** A phantom error that survives a correct fix is usually a
cache, and a recovery protocol run against a stale build reaches confident wrong conclusions:

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

**After Step 5, before declaring it unrecoverable**, every declared gate has run in this session
and its exit code is on screen:

- [ ] `${tooling.commands.typeCheck}` — ran here, exit code shown
- [ ] `${tooling.commands.build}` — ran here, exit code shown
- [ ] `${tooling.commands.lint}` — ran here, exit code shown
- [ ] The invariants in `${rulesDir}/` matching the touched paths still hold

A remembered pass is not a pass. That is the same rule `/verify` enforces, and it matters more
here: recovery exists precisely because the previous attempts were confident and wrong.

## Where the stack-specific patterns live

They do not live here. A recovery hint about a framework's hydration, its router or its content
loader belongs in that project's `${rulesDir}/`, or in the framework skill the project declares —
never in a command that ships to every repository. This file carried a list of Astro fixes for long
enough that they read as general advice; they were general to one project.

## Related

- `/debug recover` — the same protocol, reached from the debugging chain.
- `${CLAUDE_PLUGIN_ROOT}/references/recovery-protocol.md` — the protocol itself, and the only place
  its steps are written down.
