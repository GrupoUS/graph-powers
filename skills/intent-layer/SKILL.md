---
name: intent-layer
description: "Use when a repository's AGENTS.md hierarchy has to be built, grown or audited: the root node plus child nodes in the subtrees that earn one. Trigger on: set up AGENTS.md, add an intent layer, agents keep misreading where things live, which directories need their own AGENTS.md, this AGENTS.md is too long, audit our AGENTS.md files. Runs at setup step 4b and from /evolve. Not for loading context (/prime), a domain rule (setup step 5) or this plugin's wiring (skill-improve)."
---

# Intent Layer

> Adapted from `intent-layer` in crafter-station/skills (MIT), by Railly Hugo, built on Tyler
> Brandt's Intent Layer. Modified by GrupoUS: the three shell scripts became one Python script with
> a gate, and the one-root rule became this harness's root pair. `NOTICE` carries the record.

## Overview

An intent node is the `AGENTS.md` an agent reads on entering a subtree: what the subtree owns, what
must hold there, how the usual change is made, and where to go next — in under 4k tokens. The
hierarchy of those nodes is the intent layer. Without it every agent re-derives the tree from the
files, and the fourth one to do so draws a different map from the third.

This harness already reads the nodes. `/prime` loads `${paths.backendRoot}/AGENTS.md` and the
nearest node under `${paths.frontendRoot}` (`045-context-staging.md`); `graph-powers:explorer` and
`graph-powers:debugger` load the nearest one before interpreting a subtree;
`graph-powers:frontend-specialist` reads its area's node before editing. Every one of those reads
returns nothing in a repository that never grew the layer. This skill is what makes them return
something.

## One root, and it is `AGENTS.md`

Upstream's rule is "one root context file — pick `CLAUDE.md` or `AGENTS.md`". Here the root is
settled: **`AGENTS.md` is the root node**, because Codex, Cursor and Grok read it and Claude Code
reads it too. `CLAUDE.md` beside it is not a second root — it carries Claude-specific behaviour and
pointers, and its Pointers table sends the reader to `AGENTS.md` for identity and invariants;
`AGENT_SETUP.md § 4a` owns that split. A child node is always `AGENTS.md`. A `CLAUDE.md` in a
subdirectory is a node three of the four harnesses never see, and `check` says so.

Codex concatenates every `AGENTS.md` from the git root down to the working directory and stops at
32 KiB. That is why nodes are capped, and why the gate measures the longest root-to-leaf chain
rather than each file alone.

## When to use

- The setup playbook reaches step 4b: the root pair exists, and the question is which subtrees
  earn a node of their own.
- Agents keep editing the wrong package, re-asking where a flow lives, or breaking an invariant
  nobody wrote down — the symptom of a subtree with no node.
- A node is past its cap, a child was added and never linked, or `/evolve` has landed a third
  learning in a subtree that has no node to hold it.

**Not** for loading context — `/prime` reads nodes and never writes them. Not for a domain rule:
"every DB call goes through the repository layer" is a file under `${rulesDir}/` with a `paths:`
field, setup step 5. Not for this plugin's own artefacts, which `skill-improve` audits.

## The script

One file, three subcommands, standard library only. `${CLAUDE_PLUGIN_ROOT}` is the plugin root on
Claude Code; on Codex the same file sits under the skills directory the installer wrote.

| Subcommand | Answers | Exit |
|---|---|---|
| `state [ROOT]` | root present, children linked, candidates due — `none`, `partial` or `complete` | 0 |
| `measure [ROOT] --depth 3 --top 25` | tokens per directory, has-node, verdict `NODE`, `SPLIT`, `ok` or `—` | 0 |
| `check [ROOT]` | every node under the cap, linked, resolving, purpose first, chain under 32 KiB | 1 on any `FAIL` |

```bash
python -X utf8 "${CLAUDE_PLUGIN_ROOT}/skills/intent-layer/scripts/intent_layer.py" state .
python -X utf8 "${CLAUDE_PLUGIN_ROOT}/skills/intent-layer/scripts/intent_layer.py" measure . --depth 3
python -X utf8 "${CLAUDE_PLUGIN_ROOT}/skills/intent-layer/scripts/intent_layer.py" check . --exclude templates
```

None of the three writes a file. `--exclude GLOB` repeats and hides a directory whose `AGENTS.md`
is not a node — a template still carrying `{{placeholders}}`, a vendored example. Tokens are
bytes ÷ 4, an estimate within roughly 15% on code; the thresholds are coarse enough that the error
does not move a verdict.

