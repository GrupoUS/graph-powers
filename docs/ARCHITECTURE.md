# ARCHITECTURE — the decisions behind Graph Powers, and what was refused

This document records why the plugin has the shape it has. A decision without its reason written
down becomes a superstition in six months; a refused decision without a record comes back as a fresh
proposal every quarter.

---

## 1. A plugin, not a synchronised copy

**Decided:** the shared core lives in a plugin distributed through a git marketplace.

**Alternatives refused:**

- **A canonical repository plus a sync script.** That is exactly the model that produced the
  original divergence: 176 same-named files with different content. Syncing by copy depends on
  somebody running the script, always, in every repository.
- **Everything in `~/.claude/` (user level).** It applies to every project on the machine with no
  installation, but it is local: not versioned, not synced between computers, and it reaches nobody
  else on the team.

**What decided it:** the precedence chain `Managed > CLI > Project > User > Plugin`. It gives the
property the copy model never had — **a project can disagree with the plugin without forking it.**
Put the file in its own `.claude/`.

---

## 2. Configuration as a contract, not a convention

**Decided:** families of parameter in one config file per project, validated by JSON Schema, with a
safe default for every one.

The coupling was measured before it was removed: 20 hard points spread across hooks, commands and
rules, all reducible to five families — branch names, opt-in variable prefix, repository paths,
toolchain commands, and domains/IDs.

**The consequence that matters:** `hooks/_config.py` is the only file in the repository that knows
projects are different. Every hook is byte-for-byte identical in every installation.

**Refused:** letting each hook read what it needs. It spreads config reading across eleven files and
turns any contract change into eleven edits. Three hooks had drifted back into their own readers by
the time of the public release; they were folded back.

---

## 3. Fail-open in every guardrail

**Decided:** invalid payload, missing or unreadable configuration fall back to the default and
release the call.

A guardrail that takes the session down when **it** has the bug gets switched off by the first
person who trips over it, and from then on there is no guardrail at all. The accepted failure mode
is "let through something it should have blocked"; the unacceptable one is "stopped the work through
a fault of its own".

**The honest trade-off:** a config with a stray comma makes the guardrails silently use the
defaults. That is why the setup procedure ends with an executable proof that prints the branch and
the prefix in force — if the defaults come out in a project that declared something else, you see it.

---

## 4. The best of each, not the biggest

During assembly, each artefact was compared across the five source harnesses. The criteria, in this
order:

1. safe frontmatter — explicit `tools:`, `disallowedTools` on whoever judges or researches, `model`
   pinned on the node that judges;
2. most useful body per line;
3. least coupling to one project.

Two choices went against intuition and are worth recording:

- **`verify.md` came from the small project, not the big one.** The monorepo version was 1576 lines
  and injected roughly 93 KB before any work started; the static site's did the same job in 59. The
  plugin carries the light base, and whoever needs the heavy phases keeps their own — precedence
  guarantees it.
- **Three popular agents were left out.** One had project templates written into its body; another
  was a 573-line agent that command orchestration replaced; the third existed in two projects and
  overlapped the evaluator.

One skill was discarded during assembly for promising five files in `references/` that existed in no
repository at all. An artefact that is born owing five files does not enter.

---

## 5. Short names inside the plugin

**Decided:** skills enter with a short name (`debugger`, `planning`), without the project suffix
some of them carried.

The suffix existed to escape shadowing by same-named global skills — precedence between levels made
the global version win. Inside the plugin everything is namespaced as `graph-powers:<name>` and the
collision disappears by construction. Keeping the suffix would be carrying the scar without the
wound.

The public release found the other half of that story: two skills still declared the suffixed name
in their frontmatter while the commands invoked both forms, so half the calls resolved and half did
not, silently.

---

## 6. The installer deletes nothing

**Decided:** `bunx graph-powers` registers the marketplace, installs the plugin, writes the Codex
artefacts and, optionally, a starting config. It does not remove a single file.

Cleaning up the existing `.claude/` is the step that decides whether adoption works, and it is the
only one that needs judgement: telling a diverged copy apart from what is unique to that project.
Automating it means deleting, without review, files that might be the only version of something.

So the cleanup lives in a procedure that lists, compares with `diff`, classifies and **stops** for
human approval. It is slower on purpose.

---

## 7. External plugins stay external

**Decided:** `superpowers` and `impeccable` are required dependencies installed from their own
channels, not vendored copies.

The first version of this repository shipped a 3.3 MB snapshot of impeccable — 70% of the package,
one minor version behind what its own npm registry served, with no licence file and no attribution.
That is the divergence problem this repository exists to end, reproduced inside the fix for it.

**The trade-off, stated plainly:** the plugin now has runtime dependencies it does not control. The
answer is not to vendor them back; it is that the setup playbook installs them, names their
versions, and tells the user how to keep them current.

---

## 8. Both harnesses, one source

**Decided:** everything Codex needs is *generated* from the artefacts that already exist for Claude
Code.

It turned out to be cheaper than expected: Codex hooks use the same event names, the same stdin
payload and the same deny semantics, so the eleven Python files run unchanged. Skills use the same
`SKILL.md` frontmatter, so they are copied rather than converted. Only subagents needed a real
translation, into TOML.

**Refused:** a second hand-maintained list of hooks for Codex. That is the divergence problem again,
now inside a single repository.

**The one asymmetry worth knowing:** Codex has no per-tool denylist, so `disallowedTools: Write,
Edit` becomes `sandbox_mode = "read-only"`. Denying only `Edit` — as the planner does, to keep
`Write` for its plan file — is therefore not expressible, and correctly does not become a sandbox.

---

## 9. Guardrails the plugin does not try to impose

Recorded so they do not come back as proposals:

- **"Two writers on the same file", detected by agent identity.** Not implementable: a hook cannot
  tell a subagent from the main thread — same session identifier, same process. What can be done,
  and is, is the actionable half: "only write to the files you declared".
- **A spend ceiling in an interactive session.** The CLI exposes a dollar budget only in `--print`
  mode. The spawn and round ceilings are the substitute that is controllable inside the session.
- **A turn limit per subagent.** The field exists in frontmatter, was tested both possible ways, and
  **does not brake** in the measured version. Where the brake mattered — an evaluator that could
  respawn the debugger — the fix was removing the tool, which is deterministic.

---

## 10. What is still open

- **The spawn ceiling does not cover agents launched by a workflow**, which do not pass the same
  interception point. It holds for direct spawns.
- **The ceiling numbers** (25 spawns per session, 8 rounds per agent) are starting points chosen
  above the limits already present in the workflows, not measured values. Calibrating them needs
  real usage data.
- **There is no automated eval** of the agents and skills. `claude plugin eval` exists, and using it
  is the natural next step — watching something fire is not the same as watching it work.
- **The Codex artefacts are machine-specific.** `.codex/hooks.json` and `.codex/agents/` embed the
  installed plugin's absolute path, because Codex expands no plugin variable. Each machine re-runs
  the installer, and the files are gitignored. A relative-path scheme would be better and does not
  exist yet.
