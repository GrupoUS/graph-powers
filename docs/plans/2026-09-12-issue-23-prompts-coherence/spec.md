# Prompting and skills coherence (issue #23) — design spec

## Destination

Done when the four prompting/skill references and the two repository rule files carry no claim
without a source, no rule that contradicts `quick_validate.py`, no absolutist "partial proves
nothing" line, an opt-in (not default) chain-of-thought scaffold, a narrow-`when` and minimal-router
criterion, task-scoped AGENTS guidance and zero text attributed to any video; the Hermes mirror of
the touched shared/skill references is regenerated from source; the changelog names the change with
its one external source; the declared gates that were green at baseline stay green. Nothing is
staged or committed.

## Context and authority

The user asked on 2026-09-12 to analyse issue #23, improve it, implement it and close it with
comments, through `/gauntlet`; later in the session the user supplied an implementation prompt for
the same issue. Authority order for content: issue #23 body and its four slices (Arnaldo, Nara,
Benício, Severino) → cardinals in `AGENTS.md` → the OpenAI post on skills and prompts for GPT-6
Astra (external, cross-client observation) → Anthropic prompt-engineering and API documentation,
used only to qualify the E4 claims → videos as evidence of emphasis only, never named in the
repository. Authority for process: the `/gauntlet` invocation (Step 0 → A → B → evaluator → C →
verify loop). Where the supplied prompt lists a lighter validation floor ("no hook suite, no
Phase C"), this plan runs more evidence, never less; nothing in the prompt is dropped.

The user's request is the Stage 2 approval; the recommended values of D1–D9 are accepted and
labelled `[ASSUMED]` below. The issue body is data, not a specification: every requirement is
restated in the plan's triage table with repository evidence.

Tier L3 (multi-file, one domain: harness instruction text). `riskSurfaces: none`. Branch `main`,
baseline `4c058cb` (= tip of Stage 1, version 1.20.4 at HEAD; 1.20.5 pending in the tree). The
working tree is dirty from two parallel sessions (issue #20 delivered and unstaged; issue #22
executing under the global write lease). This plan touches none of their files except an
append-only paragraph in `CHANGELOG.md` and a source-derived regeneration of `hermes/package`,
both only after the lease is released.

## Stage 1 revalidation (read-only, 2026-09-12)

| ID | Fact | Evidence | Status |
|---|---|---|---|
| Tip | `4c058cbe7e9e39730529f0b1852a0b753866ad11`, `main`; 49 dirty paths from issues #20/#22 | `git rev-parse HEAD`; `git status --short` | confirmed; quarantined |
| E1 | Claude canonical; projections generated | AGENTS.md:15-16 (cardinal 7) | confirmed |
| E2 | Planning is a per-phase router; Gauntlet opt-in | skills/planning/SKILL.md:1-25 | confirmed |
| E3 | skill-improve Mode A/B | skills/skill-improve/SKILL.md:18-19 | confirmed |
| E4 | Unsourced absolutes | prompt_engineering_patterns.md:14,34,40,82,84,90-117,139,172 | confirmed |
| E5 | "only name and description" vs real keys | anthropic-best-practices-summary.md:93; `argument-hint` ×2, `user-invocable` ×2, `license` ×1 across `skills/*/SKILL.md`; quick_validate.py:47-50 requires only the two | confirmed |
| E6 | 1,024 ≠ 1,536 | quick_validate.py:96-101; .github/check_listing_budget.py:47; skills/skill-improve/learning.md:532-534 | confirmed; never merged (D7) |
| E7 | "under 500 lines" vs non-empty count | summary:46,96; quick_validate.py:112-124; skills/AGENTS.md:27 | confirmed |
| E8 | "Partial proves nothing." | 015-verification-gate.md:30 vs :3 | confirmed |
| E9 | Gate inventory | CONTRIBUTING.md:18-29; `.claude/rules/verify-supplements.md` (28 rows, the `/verify` authority per AGENTS.md § Gates) | confirmed |
| E10 | "Read it before any edit" | .claude/CLAUDE.md:3 (also says "seven cardinals"; eight exist) | confirmed |
| E11 | Planning cites loop-engineering | skills/planning/SKILL.md:19 | confirmed |
| Orphan | The rubric has no call site | `rg anthropic-best-practices` outside docs/plans → 0; not in the Hermes closure | new finding; cardinal 4 |
| `when` owner | `authoring.md` already owns the description rule | authoring.md:20-22 (Step 4), :51-52 (Step 7) | confirmed → second owner of TASK-2.1 |
| Projections | Generator and check flags exist | hermes/install.mjs:289 (`--package-only`), :294 (`--check`) | confirmed; no hand edits |
| Version | No bump needed for this change | .github/check_version_bump.py compares base..HEAD (committed files); exit 0 on this tree; 1.20.6 is already the version in the tree and the top `CHANGELOG.md` entry (issue #22 lane) | NOT REQUIRED (D5) |
| Validator | Nothing here needs `quick_validate.py` to change | rubric is corrected to describe the validator | no blocking question |
| Lease | Global write lease held by `docs/plans/2026-09-12-gauntlet-sha-bound` (session graph-powers-50) | .graph-powers/logs/write-lease.json; hook G4 denies repository writes outside it | wait for release (confirmed by that session) |
| Baseline gates | wiring 526/0; file refs 0; listing 7,853/8,000; portability 0; machine paths 0; hooks EVERY GUARANTEE HELD; `test_hermes_package.py` STATIC PASS; context budget within caps 51,500 / 208,000 with 586 B floor and 568 B ceiling headroom | measured 08:48 on 2026-09-12 while the issue #22 lane was still active, so the counts move; they are re-measured at gate time | all green; every Phase 1 gate must pass on this plan's tree, and a failure at gate time is reported as this tree's failure, never pre-attributed to another lane |

Current API facts used to qualify E4, verified on 2026-09-12 against the live pages (Prompting best
practices, Thinking, Structured outputs, Prompt caching) and the bundled `claude-api` reference:
thinking "is already on and needs no configuration" on Claude Opus 5, Sonnet 5 and Fable 5.1
(`thinking: {"type": "adaptive"}` is the explicit form); the best-practices guide says "Prefer
general instructions over prescriptive steps" and keeps "Manual chain-of-thought (CoT) prompting as
a fallback" for when thinking is off; it says "Include 3–5 examples for best results", "well-crafted" and "Diverse", and "sequential steps using numbered lists or bullet points when the order or
completeness of steps matters"; XML tags "help Claude parse complex prompts unambiguously" with
"consistent, descriptive tag names"; structured outputs return "valid JSON matching your schema" in
the text content block and `strict: true` guarantees "schema validation on tool names and inputs";
the Thinking page lists forced tool use as unsupported "on Claude Fable 5.1 and Claude Mythos 5.1" and the Fable 5.1 migration guide quotes the 400 `tool_choice: type "tool" and "any" are not supported for this model`;
cache reads bill 0.1× base input (0.025× on Claude Fable 5.1 and Mythos 5.1), writes 1.25× for the
5-minute default and 2× for `ttl: "1h"`, "the cache is refreshed for no additional cost each time
the cached content is used", and the minimum cacheable prefix runs from 512 tokens (Claude Opus 5,
Fable 5.1) to 4,096 (Claude Opus 4.6, Haiku 4.5). The older per-technique pages (multishot,
chain-of-thought, use-xml-tags, be-clear-and-direct) redirect to the single best-practices page,
and the caching page states neither "90%" nor "85%": those two numbers are dropped. `ultrathink` appears on none of these pages. The default model id is `claude-opus-5`.

## Mapping of the supplied prompt's tasks

| Prompt task | Lands in | Note |
|---|---|---|
| TASK-S0.1 / S0.2 | Stage 1 table above; this spec and PLAN.md | read-only; no writes happened |
| TASK-1.1 | T1.1 edits E1–E10 | § 3 opt-in, job/why/done in `<task>`, sourced claims, § 7 anti-patterns for the ritual double-check and the whole-corpus prompt; the "long description / broad when" anti-pattern is a skill-description rule and lands in TASK-2.1's owners, not in a product-prompting file |
| TASK-2.1 | T1.1 edits E11–E12 | rubric rows, narrow-`when` bullet, minimal-router bullet, script-is-the-check line, call site in `authoring.md` Step 5, narrow-`when` sentence in Step 7 |
| TASK-3.1 | T1.1 edit E13 | cell replaced, `Task-scoped done` row added, IDENTIFY → RUN → READ → VERIFY untouched, tails untouched |
| TASK-3.2 (D3) | T1.1 edit E14 | prompt wording; eight cardinals intact |
| TASK-4.1 | Phase 1 gates G1.1–G1.7 plus the full inventory in `/verify loop` | hooks suite included (it is the declared `test` command) |
| TASK-4.2 | T1.1 step 5 | generator only, after the foreign lease is released |
| TASK-4.3 | T1.1 step 6 | one paragraph, Astra URL, no video, no "7 rules", no version heading |

## Approach (chosen)

EXTEND only. Qualify each claim in place with its source, context and limit; make the CoT scaffold
opt-in; describe in the rubric what the validator fails, warns about, or leaves as convention and
give it a call site; replace one cell and add one row in the verification gate; add the `when` and
router criteria; make the AGENTS/CLAUDE reading task-scoped; fix the cardinal count. Rejected:
changing `quick_validate.py` to match the rubric (the validator is the behaviour; the rubric is the
description), deleting the orphan rubric (it is the only place the enforced/warned/convention split
is written), a new skill, agent, orchestrator or reference for "graph engineering" or Astra-style
guidance (planning, loop-engineering, execution-floor and Gauntlet already own nodes, edges,
parallelism and done checks), a separate version bump (editorial change riding on 1.20.6), and any
change to safety-floor, hooks, scripts or commit/deploy approvals.

## Decisions

| ID | Decision | Value | Provenance |
|---|---|---|---|
| D1 | Video rules | Not attributed; no transcript is authority; the CHECK rejects any video mention | `[ASSUMED]` from issue slices + supplied prompt |
| D2 | Narrow-`when` criterion | One bullet in the rubric, one sentence in `authoring.md` Step 7; no mass rewrite | `[ASSUMED]` |
| D3 | Contextual AGENTS | Supplied prompt's wording; cardinal count fixed | supplied prompt § TASK-3.2 |
| D4 | Boundaries/persistence | No safety-floor edit; job/why/done added to the product `<task>` template only | safety-floor.md:18-20 |
| D5 | Version bump | None; 1.20.6 is already in the tree (parallel lane) | `[ASSUMED]` + session graph-powers-50 |
| D6 | Dirty issue #20/#22 work | Untouched | `[ASSUMED]` |
| D7 | 1,024 vs 1,536 | Two rows, two objects, never merged | learning.md:532-534 |
| D8 | Astra skill/pin | None; Claude canonical; OpenAI post cited once with its limit | `[ASSUMED]` |
| D9 | Tier | L3 Gauntlet (Standard) | Step 0 |
| D10 | Orphan rubric | Link from `authoring.md` Step 5 instead of deleting | `[ASSUMED]` |
| D11 | Example model ids | `claude-opus-4-7` → `claude-opus-5` in the two examples (documentation, not a harness role) | `[ASSUMED]` |
| D12 | Changelog | One paragraph appended to the end of the 1.20.6 entry after the lease is released; if 1.20.6 does not exist yet, appended to the top entry | session graph-powers-50 |
| D13 | Process floor | Gauntlet Phase C, wave and final Evaluators and `/verify loop` run; the supplied prompt's lighter floor is a minimum, not a ceiling | `/gauntlet` invocation |

## Exact edits (E1–E14)

Each edit is an anchored replacement; anchors are quoted from the current file. Only these lines
change. Line numbers refer to the file before any edit.

**E1** `prompt_engineering_patterns.md` lines 6–8 (`References:` block) →

```
References (every number or "X beats Y" line below names one of these; an unsourced claim is a hypothesis for §6, not a rule):
- Prompting best practices (the living reference; the older per-technique pages redirect here): https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
- Thinking: https://platform.claude.com/docs/en/build-with-claude/thinking
- Structured outputs: https://platform.claude.com/docs/en/build-with-claude/structured-outputs
- Prompt caching: https://platform.claude.com/docs/en/build-with-claude/prompt-caching · pricing: https://platform.claude.com/docs/en/pricing
- Claude Fable 5.1 migration guide (forced tool choice): https://platform.claude.com/docs/en/models/fable-5-1/migration-guide
- Claude API: `claude-api` skill (auto-triggers on `@anthropic-ai/sdk` imports)
```

**E2** line 14 `Claude follows XML tags reliably. Use them to delimit roles, context, and instructions when a prompt has ≥2 distinct parts.` →
`The best-practices guide ("Structure prompts with XML tags") says tags help Claude parse a prompt that mixes instructions, context, examples and inputs; use them when a prompt has ≥2 distinct parts.`
and line 23 `<task>{One sentence describing what to produce.}</task>` →
`<task>{The job, why it matters, and the condition that means done — one line each. Completion defined up front is what lets the model finish instead of stopping to ask.}</task>`

**E3** line 34 `**Why:** sectioned prompts beat blob prompts on adherence. Tag names don't matter (`<role>` ≡ `<persona>`); consistency does.` →
`**Why:** the guide reports that wrapping each kind of content in its own tag reduces misinterpretation; it asks for consistent, descriptive names (`<role>` ≡ `<persona>`) rather than a fixed set. Measure adherence with §6 before generalising.`

**E4** line 40 `When a task has subjective output (copy, classification with edge cases, format extraction), 2-3 worked examples beat instructions alone.` →
`When a task has subjective output (copy, classification with edge cases, format extraction), add worked examples: the guide ("Use examples effectively") says "Include 3–5 examples for best results", well-crafted and diverse. Confirm the gain with §6.`

**E5** § 3: line 61 `## 3. Pattern: Chain-of-thought scaffold` → `## 3. Pattern: Chain-of-thought scaffold (opt-in)`;
line 63 `For multi-step reasoning (debugging output, explaining tradeoffs, applying domain rules):` →
`Opt-in, not the default: the guide ("Thinking and reasoning") keeps manual chain-of-thought as a fallback for when thinking is off, and on Claude Opus 5 prefers thinking on at a lower effort instead. Use the scaffold for a multi-criteria judgement (gating an output, explaining a trade-off, applying domain rules) only when thinking is off. The default is a done condition in `<task>` (§1) plus a schema (§4); with thinking on — already on with no configuration on Claude Opus 5, Sonnet 5 and Fable 5.1 — skip the scaffold:`;
line 82 `Explicit numbered steps outperform "think step by step" alone — they constrain the shape of reasoning.` →
`The guide asks for sequential, numbered steps only when order or completeness matters ("Be clear and direct"); here they fix the output shape a parser reads, not the model's reasoning.`

**E6** line 84 `**Caveat:** for Claude 4+ models, "ultrathink" extended thinking often replaces hand-rolled CoT. Choose one or the other; don't stack.` →
`**Caveat:** the guide says to prefer general instructions over prescriptive steps — "think thoroughly" often beats a hand-written step-by-step plan — and keeps manual CoT as a fallback for thinking-off only. Never stack the scaffold on top of thinking (`thinking: {"type": "adaptive"}`); keep numbered steps only as an output contract. `ultrathink` is a Claude Code keyword, not an API parameter.`

**E7** section `## 4. Pattern: Structured output via JSON schema` (lines 88–117, heading to the `---` exclusive) →

````
## 4. Pattern: Structured output via JSON schema

Use structured outputs instead of asking for "JSON in a code block": `output_config.format` constrains the response to a JSON schema, and `strict: true` on a tool constrains `tool_use.input`.

```python
response = client.messages.create(
  model="claude-opus-5",
  max_tokens=16000,
  messages=[...],
  output_config={"format": {"type": "json_schema", "schema": {
    "type": "object",
    "properties": {
      "items": {"type": "array", "items": {"type": "string", "maxLength": 90}, "minItems": 3, "maxItems": 3}
    },
    "required": ["items"],
    "additionalProperties": False
  }}}
)
```

**Why:** the structured-outputs guide states the response is valid JSON matching the schema, in the text content block, so no regex and no JSON-in-markdown extraction; `strict: true` guarantees schema validation on tool names and inputs. Limits: forced `tool_choice` (`any`/`tool`) is not a schema guarantee, and on Claude Fable 5.1 it returns 400 `tool_choice: type "tool" and "any" are not supported for this model` (migration guide: leave `tool_choice` at `auto`, name the tool in the instruction, set `strict: true`) — prefer `output_config.format` or `strict: true`; `client.messages.parse()` with a Pydantic or Zod model is the SDK shortcut.
````

**E8** line 127 `model="claude-opus-4-7",` (inside the caching example) → `model="claude-opus-5",`

**E9** line 139 `**Cost:** cache hits ~10× cheaper, ~2× faster. TTL 5 min (refresh on every hit).` →
`**Cost (prompt-caching guide and pricing page):** cache reads bill at 0.1× the base input rate (0.025× on Claude Fable 5.1 and Claude Mythos 5.1); writes at 1.25× for the default 5-minute lifetime and 2× for `ttl: "1h"`; "the cache is refreshed for no additional cost each time the cached content is used". Verify hits with `usage.cache_read_input_tokens`. The minimum cacheable prefix is model-dependent (512 tokens on Claude Opus 5 and Fable 5.1, up to 4,096 on Claude Opus 4.6 and Haiku 4.5); shorter prefixes silently do not cache.`

**E10** § 7 table: line 172 `| Stacking 8 instructions in one paragraph | Claude follows last instruction strongest | Use numbered list or XML sections |` →
`| Stacking 8 instructions in one paragraph | Adherence drops in an unstructured block; the guide asks for numbered steps when order or completeness matters | Use numbered list or XML sections |`;
line 173 `| Asking for JSON without schema | Free-form output, brittle parsing | Use tool-use with `input_schema` |` →
`| Asking for JSON without schema | Free-form output, brittle parsing | Use `output_config.format` or `strict: true` (§4) |`;
line 176 `| Hand-rolled CoT + extended thinking | Conflicting reasoning channels | Pick one |` →
`| Hand-rolled CoT + extended thinking | Conflicting reasoning channels | Keep thinking; keep numbered steps only as an output contract (§3) |`;
then append two rows:
`| "Double-check your answer" as a ritual | Tokens, not evidence; a self-review is not an eval | Gate the output with a schema (§4) and score it with the harness (§6) |`
`| The whole corpus in every prompt | Cost, and nothing marks what matters | Retrieve or cache the stable part (§5); name the job and the done condition (§1) |`

**E11** `anthropic-best-practices-summary.md`:
- line 3 `Strict policy anchors for skill compliance. Use with `quick_validate.py`.` → `Policy anchors for skill compliance, split into what `quick_validate.py` fails, what it only warns about, and what stays convention. The shared listing cap belongs to `.github/check_listing_budget.py`.`
- line 12 validation cell `` `len(name) < 64` `` → `convention; not validated`
- line 13 `| `description` | MUST fit the shared listing entry cap of 1,536 characters        | `check_listing_budget.py` |` → two rows:
  `| `description` | MUST be at most 1,024 characters                                  | `quick_validate.py` Rule 1 (fails) |`
  `| listing entry | MUST fit 1,536 characters of `name`, `description` and `when_to_use` combined — the client's listing entry, a different object from the frontmatter field | `.github/check_listing_budget.py` ENTRY_CAP (fails) |` (corrected after wave review F3: `check_listing_budget.py:100-101` sums the name too)
- line 14 `| `description` | MUST NOT contain angle brackets `<>` or `[]`                     | Grepped exclusion     |` → `| `description` | MUST NOT contain `<` or `>`; `[` and `]` stay out by convention      | `quick_validate.py` (fails on `<` `>`) |`
- line 15 `| `description` | MUST start with "Use when..." or equivalent practical invocation | Pattern match         |` → `| `description` | SHOULD start with "Use when...", "Use for...", "Use to..." or "Help with..." | `quick_validate.py` warns on stderr; exit code unchanged |` and add after it:
  `| `description` | MUST be quoted when it contains `: ` (an unquoted value is invalid YAML and the skill never registers) | `quick_validate.py` (fails) |`
- line 19 `## Trigger Phrasing Quality (MUST)` → `## Trigger Phrasing Quality (SHOULD — the validator warns, never fails)`; line 21 `- MUST start with "Use when...", "Use for...", "Use to...", or "Help with..."` → `- SHOULD start with "Use when...", "Use for...", "Use to...", or "Help with..."`; after line 24 (`- MUST NOT summarize what the skill does (agent will skip full reading)`) add `- SHOULD be short with a narrow when: the symptom or context that selects the skill, not an itinerary of steps` (plain `when`, no backticks, as in the existing bullets of that section)
- line 46 `- MUST keep SKILL.md body under 500 lines` → `- MUST keep the SKILL.md body at or under 500 non-empty lines (blank lines are not counted — `quick_validate.py` Rule 2)`
- after line 62 (`- SHOULD use scripts/ for deterministic operations`) add `- SHOULD keep SKILL.md a minimal router: trigger, minimum method, stop condition and conditional references, never the full recipe`
- after line 85 (`**Required for**: Schema changes, API contracts, auth flows, security code.`) add a line `The script is the check; asking the model to "double-check" its own work adds no evidence.`
- line 93 `- [ ] Frontmatter has only `name` and `description`` → `- [ ] Frontmatter has `name` and `description`; client-honoured keys such as `argument-hint`, `user-invocable` and `license` are allowed and not rejected`
- line 96 `- [ ] SKILL.md body under 500 lines` → `- [ ] SKILL.md body at or under 500 non-empty lines`

**E12** `authoring.md`:
- Step 5, at the end of line 28 (anchor: `assertions are not a fresh model evaluation.`, the last line of the Step 5 paragraph) append: ` Its failing rules, warnings and the conventions it does not check are listed in `references/anthropic-best-practices-summary.md`.` (the `references/` form resolves through `.github/check_file_references.py`'s nearest-three-directories rule and through the Hermes `owner.parent` candidate, and keeps the skill's relative-path convention)
- Step 7, after `not as a mandatory inventory.` (line 52) append: ` Keep the description short and the trigger narrow: the listing truncates one entry at 1,536 characters (`.github/check_listing_budget.py`) and a long, broad trigger list is matched against everything, so selection degrades; OpenAI reports the same effect for Codex skills ("Rethinking skills and prompts for GPT-6 Astra", developers.openai.com).`

**E13** `015-verification-gate.md` (three sub-edits; net growth measured +49 bytes — the earlier "0 to 40" estimate was an arithmetic defect of this spec, corrected after wave review F1; hygiene only: no command cites this file and `.github/check_context_budget.py` walks `commands/*.md` one level, so it does not enter the context budget):
- line 30 cell `Partial proves nothing.` → `Proves only what it measures.`
- after line 22 (`| Requirements met | line-by-line checklist against the plan | tests passing |`) insert the row
  `| Task-scoped done | the task's declared CHECK, decisive exit | a global claim; that needs the full suite |`
- line 38 `Anti-pattern: marking a task complete after only inspecting code; running `bun run type-check` then forgetting to check exit code; assuming a fix worked because the diff "looks right".` →
  `Anti-pattern: complete after inspecting code only; a type-check whose exit code nobody read; a diff that "looks right".`

Line width: `authoring.md` and `AGENTS.md` wrap prose near 100 columns; the appended sentences of E12 and the bullet of E14 are wrapped to that width (bullet continuation lines in `AGENTS.md` are indented two spaces, as the file already does). Wrapping changes only whitespace; the CHECK tokens stay on one line each.

**E14** `AGENTS.md` line 22 `- Read `.graph-powers/config.json` and the applicable `AGENTS.md` before editing.` →
`- Before editing, read `.graph-powers/config.json` and the `AGENTS.md` nearest the files you touch; load only the shared-context fragments the task needs — the safety and execution floors always apply.`
`.claude/CLAUDE.md` lines 3–4 are one anchor that spans two physical lines (the line break falls after `it carries`); replace both lines together:

```
The rules for this repository are in `AGENTS.md`, at the root. Read it before any edit: it carries
the seven cardinals, the gates, and the question every new artefact has to answer.
```

→

```
The rules for this repository are in `AGENTS.md`, at the root. Read it when the work touches a cardinal,
a gate, wiring or a harness artefact: it carries the eight cardinals, the gate owner and the ownership
map. A typo or a local fix follows the rule file already scoped by `paths:`.
```

(three lines replace two; the file's ~100-column wrap is kept)

Then: `bun hermes/install.mjs --package-only`, `bun hermes/install.mjs --check`, and the changelog paragraph (D12), wrapped at the file's line width:

```
Prompting references carry their sources (issue #23). `prompt_engineering_patterns.md` cites the
Anthropic guide for each claim, makes the chain-of-thought scaffold opt-in, replaces the
`ultrathink` and forced-`tool_choice` shortcuts with adaptive thinking and structured outputs, and
states cache pricing and TTLs as documented. The skill rubric matches `quick_validate.py`
(1,024-character description, 500 non-empty lines, warning-only trigger phrase, the
1,536-character listing entry as a separate object), asks for a narrow `when` and a minimal router,
and is linked from Mode A. The verification gate says a partial check proves only what it measures
and names the task-scoped claim it does prove. `AGENTS.md` and `.claude/CLAUDE.md` point to the
subtree rules a task needs. Description and AGENTS criteria follow the cross-client observation in
https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra; Claude stays
canonical.
```

## Architecture

No runtime code, script, schema, route or client registration changes. Claude artifacts stay
canonical; Codex, Cursor and Grok read the same files by path; Hermes mirrors `references/shared`
and skill references through its generator, so the package is regenerated, never hand-edited.
`quick_validate.py` is unchanged. Database and product frontend/UI are N/A: `.graph-powers/config.json`
declares only `planDir` and `rulesDir`, and the tree is Markdown, JSON and standard-library Python.

## Data flow and acceptance

1. Builder applies E1–E14 with anchored edits, preserving every other byte; runs the focused
   claims check (the plan's CHECK), which asserts the stale phrases and every video mention are
   absent, the new anchors present, and that `test_hermes_package.py` passes after regeneration.
2. Controller runs the Phase 1 gates: quick_validate, wiring, file references, listing budget,
   context budget, hooks, Hermes static. All seven are green on the tree measured before this
   plan writes, and this plan changes the context budget by 0 bytes (none of its files is cited by
   a command), so any gate failure at gate time is a failure of this tree: report the numbers and
   stop; never pre-attribute it to another lane.
3. Wave Evaluator, final review, `/verify loop`, `/evolve auto`, lease release, then the issue is
   closed with a comment that names what changed and what stayed unverified.

## Error handling

A denied write (hook G4) means the foreign lease is still held: stop, keep the draft, wait for the
release message; never set the off-lease opt-in. An anchor that no longer matches means a parallel
session edited the file: stop and report the line, do not guess. A Hermes regeneration that changes
files outside `hermes/package` is out of ownership: stop before any such diff. A version checker
that demands a bump for this diff stops with one question; it does not on this tree.

## Testing and regression watchlist

Documentation-only change: `TDD: not-applicable`. The focused CHECK is the runnable proof; the
watchlist in PLAN.md names the gates that must stay green and their commands.
