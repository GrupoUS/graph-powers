# skills/

Owns the skill folders the plugin ships (14 on 2026-08-26) — one `SKILL.md` each, plus the
`references/`, `scripts/`, `evals/` and `learning.md` a skill carries — and the contract every one
of them meets. Does NOT own the commands (`../commands/`, exposed as `/name` and turned into skills
for Codex), the agents (`../agents/`), or the shared patterns (`../references/shared/`) a skill
points at.

## Entry points

- `<name>/SKILL.md` — the frontmatter is the listing entry Claude Code routes on; the body loads on
  `Skill("graph-powers:<name>")`. Codex reads the same folders from `~/.agents/skills/` (clone
  install) or the native plugin cache; Cursor and Grok read them through plugin manifests that
  point at `./skills/` wholesale. No per-skill registration exists anywhere: the folder is the
  registration.
- `skill-improve/` — the authoring loop (Mode A) and the wiring audit (Mode B) every other skill
  passes through before it enters. Its `scripts/quick_validate.py` and `scripts/run_evals.py` are
  the validators the contracts below name.

## Contracts and invariants

- `name` equals the folder name, unquoted; `description` is one quoted line that says *when*, free
  of `<`, `>`, `[` and `]`. `skill-improve/scripts/quick_validate.py` and CI's frontmatter step
  enforce it; a divergence breaks invocation silently.
- One entry spends at most 1,536 characters of `description` plus `when_to_use`, and every entry
  spends the shared ceiling `.github/check_listing_budget.py` holds (10,752 on 2026-08-26). A long
  description here drops somebody else's skill from the listing on a shared machine.
- Body under 500 non-empty lines; detail in `references/`, loaded on demand and named from the
  body. A reference nothing points at is an orphan.
- Paths inside a skill are relative (`references/x.md`); paths to the rest of the plugin go through
  `${CLAUDE_PLUGIN_ROOT}/…`; paths into the host project go through `${rulesDir}` and the other
  placeholders `../schema/config.schema.json` declares (`.github/check_placeholders.py`).
- Every `Skill()`, `subagent_type`, workflow and `§` a skill cites resolves
  (`.github/check_wiring.py`), and an agent is always written `graph-powers:<agent>`.
- Nothing POSIX-only in a fenced bash block (`.github/check_portability.py`). Scripts are Python
  standard library; there are no shell scripts — the three `intent-layer` inherited were ported,
  and `../NOTICE` records it.
- Every skill has a call site: a command, a row in `../references/shared/060-skill-domain-matrix.md`,
  a playbook step. Cardinal 4 — an orphan does not enter.
- Material adapted from elsewhere is recorded in `../NOTICE`, with what changed and why.

## The usual change

Adding a skill:

1. `Skill("graph-powers:skill-improve")` — Mode A to capture intent, draft and write the evals;
   Mode B before it enters, so the wiring is judged by the read-only auditor.
2. The folder, `SKILL.md` first; `learning.md` from the first round, with measured numbers.
3. The call site: a row in `../references/shared/060-skill-domain-matrix.md`, a tier in
   `../references/shared/120-skill-invocation-order.md`, and the command or playbook step that
   loads it — conditionally, with the condition on the same line as the `Skill()` call, or
   `.github/check_context_budget.py` charges every invocation for it.
4. `../NOTICE` if adapted, `../CHANGELOG.md`, and the version in the five manifests: a shipped change
   that does not bump reaches nobody (`.github/check_version_bump.py`).
5. The gate list in `../AGENTS.md`, every line run.

## Anti-patterns

- A bare `Skill("<name>")` where a personal `~/.claude/skills/<name>` exists: personal beats plugin
  on the bare name, and an `"off"` override returns an error instead of running. The namespace is
  the fix, not a suffix (`../docs/ARCHITECTURE.md § 5`).
- A description that summarises the workflow: the model reads it and skips the body.
- An assertion or an approver regex written from the unquoted fixture while the call site quotes
  the path — `intent_layer\.py\s+state` failed four correct responses, and the approver asked on
  every real invocation while its own test stayed green (`intent-layer/learning.md`, round 1).
- A script edited without its mirror: a byte-identical old copy in `.agents/skills/` or a
  marketplace cache keeps serving the bug (`skill-improve/learning.md`, inherited pattern W2c).

## Pitfalls

- `skill-improve/scripts/run_evals.py` is honest only per case (`--test-case` or
  `--response-dir`); its flat default cancels a positive's `contains` against a negative's
  `not_contains`, and `--threshold 1.0` is required because `critical` is a label in the report,
  not part of the exit code.
- `bun-verify/scripts/turbo_dry_json.py` and `intent-layer/scripts/intent_layer.py` are allowed by
  name in `../hooks/smart_bash_approver.py`. A new script under a skill asks under `guarded` until
  it is added there, with both test cases.
- Eval responses captured by isolated subagents handed the listing measure routing among the
  entries given — not the live listing of a clean session. Say which one a number came from.

## Deferred nodes

`intent_layer.py measure` flags four skill folders here that carry no node, and the deferral is
declared in `.graph-powers/config.json` (`intentLayer.deferred`) with the reason on this line:
`skills/planning/`, `skills/skill-improve/`, `skills/debugger/` and `skills/intent-layer/` are
each one skill whose `SKILL.md` is already the purpose-first entry document of its folder, and
whose `references/` are named from that body. An `AGENTS.md` beside a `SKILL.md` would be the
second copy the root forbids. Revisit when a folder gains a second entry document.

## Related

- `../AGENTS.md` — the cardinals and the gate list
- `../.claude/rules/artifacts.md` — the frontmatter contract, loaded on any edit here
- `../hooks/AGENTS.md` — the guardrails a skill's script has to be allowed by
