# Proactive `skill-improve` lifecycle — Design spec

## Destination

`skill-improve` is proactive at observable skill/harness lifecycle boundaries rather than only when
the user explicitly asks for it: a session receives a small structural reminder, the skill maps each
eligible stage to Mode A, Mode B or an explicit exclusion, a bounded unprimed sample is captured in
fresh Claude Code and Codex sessions, and task close reports the mode plus eval/wiring evidence when
the lifecycle actually fired. Ordinary application work, one-off failures and agent-prompt design
continue to route elsewhere.

The change is complete only when the reminder reaches both Claude Code and Codex session context,
all lifecycle assertions pass in fixtures, the declared live positive/negative sample passes at
threshold `1.0` with trace evidence, the description and listing budgets remain green, and no
verifier or audit mode gains a write path. It does not claim an all-case live hit rate from a bounded
sample.

## Context

The current description says to act proactively before adding an agent or skill and after a model or
plugin upgrade, but the body defines no lifecycle entry protocol and the eval suite contains only
explicit requests. The only concrete caller outside the skill is `/evolve`; this repository's
path-scoped artefact rule is a reminder, not a dispatch.

The external `task-observer` project demonstrates three useful mechanisms: layered activation,
objective task-boundary backstops, and unprimed trials for behaviour that should happen organically.
It also carries a continuous observation store, scheduler and staging workflow. Those larger
subsystems are not transferred: Graph Powers already owns durable session learning through
`/evolve`, planning state through SDD, routing through the shared domain matrix, and fan-out through
the execution floor.

This is an **L5** change: it crosses skill routing, SessionStart hook output, behaviour evals and
distribution attribution. Explicit `/gauntlet` therefore becomes eligible after the structured plan
is approved.

## Reuse ledger

| # | Need | Existing asset | Verdict | Justification |
|---|---|---|---|---|
| N1 | Put the lifecycle reminder in every supported session without loading the full skill | `hooks/session_context.py:59-82,165-166`; `hooks/test_hooks.py:2280-2311` | EXTEND | The hook already injects one concise always-on execution-floor pointer into Claude Code and Codex. A second hook or registry would duplicate that path. |
| N2 | Select the owner at lifecycle stages | `skills/skill-improve/SKILL.md:3,23-56,144-148`; `references/shared/060-skill-domain-matrix.md:20-29` | EXTEND | The skill is the canonical two-mode router and the matrix owns domain precedence; the missing piece is a stage-to-owner contract plus exclusions. |
| N3 | Turn changed behaviour into RED and per-case evidence | `skills/skill-improve/references/authoring.md:181-262`; `skills/skill-improve/scripts/run_evals.py:309-376`; `skills/skill-improve/evals/evals.json:1-359` | EXTEND | The authoring loop and assertion consumer exist. Add lifecycle RED, tagged case selection and unprimed-trial rules; do not create a second grader. |
| N4 | Produce reproducible clean-session responses and traces | `(none found: searched capture, claude -p, codex exec under skills/ and scripts/)`; nearest consumer `skills/skill-improve/scripts/run_evals.py:309-376`; installer `codex/install.mjs:1-24,800-850` | NEW | Extending the grader would couple provider process/auth/JSONL failures to assertion semantics. Add one standard-library producer that invokes the existing project-scope Codex installer rather than copying installation logic. |
| N5 | Preserve and close follow-up measurements | `skills/skill-improve/learning.md:1-16,120-122,240-241,539-541,611-634` | EXTEND | Keep the append-only round history. Add stable IDs and dispositions instead of creating an observation database. |
| N6 | Capture general session learning | `commands/evolve.md:69-95`; `references/shared/100-autoresearch-loop.md:1-56` | REUSE | General observation remains `/evolve` territory; `skill-improve` receives only reusable skill/harness signals. |
| N7 | Bound research, fan-out and independent judgment | `references/execution-floor.md:1-80`; `references/shared/070-parallel-agent-spawn.md:1-39`; `agents/skill-improver.md:1-18,91-97` | REUSE | Existing caps and the report-only judge remain authoritative. |
| N8 | Credit and license the adapted methodology | `NOTICE:9-57`; `.claude-plugin/plugin.json:8`; `package.json:26`; `skills/skill-improve/LICENSE.txt:1-202` | EXTEND | The source is CC BY 4.0; provenance and its full licence travel beside the already Apache-derived skill. The two hand-owned package expressions change once and client manifests are regenerated. |

