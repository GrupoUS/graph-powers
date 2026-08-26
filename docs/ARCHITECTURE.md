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

**Refused:** letting each hook read what it needs. It spreads config reading across a dozen files and
turns any contract change into a dozen edits. Three hooks had drifted back into their own readers by
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

**Decided:** the installer registers the marketplace, installs the plugin, writes the Codex
artefacts and, optionally, a starting config. It does not remove a single file.

Cleaning up the existing `.claude/` is the step that decides whether adoption works, and it is the
only one that needs judgement: telling a diverged copy apart from what is unique to that project.
Automating it means deleting, without review, files that might be the only version of something.

So the cleanup lives in a procedure that lists, compares with `diff`, classifies and **stops** for
human approval. It is slower on purpose.

---

## 6b. Distribution is a clone, not a registry

**Decided:** two ways in — the Claude Code marketplace, and `git clone`. No npm package.

1.0.0 published to npm, and the cost showed up immediately: a registry account, a 2FA device and a
release for every one-line fix, sitting between the fix and the machine that needed it. A publish
was refused mid-session for a missing OTP while the same commit was already on `main` and already
correct.

What a registry buys is dependency resolution, versioned installs and a build artefact. This
repository has no dependencies, no build step, and its "artefact" is markdown, JSON and
standard-library Python — the checkout **is** the thing that runs. So the registry was buying
nothing and charging a release.

**What this costs, and how it is paid:** `claude plugin update` compares the version in
`.claude-plugin/plugin.json`, not the commit. A fix pushed without a bump sits on `main` while
every installed machine keeps the old files and the command reports "already at the latest
version" — a report that says covered while the old guardrail is the one running. So the version
is the delivery channel, and a CI gate refuses any change to what the plugin ships that does not
move it. Nothing about that is left to memory.

**The trade-off, stated plainly:** there is no version pinning for consumers. A clone tracks a
branch, not a tag. That is acceptable here because the harness is meant to converge, not to fork —
a project pinned to an old copy of the guardrails is the exact failure this repository exists to
end. Anyone who does need a pin can check out a tag; the update refuses to fast-forward a clone
that is not on a tracking branch.

Hook wiring follows the same one-source rule: `hooks/hooks.json` is the declaration both native
plugin loaders discover. The clone-based Codex installer reads that file and resolves its
`${CLAUDE_PLUGIN_ROOT}` placeholders only while merging the legacy `.codex/hooks.json` surface.

---

## 7. External plugins stay external

**Decided:** nothing the commands depend on is external. The rule's name is kept because it still
holds for what is optional — the `codex` and `code-review` plugins, Emil's two design skills — and
because the history of how each required piece crossed the line is the argument for the rule's
current shape. The craft layer that `impeccable` used to supply is
now the plugin's own — `skills/designer/references/craft-passes.md` and `craft-floor.md`, written
for this harness rather than copied — because a craft pass that needs a package runner, a plugin
install and a hook merge in every project puts three setup steps in front of a design task, and
each of them can be refused by this plugin's own guardrails.

`landing-page-design` tested the rule at its weakest point, and on 2026-08-26 it crossed to the
other side. Through 1.9.x it stayed external because it is a single 16 KB `SKILL.md` meant to be
forked at its design values, and a verbatim copy would have made this repository the owner of
somebody else's palette. What reversed the decision was measured rather than argued. Installed as a
personal skill it is listed in every session with a description claiming *any* web UI, so it
out-triggered `designer` and the project's design rule on dashboards, where its canon is wrong. A
personal-scope name also shadows any plugin skill of the same name, so the "only for a landing
surface" gate in `/design` could not be enforced from here. And the values that made it somebody
else's palette are exactly the ones this harness overrides. So it entered the way the debugger
references did — as adapted material recorded in `NOTICE`, the page system kept and the visual
canon demoted to a fallback that carries its reasons — and not as a snapshot.

The first version of this repository shipped a 3.3 MB snapshot of impeccable — 70% of the package,
one minor version behind what its own registry served, with no licence file and no attribution.
That is the divergence problem this repository exists to end, reproduced inside the fix for it.

`superpowers` was the last required external, and the one the rule was written around: through
1.9.x it stayed a plugin installed from its own marketplace because it was actively maintained
upstream and shipped for both harnesses. Three measured facts reversed that on 2026-08-26. Nine of
the ten commands opened with one of its skills and called twelve more — 151 references in 37 files
— so without the install `/plan`, `/debug` and `/implement` stopped mid-run; a dependency nine
commands cannot run without is not tooling around the harness, it is the harness. It ships for
Claude Code and Codex only, so on Cursor and Grok "four harnesses, one source" was true of the
guardrails and false of the method. And `check_context_budget.py` charged every one of those
calls zero bytes, because none matched a local path: the heaviest load in the command set was the
one the gate could not see. So its method layer entered the way the debugger references did —
adapted, recorded in `NOTICE`, rewritten where upstream contradicts this harness (routine commits,
a model passed at dispatch, shell scripts, a merge/PR menu at the end) — and the gates now price
what they always cost.

**The trade-off, stated plainly:** the method layer no longer tracks upstream. A fix Jesse Vincent
ships reaches this plugin only when somebody reads the release notes and ports it; the price of
that is a periodic diff against upstream, and the price of the alternative was a harness that did
not run on two of its four targets.

