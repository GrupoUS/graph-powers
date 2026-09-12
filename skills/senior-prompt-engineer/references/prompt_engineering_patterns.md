# Prompt Engineering Patterns (application-level)

> Patterns for building Claude API / LLM features INSIDE the product (not Claude Code subagent design — see `agentic_system_design.md` for that).
> Use when a host project gains an AI feature: text generation, RAG over docs, structured output extraction, eval-driven iteration.

References (every number or "X beats Y" line below names one of these; an unsourced claim is a hypothesis for §6, not a rule):
- Prompting best practices (the living reference; the older per-technique pages redirect here): https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
- Thinking: https://platform.claude.com/docs/en/build-with-claude/thinking
- Structured outputs: https://platform.claude.com/docs/en/build-with-claude/structured-outputs
- Prompt caching: https://platform.claude.com/docs/en/build-with-claude/prompt-caching · pricing: https://platform.claude.com/docs/en/pricing
- Claude Fable 5.1 migration guide (forced tool choice): https://platform.claude.com/docs/en/models/fable-5-1/migration-guide
- Claude API: `claude-api` skill (auto-triggers on `@anthropic-ai/sdk` imports)

---

## 1. Pattern: XML-tagged structured input

The best-practices guide ("Structure prompts with XML tags") says tags help Claude parse a prompt that mixes instructions, context, examples and inputs; use them when a prompt has ≥2 distinct parts.

```xml
<role>You are a {role specific to the host product}.</role>

<voice_constraints>
{tone rules · forbidden patterns · required phrases — sourced from the host project's brand/voice skill}
</voice_constraints>

<task>{The job, why it matters, and the condition that means done — one line each. Completion defined up front is what lets the model finish instead of stopping to ask.}</task>

<input>
{json_dump(input_data)}
</input>

<output_format>
{Exact format Claude must return — JSON shape, max length, language, etc.}
</output_format>
```

**Why:** the guide reports that wrapping each kind of content in its own tag reduces misinterpretation; it asks for consistent, descriptive names (`<role>` ≡ `<persona>`) rather than a fixed set. Measure adherence with §6 before generalising.

---

## 2. Pattern: Few-shot before zero-shot

When a task has subjective output (copy, classification with edge cases, format extraction), add worked examples: the guide ("Use examples effectively") says "Include 3–5 examples for best results", well-crafted and diverse. Confirm the gain with §6.

```xml
<examples>
<example>
  <input>{ ... }</input>
  <output>{ ... }</output>
</example>
<example>
  <input>{ ... }</input>
  <output>{ ... }</output>
</example>
</examples>

<input>{ ... }</input>
```

Examples should span the **decision boundary** (one easy case, one hard case, one tricky case). Not 5 trivial cases.

---

## 3. Pattern: Chain-of-thought scaffold (opt-in)

Opt-in, not the default: the guide ("Thinking and reasoning") keeps manual chain-of-thought as a fallback for when thinking is off, and on Claude Opus 5 prefers thinking on at a lower effort instead. Use the scaffold for a multi-criteria judgement (gating an output, explaining a trade-off, applying domain rules) only when thinking is off. The default is a done condition in `<task>` (§1) plus a schema (§4); with thinking on — already on with no configuration on Claude Opus 5, Sonnet 5 and Fable 5.1 — skip the scaffold:

```xml
<task>Decide whether this output passes the gate.</task>

<input>{output}</input>

<reasoning_steps>
1. Identify the N criteria that apply.
2. List violations (criteria absent + anti-patterns present).
3. Verdict: PASS | REVISION_REQUIRED.
4. If REVISION_REQUIRED: propose minimal edits.
</reasoning_steps>

<output_format>
Return JSON: { "criteria": [...], "violations": [...], "verdict": "...", "edits": [...] }
</output_format>
```

The guide asks for sequential, numbered steps only when order or completeness matters ("Be clear and direct"); here they fix the output shape a parser reads, not the model's reasoning.

**Caveat:** the guide says to prefer general instructions over prescriptive steps — "think thoroughly" often beats a hand-written step-by-step plan — and keeps manual CoT as a fallback for thinking-off only. Never stack the scaffold on top of thinking (`thinking: {"type": "adaptive"}`); keep numbered steps only as an output contract. `ultrathink` is a Claude Code keyword, not an API parameter.

---

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

---

## 5. Pattern: Prompt caching for stable context

When prompts include large stable blocks (manuals, brand guides, schema docs), use prompt caching to skip re-tokenization on every call.

```python
client.messages.create(
  model="claude-opus-5",
  system=[
    {
      "type": "text",
      "text": stable_context_50kb,
      "cache_control": {"type": "ephemeral"}
    }
  ],
  messages=[{"role": "user", "content": user_prompt}]
)
```

**Cost (prompt-caching guide and pricing page):** cache reads bill at 0.1× the base input rate (0.025× on Claude Fable 5.1 and Claude Mythos 5.1); writes at 1.25× for the default 5-minute lifetime and 2× for `ttl: "1h"`; "the cache is refreshed for no additional cost each time the cached content is used". Verify hits with `usage.cache_read_input_tokens`. The minimum cacheable prefix is model-dependent (512 tokens on Claude Opus 5 and Fable 5.1, up to 4,096 on Claude Opus 4.6 and Haiku 4.5); shorter prefixes silently do not cache.

**Typical use cases:** brand/voice manuals for copy generators, doc corpus for RAG retrievers, schema reference for extraction.

---

## 6. Pattern: Eval-driven prompting

Don't iterate prompts on vibes. Build a small eval harness:

```python
test_cases = [
  {"input": {...}, "expected_traits": [...]},
  ...
]

def grade(output, traits):
  return sum(check(output, t) for t in traits) / len(traits)

# Run candidate prompt against every test case, score, average.
```

Each prompt mutation gets scored against the same fixed harness. Pick the highest-scoring variant — not the one that "feels best".

See `llm_evaluation_frameworks.md` for the full eval pattern + repo conventions for storing test cases.

---

## 7. Anti-patterns

| Anti-pattern | Why bad | Fix |
|---|---|---|
| "Be creative" / "Use your best judgment" | Underspecified → high variance | Specify decision criteria explicitly |
| Stacking 8 instructions in one paragraph | Adherence drops in an unstructured block; the guide asks for numbered steps when order or completeness matters | Use numbered list or XML sections |
| Asking for JSON without schema | Free-form output, brittle parsing | Use `output_config.format` or `strict: true` (§4) |
| Prompt-injecting user content | Untrusted text bypasses guardrails | Wrap user input in `<user_input>…</user_input>` and instruct Claude to treat it as data |
| Tweaking prompts without an eval | Drift; "improvements" regress on edge cases | Build minimal eval first |
| Hand-rolled CoT + extended thinking | Conflicting reasoning channels | Keep thinking; keep numbered steps only as an output contract (§3) |
| "Double-check your answer" as a ritual | Tokens, not evidence; a self-review is not an eval | Gate the output with a schema (§4) and score it with the harness (§6) |
| The whole corpus in every prompt | Cost, and nothing marks what matters | Retrieve or cache the stable part (§5); name the job and the done condition (§1) |

---

## 8. Project hookup

- Brand voice / domain taxonomy / forbidden terms live in the host project's domain skill (e.g., `<brand>` skill, `<product>` skill). Preload that skill when building generators or judges.
- For Karpathy-style optimize loops over prompts/skills, use a project-bound autoresearch skill — frozen harness, append-only `experiments.tsv`, crash discipline.
- For migrations between Claude API model versions or new SDK apps, route through the `claude-api` skill.

Owner: `senior-prompt-engineer` skill.
