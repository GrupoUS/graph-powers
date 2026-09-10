> Hermes auxiliary: `content/` paths are `file_path` values relative to the registered-document parent. Apply the loaded graph-engineering mapping and host policy; this file is served without template expansion.

# Grok Build, Grok Bot and Cursor compatibility

Official contracts checked on 2026-09-10. Claude artefacts remain canonical; client generators
adapt the supported interfaces. A generated file, a discovered extension and a hook executed by a
native client are different evidence. Report which one was checked.

## Grok CLI / Grok Build

[Grok Build's extension documentation](https://docs.x.ai/build/features/skills-plugins-marketplaces)
describes native plugins and Claude compatibility. Keep the generated `.grok-plugin/` manifest
and the canonical `https://github.com/GrupoUS/graph-powers/blob/main/hooks/hooks.json`; do not install another copy of those hooks under user config.
The [settings reference](https://docs.x.ai/build/settings/reference) distinguishes plugin paths,
enabled/disabled lists and compatibility switches. A path alone does not establish activation.

Before changing approval posture, verify the exact package and its active discovery with
`grok inspect --json`. Match the enabled Graph Powers entry and its plugin hook source to the
verified root. An installed entry from `grok plugin list --json` is package inventory, not proof
that the current session loads it. An unavailable or malformed inventory is not an empty inventory
and must not trigger installation or trust. Preserve an explicit disabled setting or trust decision;
resolve it through the native client before requesting autonomous setup again. Guarded setup
can configure discovery without granting trust or changing approval posture.

Configuration edits target a conservative subset of [TOML](https://toml.io/en/v1.0.0), not the
entire language. An unsupported structure must stop installation without writing the configuration,
including under guarded policy. Preserve the operator's file and make that edit through the native
configuration interface instead of rewriting an unfamiliar structure.

The [hook contract](https://docs.x.ai/build/features/hooks) makes only `PreToolUse` blocking.
Passive events ignore stdout. Consequently, registering `SessionStart` or `SubagentStart` does
not prove that their Claude `additionalContext` reaches Grok. Supply the execution floor and
applicable method in the parent instructions and the canonical delegation handoff. Do not claim
that Stop verification blocks completion on Grok.

Local research used Grok 1.0.25: the existing installed package exposed its namespaced agents and
an enabled plugin through inspection. A disposable home with an untrusted clone exposed a disabled
plugin and no loaded skills/hooks despite a configured path and enabled list. This demonstrates
why package integrity cannot substitute for active discovery. Inspection plus a direct Python
guardrail probe still does not prove native end-to-end tool interception.

## Cursor

[Cursor's native plugin format](https://cursor.com/docs/reference/plugins) accepts the generated
manifest paths. Keep native hook event and matcher translation in the Cursor generator, rather
than maintaining another hook inventory.

[Cursor Hooks](https://cursor.com/docs/hooks) documents `additional_context` for `sessionStart`.
The generated command selects that response explicitly; Claude and Codex keep their existing
envelope. Cursor also has `subagentStart`, but its documented output is a permission decision and
a user message, not context injection. The canonical `https://github.com/GrupoUS/graph-powers/blob/main/hooks/subagent_context.py` registration therefore
remains omitted. This is an output-contract limitation, not a missing event. Put child context in
the delegation prompt.

IDE and CLI settings are separate. Merge their existing fields and lists, including unknown
fields inside `autoRun`; retain operator and team restrictions. Generated package checks and
sandbox hook execution do not certify the installed IDE's behavior. Verify a fresh native session
before reporting runtime parity.

## Grok Bot

[Grok Bot](https://docs.x.ai/grok-bot/overview) is a separate persistent agent product. Its
[skills documentation](https://docs.x.ai/grok-bot/skills-routines-and-automations) describes saved
skills, supported packaged skills under Settings → Plugins, and enabling private skills per Bot
under Plugins → Yours. It does not document a local `.grok-plugin/` manifest loader or the
Grok Build hook/configuration contract. Installing the desktop app or configuring the local CLI
does not establish a plugin installation inside a Bot's computer.

Use the supported skill surface when preparing Graph Powers work for a Bot:

1. Identify the Bot's workspace and available files. Make a reviewed Graph Powers source snapshot
   available there through an authorized file transfer or repository access.
2. Select the existing canonical method for the task; keep its referenced files available in the
   same snapshot. Resolve plugin-root references to that snapshot. Missing references are a
   blocker, not permission to replace the method with a summary.
3. Prepare the saved skill using the method's trigger, required inputs, steps, validation, return
   contract and approval boundaries. Use the supported Bot skill UI to save/enable it when that
   action is authorized. Do not maintain a second Graph Powers skill inventory in this repository.
4. Run a one-time, harmless example and inspect the result before considering a routine. Creating
   a routine is a separate request; a skill installation does not schedule work.

This is a preparation procedure, not a tested Bot installer. Bot hook enforcement, local plugin
loading and runtime parity remain **UNVERIFIED**. Native Bot permissions continue to govern actions;
the Python guardrails on the developer's computer do not protect a different cloud computer.

Installation entry points and package checks remain in [content/AGENT_SETUP.md](content/AGENT_SETUP.md).
