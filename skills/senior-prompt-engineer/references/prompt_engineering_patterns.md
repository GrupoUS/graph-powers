# Prompt Engineering Patterns (application-level)

> Patterns for building Claude API / LLM features INSIDE the product (not Claude Code subagent design — see `agentic_system_design.md` for that).
> Use when a host project gains an AI feature: text generation, RAG over docs, structured output extraction, eval-driven iteration.

References:
- Anthropic prompt design: https://docs.claude.com/en/docs/build-with-claude/prompt-engineering
- Claude API: `claude-api` skill (auto-triggers on `@anthropic-ai/sdk` imports)

---

## 1. Pattern: XML-tagged structured input

Claude follows XML tags reliably. Use them to delimit roles, context, and instructions when a prompt has ≥2 distinct parts.

```xml
<role>You are a {role specific to the host product}.</role>

<voice_constraints>
{tone rules · forbidden patterns · required phrases — sourced from the host project's brand/voice skill}
</voice_constraints>

<task>{One sentence describing what to produce.}</task>

<input>
{json_dump(input_data)}
</input>

<output_format>
{Exact format Claude must return — JSON shape, max length, language, etc.}
</output_format>
```

**Why:** sectioned prompts beat blob prompts on adherence. Tag names don't matter (`<role>` ≡ `<persona>`); consistency does.

---

## 2. Pattern: Few-shot before zero-shot

When a task has subjective output (copy, classification with edge cases, format extraction), 2-3 worked examples beat instructions alone.

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

## 3. Pattern: Chain-of-thought scaffold

For multi-step reasoning (debugging output, explaining tradeoffs, applying domain rules):

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

Explicit numbered steps outperform "think step by step" alone — they constrain the shape of reasoning.

**Caveat:** for Claude 4+ models, "ultrathink" extended thinking often replaces hand-rolled CoT. Choose one or the other; don't stack.

---

## 4. Pattern: Structured output via JSON schema

Use Claude's tool-use API to enforce schemas instead of asking for "JSON in a code block".

```python
tools = [{
  "name": "submit_result",
  "description": "Submit the structured result",
  "input_schema": {
    "type": "object",
    "properties": {
      "items": {
        "type": "array",
        "items": { "type": "string", "maxLength": 90 },
        "minItems": 3, "maxItems": 3
      }
    },
    "required": ["items"]
  }
}]

response = client.messages.create(
  model="claude-opus-4-7",
  tools=tools,
  tool_choice={"type": "tool", "name": "submit_result"},
  messages=[...]
)
```

**Why:** the API rejects malformed output before it reaches your app. No regex parsing, no JSON-in-markdown extraction.

---

## 5. Pattern: Prompt caching for stable context

When prompts include large stable blocks (manuals, brand guides, schema docs), use prompt caching to skip re-tokenization on every call.

```python
client.messages.create(
  model="claude-opus-4-7",
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

**Cost:** cache hits ~10× cheaper, ~2× faster. TTL 5 min (refresh on every hit).

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
| Stacking 8 instructions in one paragraph | Claude follows last instruction strongest | Use numbered list or XML sections |
| Asking for JSON without schema | Free-form output, brittle parsing | Use tool-use with `input_schema` |
| Prompt-injecting user content | Untrusted text bypasses guardrails | Wrap user input in `<user_input>…</user_input>` and instruct Claude to treat it as data |
| Tweaking prompts without an eval | Drift; "improvements" regress on edge cases | Build minimal eval first |
| Hand-rolled CoT + extended thinking | Conflicting reasoning channels | Pick one |

---

## 8. Project hookup

- Brand voice / domain taxonomy / forbidden terms live in the host project's domain skill (e.g., `<brand>` skill, `<product>` skill). Preload that skill when building generators or judges.
- For Karpathy-style optimize loops over prompts/skills, use a project-bound autoresearch skill — frozen harness, append-only `experiments.tsv`, crash discipline.
- For migrations between Claude API model versions or new SDK apps, route through the `claude-api` skill.

Owner: `senior-prompt-engineer` skill.