## Regression watchlist

| # | Existing behaviour that must still work | How to prove it | Owner phase |
|---|---|---|---|
| W1 | One weak description remains Mode A; a new skill runs Mode A authoring before Mode B integration | Good/bad fixture responses for every `proactivity-contract` case in `test_run_evals.py` | Behaviour phase |
| W2 | Agent prompt design routes to `senior-prompt-engineer`; only its later registration/wiring invokes Mode B | Boundary fixture plus the live `claude:bound-agent-prompt-draft` trial | Behaviour phase |
| W3 | Ordinary application source, one isolated product failure and unrelated upgrades do not invoke `skill-improve` | Three boundary fixtures; no `skill-improve` load in their trace expectation | Behaviour phase |
| W4 | Mode B remains report-only and the paired judge remains unable to Write/Edit | Wiring, Codex native-policy and Codex semantic-policy gates | Integration phase |
| W5 | Session context still reports project, branch, usable gates and the execution-floor pointer | Hook suite for Claude Code and Codex, including unchanged first line | Hook phase |
| W6 | Existing bounded-fanout work remains intact | Exact hashes of the already-dirty skill blocks plus changelog prefix, source versions and generated Codex manifest shape | Every phase |
| W7 | Skill listing stays below both per-entry and shared ceilings | `quick_validate.py` and `check_listing_budget.py` | Behaviour and final phases |
| W8 | The new always-on posture is exactly one bounded line and does not duplicate the lifecycle matrix | Hook assertion: one occurrence, no newline, rendered UTF-8 length at most 512 bytes; context-budget gate separately stays green | Hook and final phases |

### Executable acceptance probes

The Phase B plan must carry these commands verbatim and record exit codes plus the named output.

1. Skill and runner contracts:

   ```text
   python3 skills/skill-improve/scripts/quick_validate.py skills/skill-improve
   python3 skills/skill-improve/scripts/test_run_evals.py
   python3 skills/skill-improve/scripts/test_capture_trigger_evals.py
   ```

   **EXPECT:** `Skill is valid`; all runner and capture-producer tests exit `0`. The producer tests
   use fake Claude/Codex JSONL streams and prove fresh directories, exact unmodified prompts,
   positive load, negative abstention, malformed stream/auth failure, and missing executable.

2. Mandatory unprimed live sample, run once before the lifecycle edit and once after it:

   ```text
   python3 skills/skill-improve/scripts/capture_trigger_evals.py --phase baseline --timeout-seconds 300 --plugin-root . --evals-path skills/skill-improve/evals/evals.json --response-dir .claude/audit/skill-improve-proactivity/red --trial codex:pro-precreate-skill --trial claude:bound-agent-prompt-draft
   python3 skills/skill-improve/scripts/run_evals.py --skill-path skills/skill-improve --evals-path skills/skill-improve/evals/evals.json --response-dir .claude/audit/skill-improve-proactivity/red --case-tag proactive-live --threshold 1.0
   python3 skills/skill-improve/scripts/capture_trigger_evals.py --phase candidate --timeout-seconds 300 --plugin-root . --evals-path skills/skill-improve/evals/evals.json --response-dir .claude/audit/skill-improve-proactivity/green --baseline-dir .claude/audit/skill-improve-proactivity/red --trial codex:pro-precreate-skill --trial claude:bound-agent-prompt-draft
   python3 skills/skill-improve/scripts/run_evals.py --skill-path skills/skill-improve --evals-path skills/skill-improve/evals/evals.json --response-dir .claude/audit/skill-improve-proactivity/green --case-tag proactive-live --threshold 1.0
   ```

   **EXPECT:** capture never appends probe language and emits one trace plus one response per trial.
   BASELINE exits `0` only when both provider runs were captured and parsed; it reports polarity
   mismatches without converting them to infrastructure failure, and its assertion gate may be the
   expected RED exit `1`. GREEN prints `PASS codex:pro-precreate-skill expected=load observed=load` and
   `PASS claude:bound-agent-prompt-draft expected=skip observed=skip` and
   `PASS candidate-digest changed`; the tagged assertion gate exits `0`. RED is evidence, not
   required to fail organically; at least the new hook assertion is
   RED before production edits. Missing CLI, auth failure, malformed/incomplete JSONL, missing trace
   or an activation mismatch is `BLOCKED`/exit `1` in GREEN, never `NOT MEASURED` or `SKIP`.

