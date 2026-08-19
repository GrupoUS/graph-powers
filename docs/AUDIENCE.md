# AUDIENCE — who Graph Powers is for, what it solves, what it does not

## The problem

Anyone who uses an agent CLI seriously ends up building a harness: a few subagents, a few skills,
commands that chain the work, hooks that stop an agent committing on its own. It works. Then a
second project arrives, and the fastest way to have the same harness is to copy the folder.

From there, two harnesses. Then four. Each gets fixes the others do not, and nobody notices, because
nothing breaks — they just drift apart.

The measurement that produced this repository, across five projects in one group:

| | |
|---|---|
| Files with the same name in ≥4 of the 5 projects | 221 |
| Of those, **byte-for-byte identical** | **45** |
| Of those, diverged | **176** |
| Files that existed in only one project | 178 |

The cost is not tidiness. Two security defects fixed in **one** of the projects were still live in
the other four:

- a researcher with write permission, against its own description, because the `memory:` field
  injects `Write`/`Edit` on top of the tool allowlist;
- an evaluator carrying the `Agent` tool with no turn limit, closing a recursion loop.

Fixing it in one repository never reached the others. There was no copy — there were five.

## Who it is for

**It fits you if:**

- you maintain more than one repository with Claude Code or Codex CLI, and you have already copied
  a `.claude/` from one to another;
- the configurations started identical and today you cannot say which one is right;
- you want a guardrail fix to reach every project without visiting each one;
- your projects have different stacks and you do not want one harness per stack;
- you work across both Claude Code and Codex and want the same rails in both.

**It does not fit if:**

- you have a single project and do not intend to have another. A local `.claude/` solves it, and
  this plugin only adds indirection;
- you want a finished harness that guesses your domain rules. The plugin brings **process**; your
  product's rules remain yours to write;
- you need something that works without an agent CLI installed;
- you cannot install two external plugins. `superpowers` and `impeccable` are required, and neither
  is vendored here.

## What it delivers

| | |
|---|---|
| **12 agents** | research, review, debugging, planning, verification, frontend, mobile, security, and an audit of the harness itself |
| **12 skills** | process (planning, debugging, skill creation, harness audit) and craft (UX, performance, SEO, accessibility, Astro, browser testing) |
| **12 commands** | from planning to verification, chained |
| **11 guardrails** | git rails, execution ceilings, file protection, kill switch — running on both harnesses from the same files |
| **1 contract** | `schema/config.schema.json` — the parameters that make all of the above work in any repository |

The guardrails are the part that pays for itself fastest. They stop an agent — with code, not with a
request in a prompt — from committing without approval, working on a protected branch, writing to a
file that is not its own, or entering an endless spawn loop.

## What it does not do

- **It does not clean your `.claude/` on its own.** That is the step that decides whether adoption
  works, and it needs judgement about what is unique to your project. There is a procedure for it,
  reviewed by a person before any removal.
- **It does not write your domain rules.** Data invariants, integrations, UI conventions: the plugin
  brings the place where they live (`.claude/rules/`) and the routing that loads them, not the
  content.
- **It does not stop you disagreeing.** Claude Code precedence is `Project > Plugin`: any file you
  put in your `.claude/` beats the plugin's, with no fork and no uninstall. The plugin is the floor,
  not the cage.
- **It is not an agent framework.** No new runtime, no dependency, no background process. Markdown,
  JSON and standard-library Python.
- **It does not vendor other people's work.** `superpowers` and `impeccable` install from their own
  channels and update on their own schedule.

## How you know it is working

Three observable signals, in order of importance:

1. **A guardrail fix reaches every project** on the next plugin update, with nobody visiting any
   repository. If you have to edit in two places, something went back to the old model.
2. **Each project's `.claude/` shrinks** to configuration and domain. In a project with no skills of
   its own, `skills/` and `commands/` end up empty.
3. **The guardrails deny when they should.** `python3 hooks/test_hooks.py` exits `0`, and a
   `git commit` without approval is blocked citing that project's prefix — under Claude and under
   Codex alike.

## The cost

`claude plugin details graph-powers` reports the always-on context cost of having everything
available — a few thousand tokens per session. Hooks do not count: they show up as `harness-only —
no model context cost`.

If that is too much for a small project, the answer is `claude plugin disable` on the components it
does not use. Editing the plugin to fit one project is the beginning of the problem it came to
solve.