The `intent-layer` skill is the other side of the same rule, and it is worth saying why it is not a
contradiction. Upstream (crafter-station/skills, MIT) ships three shell scripts, which cardinal 8
bans from anything an agent executes, and a "one root file, pick `CLAUDE.md` or `AGENTS.md`" rule
that this harness's root pair contradicts by design. A copy that tracked upstream would therefore be
wrong on every machine that installs it. So it enters the way the debugger references did — as
adapted material recorded in `NOTICE`, deliberately not tracking upstream because it no longer says
the same thing — rather than as an install-by-copy dependency. The test is not "is it small enough
to vendor"; it is "would the upstream bytes be correct here". For `landing-page-design` they stopped
being correct the day the harness had an owner for every value in it; for `intent-layer` they never
were.

---

## 8. Four harnesses, one source

**Decided:** everything Codex, Cursor or Grok needs is *generated* from the artefacts that already
exist for Claude Code.

It turned out to be cheaper than expected: Codex hooks use the same event names and stdin payload,
so the thirteen Python files run unchanged. One script is registered twice:
`smart_bash_approver.py` blocks at `PreToolUse`, then reuses the same classification at
`PermissionRequest` to approve safe escalations without surfacing a prompt. The event response
shapes differ, and the script emits each client's supported vocabulary from that one decision.
`tool_approver.py` is registered only on `PermissionRequest`, for every tool that is not `Bash`:
the same `autonomy` posture, applied to the half of a session that a shell classifier cannot see.
Skills use the same `SKILL.md` frontmatter, so they are copied rather than converted. Only
subagents needed a real translation, into TOML.

Cursor is the third client. Its native hook file is a flattened, renamed copy of `hooks/hooks.json`
(`cursor/install.mjs`): `Bash` becomes `Shell`, `Edit` becomes `StrReplace`, nested matcher groups
become an array of commands, and `${CLAUDE_PLUGIN_ROOT}` becomes a path relative to the plugin
root. PermissionRequest and Notification do not exist there, so they are skipped — inventing a
Cursor event for them would be a second owner for a decision that already has one. `preToolUse`
still classifies the shell. The IDE confirmation flood is not a hook: it is
`~/.cursor/permissions.json`, which the same installer writes.

Grok CLI is the fourth client. It reads Claude's nested `hooks/hooks.json` and aliases
`CLAUDE_PLUGIN_ROOT` from `GROK_PLUGIN_ROOT`, so there is no translated hook list. What does
not line up is the stdin payload: camelCase (`toolName`, `toolInput`, `workspaceRoot`) and Grok
tool names (`run_terminal_command`, `search_replace`, `spawn_subagent`). `_config.py` canonicalises
those onto the Claude names the gates already branch on, and `emit_pretool_deny` writes both
Grok's top-level `{ "decision": "deny" }` and Claude's `hookSpecificOutput.permissionDecision`.
`.grok-plugin/` is generated (`grok/install.mjs`). The confirmation flood is
`~/.grok/config.toml` `[ui] permission_mode = "always-approve"` — user config only; a project
`.grok/config.toml` cannot set it. PreToolUse deny still blocks.

**Refused:** a second hand-maintained list of hooks for Codex, Cursor or Grok. That is the divergence
problem again, now inside a single repository.

**The asymmetries worth knowing.** Codex has no per-tool denylist, so `disallowedTools: Write,
Edit` becomes `sandbox_mode = "read-only"`. Denying only `Edit` — as the planner does, to keep
`Write` for its plan file — is therefore not expressible, and correctly does not become a sandbox.

And `workflows/` does not cross at all: Codex has no equivalent of `Workflow({name})`, so the two
orchestrations are Claude Code only. This is the one place the "one source" rule bends, and it bends
in the safe direction — nothing is hand-maintained twice; a capability simply exists on one side.
What matters is that the chain is an accelerator, not a floor: under Codex, `/plan`, `/implement` and
`/verify` do the same work as commands, which is the same fallback Claude Code takes when the
workflow name does not resolve.

---

## 9. Guardrails the plugin does not try to impose

Recorded so they do not come back as proposals:

- **"Two writers on the same file", detected by agent identity.** Not implementable: a hook cannot
  tell a subagent from the main thread — same session identifier, same process. What can be done,
  and is, is the actionable half: "only write to the files you declared". That half was armed and
  unarmed at the same time until 1.3.0 — the hook read a lease file nothing ever wrote. The producer
  is now planning Phase C, from the validated `writeLease` emitted by
  `skills/planning/scripts/sdd.py`.
- **A spend ceiling in an interactive session.** The CLI exposes a dollar budget only in `--print`
  mode. The spawn and round ceilings are the substitute that is controllable inside the session.
- **A turn limit per subagent.** The field exists in frontmatter, was tested both possible ways, and
  **does not brake** in the measured version. Where the brake mattered — an evaluator that could
  respawn the debugger — the fix was removing the tool, which is deterministic.

---

## 10. What is still open

- **The spawn ceiling does not cover agents launched by a workflow**, which do not pass the same
  interception point. It holds for direct spawns. This matters more since 1.3.0, because the plugin
  now ships workflows: the ceilings that bound them are their own (`maxParallelWave`,
  `maxTasksPerPlan`, `maxRepatch`, and the round limit), declared in the config and enforced in the
  script rather than by the hook.
- **The ceiling numbers** (25 spawns per session, 8 rounds per agent) are starting points chosen
  above the limits already present in the workflows, not measured values. Calibrating them needs
  real usage data.
- **There is no automated eval** of the agents and skills. `claude plugin eval` exists, and using it
  is the natural next step — watching something fire is not the same as watching it work.
- **The Codex artefacts are machine-specific.** `.codex/hooks.json` and `.codex/agents/` embed the
  installed plugin's absolute path, because Codex expands no plugin variable. Each machine re-runs
  the installer, and the files are gitignored. A relative-path scheme would be better and does not
  exist yet.