3. Hook, routing and budgets:

   ```text
   python3 hooks/test_hooks.py
   python3 .github/check_wiring.py
   python3 .github/check_codex_native.py
   bun .github/check_codex_policy.mjs
   python3 .github/check_listing_budget.py
   python3 .github/check_context_budget.py
   ```

   **EXPECT:** all exit `0`; both harnesses receive one lifecycle line; the line is at most 512
   UTF-8 bytes after path resolution; wiring has zero unresolved references; both budgets are below
   their declared ceilings.

4. Preservation of the already-dirty skill work:

   ```text
   python3 -X utf8 -c "from pathlib import Path; import hashlib; a=Path('skills/skill-improve/references/authoring.md').read_text(encoding='utf-8'); ab=a[a.index('### 5b. Run with-skill against baseline'):a.index('### 5c. Draft assertions while the runs complete')]; l=Path('skills/skill-improve/learning.md').read_text(encoding='utf-8'); rb=l[l.index('## Round 9 —'):].split('\n## Round 10 —',1)[0].rstrip()+'\n'; h=Path('skills/skill-improve/references/harness-wiring-audit.md').read_bytes(); got=(hashlib.sha256(ab.encode()).hexdigest(),hashlib.sha256(rb.encode()).hexdigest(),hashlib.sha256(h).hexdigest()); want=('6e739fb722751c7acd8f80f4fbc1bbcf6235cb2f4263c4763730f95c73496c07','620d42425e629fe3216295c38aa1e717bd13f09ac2bdd1eaf71b12214b8d94d0','ca476b801aea7a1e6ba145a75199af5bc3647510a3913e96e740fe7bf0cfcb72'); assert got==want,(got,want); print('pre-existing skill-improve work preserved')"
   ```

   **EXPECT:** the exact message above and exit `0`. New Mode A guidance must be inserted outside
   the hashed `5b` block; Round 10 is append-only; Mode B is not owned by this change.

5. Preservation of the already-dirty distribution work:

   ```text
   python3 -X utf8 -c "from pathlib import Path; import hashlib; H=lambda b:hashlib.sha256(b).hexdigest(); V=lambda t:next(x for x in t.splitlines(keepends=True) if '\"version\"' in x).encode(); c=Path('CHANGELOG.md').read_text(encoding='utf-8'); end='verification to the balanced Terra tier; both Codex generators consume the same semantic policy.'; cb=(c[c.index('## 1.17.0'):c.index(end)+len(end)].rstrip()+'\n').encode(); ps=['package.json','.claude-plugin/plugin.json','.codex-plugin/plugin.json','.cursor-plugin/plugin.json','.grok-plugin/plugin.json']; raw={p:Path(p).read_text(encoding='utf-8') for p in ps}; cl=raw['.codex-plugin/plugin.json'].splitlines(keepends=True); s=next(i for i,x in enumerate(cl) if '\"skills\"' in x); e=next(i for i in range(s+1,len(cl)) if cl[i].strip() in {']','],'}); cp=V(raw['.codex-plugin/plugin.json'])+(''.join(cl[s:e+1])+'commands_present='+str('\"commands\"' in raw['.codex-plugin/plugin.json'])+'\n').encode(); y=next(x for x in Path('plugin.yaml').read_text(encoding='utf-8').splitlines(keepends=True) if x.startswith('version:')); got=(H(cb),H(V(raw['package.json'])),H(V(raw['.claude-plugin/plugin.json'])),H(cp),H(V(raw['.cursor-plugin/plugin.json'])),H(V(raw['.grok-plugin/plugin.json'])),H(y.encode())); want=('c8075ea28f5c9a6e335bc8a976ed5096420af7fc549fce27f9f4c7d99e42d29b','944d9f558ff298640a3e895a02cce431f6ebc8f3fd0e78ec983bad07a5fbcd7f','944d9f558ff298640a3e895a02cce431f6ebc8f3fd0e78ec983bad07a5fbcd7f','fdaabf49e7bdc8373b59fff57128040917fc98d9d349064cc36ef8c9de55476b','944d9f558ff298640a3e895a02cce431f6ebc8f3fd0e78ec983bad07a5fbcd7f','944d9f558ff298640a3e895a02cce431f6ebc8f3fd0e78ec983bad07a5fbcd7f','f65bad2f72a503c9b4714371f2a34731da8b9a989463e4c5e537bd79fbbd1963'); assert got==want,(got,want); print('pre-existing distribution work preserved')"
   ```

   **EXPECT:** the exact message above and exit `0`, after all four generators run. Append the new
   `1.17.0` changelog paragraph after the hashed prefix; preserve every existing raw version line
   and the Codex manifest's raw generated skill-array/no-commands hunk while changing only licence
   fields.

