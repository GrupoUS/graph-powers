---
description: "Load this project's context at the start of a session — rules, conventions, stack, the paths that matter. Use when the user asks to load context, get up to speed, or what the conventions here are. Modes (positional) — default: auto-classify · backend · frontend · fullstack. Loads the minimum viable context, never eagerly. Do not use to locate one specific thing (/research)."
workflow_type: augmented-llm
---

# /prime — Intelligent Context Loader

**ARGUMENTS**: $ARGUMENTS

> **Read before step 0 — never reconstruct these from memory:** `${CLAUDE_PLUGIN_ROOT}/references/shared/000-config-loader.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/005-superpowers-bootstrap.md` · `${CLAUDE_PLUGIN_ROOT}/references/shared/020-complexity-routing.md`
>
> Those three, and nothing else. A context loader that opens by loading the agent matrix and the
> guardrail index has already lost the argument it is making. Spawning is the execution floor's, and
> the floor is in force without being read here.

> First positional arg = scope. Examples:
> ```
> /prime                  # auto-classify intent, then load
> /prime backend          # backend-focused (rules + recent backend changes)
> /prime frontend         # frontend-focused (rules + recent frontend changes)
> /prime fullstack        # multi-domain
> ```

---

## Goal

Load **minimum-viable** project context for the current task. Never eager-load everything.

Tier model:
- **Tier 1** (always loaded by harness): root `AGENTS.md` + `.claude/CLAUDE.md`
- **Tier 2** (load on demand): the rule files the project actually wrote under `${rulesDir}/` — list the directory, match on each file's `paths:`, and read only what matches
- **Tier 3** (load only when justified): `docs/`, ADRs, learnings, design specs, spec docs

Plus optional project supplements under `${rulesDir}` (routing supplements, anti-patterns, layer maps, project snapshot, Tier 3 docs).

---

## 0. Setup (every mode)

`/prime` is a context loader — it does not mutate code, so it does NOT invoke the superpowers bootstrap itself. Instead, surface a one-line recommendation at the end of the output (per `${CLAUDE_PLUGIN_ROOT}/references/shared/005-superpowers-bootstrap.md`): the **next** command should load `Skill("superpowers:using-superpowers")` as its first skill call.

Read `.graph-powers/config.json`. Note `${paths.*}` and `${rulesDir}` for later loading.

If continuing a prior session: read `.graph-powers/HANDOFF.md` first when it exists — it is written by `/evolve handoff` and is the only place session state lives.

Run:
```bash
git status --short
git log --oneline -10
```

If `${rulesDir}/routing-supplements.md` exists, note it for stage 2 deep loading.

### 0.1 Auto-research flag (default ON for L3+)

If `$ARGUMENTS` contains `--no-auto-research` → skip. Otherwise on **L3+ intent** (per `${CLAUDE_PLUGIN_ROOT}/references/shared/020-complexity-routing.md` — Complexity Routing`), spawn discovery agents BEFORE returning prime output:

```ts
Agent({ subagent_type: "graph-powers:explorer",  run_in_background: true, prompt: "<scoped repo discovery>" })
Agent({ subagent_type: "graph-powers:librarian", run_in_background: true, prompt: "<external doc lookup>" })
```

Both calls go in the SAME assistant turn (parallel). Non-blocking — return prime output while they run; their results merge on the next user turn. The rule behind that is the execution floor's §1 and §2; this command only names the moment it applies.

If discovery agents return conflicting signals about scope/architecture, invoke `mcp__sequential-thinking__sequentialthinking` to reconcile **before** dispatching a stage. L4+ MUST · L3 SHOULD · L1-L2 skip.

---

## 1. Mode dispatch

Parse the first positional token from `$ARGUMENTS`, then read **only** the matching section of the
staging reference. Reading more than one is the failure this table exists to prevent.

| Token | Then read |
|---|---|
| (none) / `auto` / `cross` | § 2 below (auto-classify), which then picks one of the three |
| `backend` / `api` / `db` | read `${CLAUDE_PLUGIN_ROOT}/references/shared/045-context-staging.md` § 4.5a |
| `frontend` / `ui` / `react` | read `${CLAUDE_PLUGIN_ROOT}/references/shared/045-context-staging.md` § 4.5b |
| `fullstack` / `multi` | read `${CLAUDE_PLUGIN_ROOT}/references/shared/045-context-staging.md` § 4.5c |

---

## 2. Auto-classify mode (default)

Read user task description from `$ARGUMENTS` (after the mode token, if any). Classify intent:

| Signal | Classify as | Then read |
|---|---|---|
| React / UI / layout / styling / component / page | frontend-heavy | staging § 4.5b |
| API / handler / route / middleware / service / validator | backend-heavy | staging § 4.5a |
| Schema / migration / RLS / FK / index / enum | backend (data) | staging § 4.5a, schema emphasis |
| External provider / webhook / payment / email / monitoring | integration-heavy | staging § 4.5a, integration rule first |
| UI + API + schema | fullstack | staging § 4.5c |
| Vague / exploratory | partial — see § 2.1 | — |

### 2.1 Vague task

Don't load eagerly. Output:

```
Project: ${project.name} | Branch: {branch}
Intent: unclear
Recommended next: ask user "Is this primarily frontend, backend, integration, or cross-domain?"
```

---

## 3. Anti-bloat rules (all modes)

- Never use `/prime` as "read every rule and every reference"
- Never load both full architecture and full design-spec sets unless task truly spans both
- Never preload historical learnings unless task suggests debugging / performance / edge cases / prior-bug-sensitive areas
- Prefer **one targeted reference** over multiple broad references
- If unsure → load index/README first, never the children
- Stop after the minimum sufficient load

---

## 4. Output format

```
Project: ${project.name} | Mode: {auto|backend|frontend|fullstack} | Stage: {1-4}
Branch: {branch} | Recent: {summary of git log -5}
Loaded:
  - {exact files actually loaded}
Supplements applied: {yes/no — list `${rulesDir}` supplement files actually loaded}
Next on demand: {only the most relevant additional files}
Ready for: {task description or "awaiting task"}
Reminder: next command should open with Skill("superpowers:using-superpowers").
```

Keep summary under 120 words.

---

## 5. Stop conditions

- Stop after § 0 if the task hasn't been provided
- Stop after the minimum sufficient deep load
- If task becomes destructive / payment-related / auth-changing / schema-changing → flag before implementation
- If > 4 files seem necessary in one stage → reassess classification
