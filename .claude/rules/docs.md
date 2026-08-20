---
paths:
  - "docs/**"
  - "README.md"
  - "AGENT_SETUP.md"
  - "*.md"
---

# Documentation

## One thing, one place

This repository exists because duplicated content diverges. That holds for the documentation too:
each fact lives in one file and the others point at it.

| Subject | Where it lives |
|---|---|
| What the plugin is, why it exists, what it brings | `README.md` |
| The setup procedure the agent executes | `AGENT_SETUP.md` |
| Architecture decisions and what was refused | `docs/ARCHITECTURE.md` |
| Who it is for, what it solves, what it does not | `docs/AUDIENCE.md` |
| How to review a change here | `CONTRIBUTING.md` |
| The project parameter contract | `schema/config.schema.json` |

**The root `DESIGN.md`, `PRODUCT.md` and `REVIEW.md` are not documentation about this plugin.** They
are the specifications the agent applies to the *host project*: what its counterpart must contain,
how to source each section, and how to improve one that already exists. Writing plugin
meta-documentation into them is the one mistake this table exists to prevent.

## Numbers need a source

Every measurement cited says how it was obtained and when. "221 files, 45 identical" is useful;
"a lot of duplication" is not. A number with no source ages without anyone noticing.

## No machine paths

No home directory in a tracked file: any path whose first segment is `home` or `Users`, in any of
its three spellings. Use `<org>/<repo>`, a shell variable the text defines itself, or the Claude
Code default path, which is the same on every machine.

A bare drive root is **not** in that class and is allowed: `Remove-Item -Recurse -Force C:\` is how
the destructive-floor tests spell the hazard they defend against, and `C:\Windows\System32` is the
same path on every Windows install. `.github/check_machine_paths.py` is the one place the rule is
written as code; the earlier version lived inline in three files and failed on those very fixtures.

## A published command is a tested command

Every command that appears in the documentation was run before it was written down. If the output is
quoted, it is the real output. A guide that was never run is a hypothesis formatted as an
instruction.

## English

The documentation is in English so the plugin is usable outside the group that wrote it. Projects
that install it declare their own language in `project.locale`, and their rules and instructions are
theirs to write in whatever language they work in.