## Background research

At external HEAD
[`510caad`](https://github.com/rebelytics/one-skill-to-rule-them-all/tree/510caad26c907793e48306262af216ff9f71c9f7),
`task-observer` uses a description, persistent instruction and session hook as complementary
activation layers; it explicitly says description matching alone is not enforceable. It adds a
post-task summary so a loaded-but-inert observer becomes visible, keeps trial triggers outside the
prompt being measured, and records negative observations rather than treating silence as success.

The transferable mechanisms are adapted, not copied. POSIX snippets, Claude/Cowork-specific paths,
the continuous per-observation filesystem, autonomous application, scheduler and unbounded
threshold heuristics conflict with this repository's portability, one-source, no-verifier-writes
and bounded-fanout contracts and are excluded.

Local evidence agrees with the external diagnosis:

- `skills/skill-improve/SKILL.md` carries proactive wording but no lifecycle entry body.
- `skills/skill-improve/evals/evals.json` has twelve cases, all positive cases phrased as explicit
  skill/harness requests and only two negatives.
- `skills/skill-improve/learning.md` repeatedly records that clean-session trigger measurement is
  still open.
- `.claude/rules/artifacts.md` is the repository-local automatic reminder; installed projects do
  not inherit that project rule.
- `hooks/session_context.py` is already the cross-harness route for a concise always-on pointer.

Baseline on the pre-change worktree: `quick_validate.py` PASS; six eval-runner tests PASS; listing
`10,109 / 10,752` characters; wiring `459` references and `12` agents with zero unresolved; command
context floor `269,953 / 270,000` bytes. The hook posture is therefore a pointer and compact
conditional, never a copy of the lifecycle matrix.

## Approach (chosen)

Use a **bounded layered lifecycle**:

1. SessionStart injects one concise conditional pointer to the canonical lifecycle section in
   `skill-improve`; it guides and never claims to spawn.
2. `SKILL.md` owns one stage matrix. New-skill work is intentionally sequential: Mode A authors and
   measures the artefact first; Mode B audits registration and call sites only after a candidate
   exists. New-agent prompt design remains `senior-prompt-engineer`; Mode B starts only at harness
   integration. Task close never selects a mode — it only exposes whether a required stage ran.
3. Mode A starts lifecycle-triggered behaviour changes with RED. Organic-trigger trials preserve the
   user prompt byte-for-byte, run in a fresh temporary project, and record negative evidence rather
   than interpreting silence as success.
4. Round follow-ups use an append-only stable-ID/disposition contract. The next round whose concrete
   path or lifecycle-event slug matches an open follow-up must disposition it before claiming PASS.
5. Evals add lifecycle positives and nearest-boundary negatives. Critical assertions check the
   selected owner and observable action, not merely the string `skill-improve`; exactly two cases are
   the bounded live sample in this round and the rest are contract fixtures.
6. The `task-observer` influence is recorded in `NOTICE`; no upstream command or prose block is
   redistributed verbatim.

### Lifecycle stage contract

The matrix below is the single routing authority added to `SKILL.md`. Earlier or later wording may
explain it but may not restate a competing version.

| Stage observed before task close | Owner and timing | Minimum evidence | Explicit exclusion |
|---|---|---|---|
| Create a skill, or materially change one skill's body, description, reference or eval behaviour | **Mode A before the first draft/edit.** For a new skill, Mode A completes before any Mode B integration pass. | Intent plus RED for changed behaviour; focused case at `1.0`; `quick_validate.py` | Typo/prose-only repair with no rule, trigger or behaviour change |
| Register a newly authored skill or connect its command/agent/call sites | **Mode B after the Mode A candidate exists and before integration is accepted.** | Changed-edge baseline; caller → resolver → target evidence; report-only verdict | It does not rewrite the skill body that Mode A owns |
| Design or revise one agent prompt/body | **`senior-prompt-engineer` before drafting.** `skill-improve` does not fire. | Prompt-engineering acceptance evidence | Naming the artefact “agent” does not make prompt design Mode B |
| Register, remove or rename an agent, or change its harness call sites/model registration | **Mode B after a prompt candidate exists and before integration is accepted.** | Registration, call-site and generated-client edges; report-only verdict | No agent prompt/body edits |
| Plugin/model upgrade with observed or declared impact on discovery, tool contract, hook payload or model routing | **Mode B before accepting the upgraded wiring.** | Exact changed surface plus native/generated parity | Database, framework, application or package upgrade with no harness impact |
| Two materially similar misses of the same skill rule in current evidence | **Mode A regression before another prose tweak.** | Two named misses, one reproducing RED, then focused GREEN | One isolated application/product failure routes to its domain owner |
| Competing descriptions, shadowing, orphan/dangling edge, or a second claimant discovered during Mode A | **Escalate A → B once the second edge is evidenced.** | The competing claimant/edge; no speculative escalation | A weak description with no second claimant stays Mode A |
| Task boundary | **No new mode.** Report `<mode>: <deciding evidence>` only if a row above fired; otherwise say nothing about this lifecycle. | Trace/eval/wiring command that actually ran | Never invoke a skill merely to manufacture a close-out line |

### Follow-up identity and state contract

`learning.md` remains append-only. A follow-up is created once in the round that discovers it:

```markdown
**Follow-up `R10-F1` — OPEN:** <one measurable question>
**Applies when:** path `<concrete/path>` or event `<lifecycle-event-slug>`
**Close with:** `<command or trace>` producing `<observable result>`
```

- ID is `R<origin-round>-F<ordinal>`, unique across the file; ordinals start at `1` in each round and
  are never reused.
- Later rounds do not edit the origin. They append `**Disposition `R10-F1` — CLOSED:** <dated
  evidence>`, `**Disposition `R10-F1` — DEFERRED:** <external condition>; reopen when <objective
  condition>`, or `**Disposition `R10-F1` — OPEN:** reactivated because <the condition now true>`.
- Allowed transitions are `OPEN → CLOSED`, `OPEN → DEFERRED`, and `DEFERRED → OPEN` when the named
  condition becomes true. `CLOSED` never reopens; a materially new question gets a new ID.
- Applicability is mechanical: the current changed path equals or descends from the literal
  `Applies when` path, or the current lifecycle row has the identical event slug. Only structured
  `Follow-up`/`Disposition` records participate; legacy “Next round should measure” prose is not an
  implicit backlog.
- Allowed event slugs are `skill-authoring`, `skill-wiring`, `agent-wiring`, `harness-upgrade`,
  `repeated-skill-miss`, `trigger-collision` and `proactive-routing`; inventing a synonym does not
  create a match.
- Round 10 creates `R10-F1` for the repeated clean-session debt and closes it only after the mandatory
  GREEN trace succeeds. If only the bounded sample is measured, its text names that sample and does
  not claim a suite-wide hit rate.

### Clean-session capture contract

`capture_trigger_evals.py` is a producer, not another grader. It reads only cases tagged
`proactive-live`, preserves the case prompt exactly, and writes ignored evidence under
`.claude/audit/`; `run_evals.py` remains the assertion authority via its new `--case-tag` selector.

- Each `--trial <backend>:<case-id>` gets a new `tempfile.TemporaryDirectory`; no prior transcript,
  project rule, working-tree `AGENTS.md` or response is reused.
- Claude Code runs non-persistently with the candidate plugin supplied by `--plugin-dir`, project-only
  setting sources, plan permission mode, Write/Edit disallowed and verbose stream JSON.
- Codex first invokes the existing `codex/install.mjs --scope project` into the temporary project,
  then runs `codex --ask-for-approval never exec --json --ephemeral --ignore-user-config
  --ignore-rules --sandbox read-only --dangerously-bypass-hook-trust --skip-git-repo-check`. The
  approval flag is deliberately before `exec` — Codex 0.152.0 rejects it afterward. The bypass
  applies only to the vetted candidate hook inside the disposable project; it does not bypass the
  read-only filesystem sandbox.
- A Claude positive requires a `Skill` tool-use whose input resolves
  `graph-powers:skill-improve`; a Codex positive requires a tool event that reads the generated
  `.agents/skills/skill-improve/SKILL.md`. Both must occur before task work. A negative requires that
  evidence to be absent. The response text is then graded separately.
- The producer rejects a live prompt containing `skill-improve`, `Mode A`, `Mode B`, an instruction to
  load `SKILL.md`, or eval/probe wording. It recursively parses JSONL rather than matching raw output.
- CLI absence, authentication failure, timeout, non-zero child exit, malformed/incomplete JSONL or
  missing response exits `1` in both phases. Wrong load/skip polarity is recorded but non-blocking in
  `baseline`; it exits `1` in `candidate`. There is no success-with-skip path.
- Before either backend runs, the producer computes `candidate_digest`: SHA-256 over every regular,
  non-symlink file under the sorted repo-relative roots `.claude-plugin/`, `agents/`, `codex/`,
  `commands/`, `hooks/`, `references/`, `schema/`, `skills/`, `templates/` and `workflows/`. For each
  file the digest input is POSIX relative path, NUL, decimal byte length, NUL, then exact bytes. An
  unreadable file or symlink fails capture. This surface contains every source used to assemble the
  disposable Claude/Codex candidates while excluding audit output, plans and `.git` churn.
- Every trace records that aggregate digest and file count, backend and CLI version, reported model
  when present, UTC time, candidate git revision/dirty flag, case ID, prompt digest, child exit and
  parsed load/skip event. Candidate phase additionally requires `--baseline-dir`, verifies every RED
  trace agrees on one baseline digest and every GREEN trace agrees on a different candidate digest,
  and verifies prompt digests match by backend/case. Thus dirty RED and GREEN worktrees remain
  distinguishable and reproducible. No token, credential, environment dump or unrelated response is
  recorded.
- Fake-stream unit tests inject executable paths and never contact a provider. The real command is a
  completion gate. RED and GREEN together consume four clean sessions; the Phase B plan counts them
  against the configured workflow cap and still reserves its independent evaluator.

### Rejected alternatives

- **Description only:** cheapest, but it is the current design and has no operational body or
  lifecycle evidence.
- **Full task-observer transplant:** duplicates `/evolve`, adds another backlog and scheduler,
  imports non-portable commands, and broadens `skill-improve` from its two measured modes into a
  general session observer.
- **A new lifecycle hook with its own state:** duplicates `session_context.py` and creates a second
  state machine solely to remember whether a reminder was emitted.

## Architecture

| Layer | Owner | Change |
|---|---|---|
| Session activation | `hooks/session_context.py` | Resolve the canonical skill path and append a concise conditional lifecycle pointer after the execution-floor line; if the resolved path makes the line exceed 512 bytes, fall back to the relative canonical path; always fail open. |
| Hook contract | `hooks/test_hooks.py` | Prove the pointer reaches Claude Code and Codex exactly once, has no embedded newline, stays at most 512 UTF-8 bytes, names the canonical file, and leaves the first-line gate tag unchanged. |
| Lifecycle router | `skills/skill-improve/SKILL.md` | Tighten the description and add the only stage → owner → timing → minimum evidence → exclusion matrix, including sequential Mode A then Mode B for a new skill. |
| Authoring behaviour | `skills/skill-improve/references/authoring.md` | Add lifecycle RED, repeated-failure threshold, exact unprimed-trial rules and follow-up disposition rules outside the existing hashed `5b` block. |
| Behaviour oracle | `skills/skill-improve/evals/evals.json` | Add positives for pre-create, pre-wire, relevant upgrade, repeated miss and applicable open follow-up; add negatives for agent-prompt design, unrelated upgrade, one-off app failure, closed learning and product “agent” work. Tag the bounded live pair separately. |
| Assertion selector | `skills/skill-improve/scripts/run_evals.py`, `test_run_evals.py` | Add `--case-tag` only with `--response-dir`; zero matching cases or missing tagged responses fails. Existing all-case and `--test-case` semantics remain unchanged. |
| Trace producer | `skills/skill-improve/scripts/capture_trigger_evals.py`, `test_capture_trigger_evals.py` | Implement the two backend adapters and exact failure contract above; invoke the existing Codex project installer; write only ignored response/trace artefacts. |
| Round record | `skills/skill-improve/learning.md` | Extend the template with structured IDs/dispositions, then append Round 10 and `R10-F1`; never rewrite prior rounds or current Round 9. |
| Local dogfood | `.claude/rules/artifacts.md` | Point its existing reminder at the canonical lifecycle section and require task-close evidence when a lifecycle event fired. |
| Distribution source | `NOTICE`, `CHANGELOG.md`, `.claude-plugin/plugin.json`, `package.json`, `skills/skill-improve/LICENSE-CC-BY-4.0.txt` | Record source, author, licence, source commit and what changed; retain the Apache licence; add `CC-BY-4.0` to both hand-owned SPDX expressions. `[ASSUMED]` Join the already-unreleased `1.17.0` worktree rather than create a second bump. |
| Generated distribution | `.codex-plugin/plugin.json`, `.cursor-plugin/plugin.json`, `.grok-plugin/plugin.json`, `plugin.yaml` | Never hand-edit. Regenerate from `.claude-plugin/plugin.json` with `bun codex/native-plugin.mjs --emit-only`, `bun cursor/install.mjs --emit-only`, `bun grok/install.mjs --emit-only`, and `bun hermes/install.mjs --emit-only`; generators copy `license` at `codex/native-plugin.mjs:43-52`, `cursor/install.mjs:128-137`, `grok/install.mjs:49-58`, and `hermes/install.mjs:48-58`. |

No generated Codex companion changes are needed unless an agent source changes; this design does not
change `agents/skill-improver.md`.

## Data flow

```text
SessionStart
  → short lifecycle pointer reaches the parent session
  → eligible event occurs
    → load skill-improve + learning.md
    → classify authoring as Mode A, wiring as later Mode B, or route an explicit exclusion
    → establish RED or bounded changed-edge baseline
    → author/audit through the existing mode
    → run focused evals/wiring plus required repository gates
    → append a disposition for every mechanically applicable open follow-up
  → task close reports mode + deciding evidence only when an earlier lifecycle row fired
```

General task observations that do not target a reusable skill/harness behaviour stay in `/evolve`.
Mode B remains report-only; the user or a later approved implementation owns patches.

## Error handling

- If the SessionStart hook cannot resolve the plugin file, emit the relative canonical path and exit
  successfully; the hook never blocks session startup.
- If one task creates a skill and wires it, run Mode A first and Mode B second. They are sequential
  stages, not competing interpretations. If a weak existing skill later reveals a second claimant,
  escalate only after that edge is evidenced.
- If a task creates an agent, `senior-prompt-engineer` owns the prompt candidate; Mode B can audit
  registration afterward but never edits the prompt body.
- A single application failure is not recurrence. Route to the domain owner; require two materially
  similar misses before creating a skill regression case.
- An upgrade with no observed effect on skill selection, tool contract, model routing or hook shape
  does not trigger Mode B.
- If an organic trial is primed with the skill, mode, load instruction or eval wording, the producer
  exits `1`; it does not count the run positive or negative.
- If either declared clean-session capture cannot run or yields no parseable load/skip evidence,
  completion is `BLOCKED`. Synthetic fixtures prove adapters and assertions, never live routing.
- If an `OPEN` follow-up is applicable, missing disposition is a failing completion gate. A valid
  `DEFERRED` disposition names an external condition and an objective reactivation condition.
- Any report-only agent write, listing-budget overage, unresolved edge or failed critical assertion
  is a failing gate, never a caveat attached to PASS.

## Testing

### RED first

Add and unit-test the producer and tagged selector first, then capture the bounded live pair against
the unchanged lifecycle body/hook. Record both results even if description matching already passes
one organically. The deterministic RED is the new hook assertion, which must fail before production
edits. A live prompt may state the user's task but must not name `skill-improve`, a mode, a load
instruction or expected eval outcome.

### Focused checks

- `python3 skills/skill-improve/scripts/quick_validate.py skills/skill-improve`
- `python3 skills/skill-improve/scripts/test_run_evals.py`
- `python3 skills/skill-improve/scripts/test_capture_trigger_evals.py`
- Per-case `run_evals.py --test-case ... --threshold 1.0` while iterating.
- One tagged `--response-dir ... --case-tag proactive-live --threshold 1.0` gate over the mandatory
  fresh-session pair; zero selected cases and missing responses fail.
- New hook assertions in `python3 hooks/test_hooks.py` for Claude Code and Codex.
- `python3 .github/check_listing_budget.py`
- `python3 .github/check_wiring.py`
- `python3 .github/check_portability.py`
- `python3 .github/check_context_budget.py`
- `python3 .github/check_machine_paths.py`
- `python3 .github/check_placeholders.py`

### Gauntlet close

The approved plan will assign disjoint hook and skill paths, keep the response producer and
production activation in ordered tasks so RED is captured first, count all four live RED/GREEN
sessions against the configured workflow cap, reserve one Evaluator per wave, preserve focused
evidence in the plan, then run the repository's complete gate list through `/verify loop
<PLAN_FILE>`. A deliberately wrong response must exit `1`; a correct response graded against a
nearest negative must also exit `1`.

## Assumptions

- `[ASSUMED]` The user wants proactive skill/harness lifecycle behavior, not an always-on observer of
  every application task.
- `[ASSUMED]` The existing uncommitted `1.17.0` version and changelog entry are one unreleased
  working tree; this change may extend that release without a second bump.
- `[ASSUMED]` A concise SessionStart pointer is acceptable global context cost because it is
  conditional, does not load the skill body, is hard-capped at 512 rendered UTF-8 bytes, and closes
  a measured missing activation edge.
- `[ASSUMED]` The bounded live sample intentionally proves one positive on Codex and the nearest
  negative on Claude Code, while deterministic hook tests prove the structural line reaches both.
  It does not claim full polarity parity across clients.

## Out of scope

- A general per-session observation log, scheduler, review queue or automatic skill installer.
- Automatic patch application by `skill-improver` or any other verifier.
- Editing global user configuration or the global `SubagentStart` matcher.
- Agent prompt design, ordinary product/application failures, memory preferences or project-specific
  content.
- Replacing `/evolve`, the domain matrix, SDD state, the execution floor or the existing eval grader.
- Copying POSIX snippets or Claude/Cowork-specific path conventions from the external project.
- Claiming a statistically meaningful trigger rate from two live cases, or launching an unbounded
  cross-product of cases and clients.

## Not yet specified

No design choice is deferred to Phase B. It must assign exact task ownership and preserve the order
producer/RED → production lifecycle → GREEN. The licence decision is closed here: keep the existing
Apache text, ship CC BY 4.0 beside it, attribute the pinned source, update the two hand-owned package
expressions, then regenerate four client manifests from the Claude manifest. Any unavailable live
backend blocks completion under the capture contract above.

## Rollback

- Remove the SessionStart lifecycle pointer and its focused tests; the existing project/branch/gates
  and execution-floor context remain unchanged.
- Revert the lifecycle matrix, authoring additions, capture producer, tag selector and new eval cases
  together; the original two-mode router, runner semantics and twelve-case suite remain valid.
- Remove only appended Round 10, provenance/changelog hunks and the CC BY licence file; restore the
  two source licence expressions and regenerate clients. Do not rewrite existing Round 9,
  bounded-fanout edits, version bump or unrelated dirty files.
- No database, external service, scheduler, installed skill or global configuration changes exist to
  migrate or undo.

## References

- [`task-observer` source at the researched commit](https://github.com/rebelytics/one-skill-to-rule-them-all/tree/510caad26c907793e48306262af216ff9f71c9f7)
- [Layered activation and task-boundary backstop](https://github.com/rebelytics/one-skill-to-rule-them-all/blob/510caad26c907793e48306262af216ff9f71c9f7/references/environments.md#L6-L124)
- [Unprimed organic-trial design](https://github.com/rebelytics/one-skill-to-rule-them-all/blob/510caad26c907793e48306262af216ff9f71c9f7/references/skill-authoring.md#L553-L568)
- [CC BY 4.0 attribution terms](https://github.com/rebelytics/one-skill-to-rule-them-all/blob/510caad26c907793e48306262af216ff9f71c9f7/LICENSE.txt#L119-L145)
- Existing Graph Powers authorities: `skills/skill-improve/SKILL.md`,
  `references/execution-floor.md`, `references/shared/060-skill-domain-matrix.md`,
  `commands/evolve.md`.