The project declares what would otherwise be retyped on every run in `.graph-powers/config.json`,
block `intentLayer` (contract: `${CLAUDE_PLUGIN_ROOT}/schema/config.schema.json`): `threshold`,
`split`, `maxNodeTokens`, `codexCap`, `exclude`, and `deferred` — directories the project decided
do not earn a node although the measure says they would. A flag wins over the block; the block
wins over the defaults; `--exclude` adds to the block's list. A deferral is a decision, so `check`
refuses it until the nearest ancestor node names the directory in backticks — `` `references/` `` —
with the reason beside it, and warns once the directory grows a node of its own. That is what lets
`state` reach `complete` honestly on a tree where the numbers say otherwise.

## Procedure

1. **Detect.** Run `state`. Show its output before saying anything about the tree.
2. **Route.** `none` means the root pair is missing — that is `AGENT_SETUP.md § 4a`, not this
   skill. `partial` runs steps 3 to 7 on what `state` named. `complete` goes to step 8.
3. **Measure.** Run `measure`. Paste the table first, verdicts and all. The table is the argument;
   a node proposed without it is a preference.
4. **Decide.** Apply the signals below to the table. Name which directories get a node, which get
   nothing, and the reason for each. `${paths.backendRoot}`, `${paths.frontendRoot}` and
   `${paths.schemaRoot}` are the first candidates, because the harness already reads nodes there.
   A directory the table flags and the decision refuses goes into `intentLayer.deferred`, and its
   reason goes into the nearest ancestor node's row — never only into the config.
5. **Capture.** For each node, answer the four questions in `references/capture-protocol.md` from
   the repository first — entry points, invariants, the canonical way to add the usual thing, the
   mistake already made once. What only a person knows is asked, one question at a time.
   Leaf-first: a parent node summarises its children, never the raw code.
6. **Write.** The shapes are in `references/node-anatomy.md`. Every child gets a downlink from the
   nearest ancestor node — in the root, a row in `Where things live`. Relative paths only.
7. **Check.** Run `check`. It has to exit 0, and its output is quoted in the report. A `FAIL` is
   fixed or explained; it is never trimmed out of the output.
8. **Maintain** (`state` said `complete`): ask which is wanted — *audit the nodes* (stale
   contracts, `check` findings, the capture questions asked again) or *find candidates* (`measure`
   again) — and do both when nobody is there to answer.

## Signals — when a subtree earns a node

| Signal | Action |
|---|---|
| 20k tokens or more in a directory, no node | create one, 2–3k tokens |
| 64k tokens or more | create one and split: child nodes below it |
| A responsibility boundary — its own manifest, deploy or owner | create one, whatever the size |
| Hidden contracts or invariants the code does not enforce | document them in the nearest ancestor node |
| A concern that crosses several subtrees | place it at the lowest common ancestor, once |

Not every directory. Not tests, unless the test harness itself has contracts. Not a utilities
folder small enough to read whole. A node the reader can replace by opening two files is weight.

## What a node holds

Purpose in the first lines — what it owns, what it explicitly does not. Then entry points,
contracts and invariants, the pattern for the usual change, anti-patterns from real incidents,
pitfalls (what looks deprecated and is not), and downlinks. Compression over explanation: the
reader is a capable model, and "we use TypeScript 5 and Express" is a line it does not need.
`references/node-anatomy.md` has the template and one before-and-after.

## Rationalisations

| Thought | Reality |
|---|---|
| "One node per directory keeps it consistent" | Consistency is not the goal; a reader entering a subtree is. Measure, then place. |
| "The root can hold it all" | Codex stops reading at 32 KiB, and every harness stops attending well before. Split by ownership. |
| "Put the rule in the node and in the rules layer" | One place. A path-scoped rule loads on its own; a node is read on entry. Pick by who needs it, when. |
| "The subdirectory has a `CLAUDE.md`, that counts" | Three harnesses never read it. Move it to `AGENTS.md`. |
| "Skip `check`, the nodes look fine" | Orphans and dangling downlinks look fine. The gate is the only reader that opens every link. |

## Where the depth lives

- `references/capture-protocol.md` — the four questions, the interview set, the capture order,
  the summarisation rules for parent nodes.
- `references/node-anatomy.md` — the root downlink row and the child template, a monorepo
  example, the compression before-and-after, and the checklist `check` cannot measure.
- `scripts/intent_layer.py` — `state`, `measure`, `check`.
