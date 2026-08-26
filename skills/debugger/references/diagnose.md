# Steps 1–3 — Diagnose: Build the loop → Reproduce & minimise → Hypothesise

> Front half of the **diagnose-first** chain (mattpocock `diagnosing-bugs` §1–§3), adapted for a full-stack repository with a split deploy target. This is the gate before any code-reading or fixing. Back half (instrument → fix → verify/cleanup, Steps 4–6) lives in `references/methodology.md`.

---

## Why the loop comes first

**If you can't run it on demand, you can't fix it.** A bug that only happens "sometimes in prod" is
a bug whose feedback loop nobody has built yet — build it *before* opening source files. Get the
loop right and the bug is 90% fixed; the rest is mechanical. The gates this enforces are in
`Skill("debugger") § Iron Law`.

---

## Step 1 — Build the Feedback Loop (P1)

Construct a deterministic, agent-runnable pass/fail signal. Pick the highest-rank option that fits the bug.

| Rank | Loop | the project example | Use when |
|------|------|------------------|----------|
| **1** | Failing **vitest** test | `${tooling.commands.test} -t "<bug-name>"`, run from the workspace that owns the seam | Pure code logic; any API procedure or UI component bug |
| **2** | **HTTP fixture** (curl) | `curl -sS -X POST ${project.stagingUrl}/api/<endpoint> -H "authorization: Bearer $TOKEN" -H "content-type: application/json" -d '<json>' \| jq` | tRPC 500 / UNAUTHORIZED / payload edge case |
| **3** | **CLI fixture** (Python stdlib, per cardinal rule #3) | `python scripts/<repro>.py --param ...` | Multi-step external API repro (payment provider, messaging platform, ad platform) |
| **4** | **Browser smoke** | `bunx agent-browser open ${project.stagingUrl}/<route> && bunx agent-browser snapshot -i -c && bunx agent-browser console` | UI regressions, hydration mismatch, auth redirect; auth pages use `--cdp` attach — `Skill("webapp-testing")` |
| **5** | **Replay harness** | Recorded webhook JSON re-posted to the local API → expected DB delta | Webhook idempotency / signature / partial-failure bugs |
| **6** | **Fuzz / differential** | Two-driver diff (HTTP vs WebSocket database driver), property test via `fast-check` | Driver-edge bugs, transaction semantics, race conditions |
| **7** | **Log parse** | `python scripts/fetch_logs.py --filter "<error>"` against the project's CI and host log sources | Bug visible only via observability, no live trigger available |
| **8** | **Metrics scrape** | Metrics dashboard, Postgres `pg_stat_statements`, request-count alerts | Slow burn perf / leak / cache miss bugs |
| **9** | **Manual repro** | "click here, then click there" | **Last resort.** Does not satisfy Step 1 exit until promoted to rank 1–4. |

The loop must be: **fast** (< 30s ideal, < 5min hard cap), **sharp** (binary pass/fail, no eyeballing), **repeatable** (3 runs = 3 identical results, or variance source captured), **agent-runnable** (no human in the loop). *If you catch yourself reading code to build a theory before this command exists — stop. Jumping straight to a hypothesis is the exact failure this skill prevents.*

### project-specific reproducer recipes

**Driver-capability repro (only when the connection module imports an HTTP-only driver):**
```ts
// Read the connection module's import FIRST. Serverless Postgres vendors ship an
// HTTP driver that cannot open a transaction and a pool/WebSocket driver that can.
// This repro is meaningful only once you have confirmed the project is on the
// HTTP one — otherwise the bug is elsewhere, and "de-atomize the callers" is the
// wrong fix in either case.
import { db } from "<connection module>";
it("repro: db.transaction() rejects on the HTTP driver", async () => {
  await expect(
    db.transaction(async (tx) => tx.select().from(users))
  ).rejects.toThrow(/No transactions support/);
});
// Fix path: restore the transaction-capable driver — NOT rewrite the call sites.
```

**Authenticated staging probe:**
```bash
# Pre-req: an authenticated browser session. Attach to one the person already opened;
# never automate the sign-in. See Skill("webapp-testing") for the attach pattern.
bunx agent-browser snapshot -i -c -o ".graph-powers/logs/<bug>-snapshot.json"
bunx agent-browser console > ".graph-powers/logs/<bug>-console.log"
bunx agent-browser errors  > ".graph-powers/logs/<bug>-errors.log"
bunx agent-browser network requests --filter "api-staging" > ".graph-powers/logs/<bug>-net.log"
```

**tRPC 500 repro:**
```bash
# Read the token with the Read tool and paste it in place of <token>. Never commit it; vault-only.
# Not `curl … | jq`: in PowerShell `curl` is an alias of `Invoke-WebRequest`, which rejects `-s`,
# and `jq` is not there at all — so on Windows this printed a parameter error, not a response body.
python -X utf8 -c "import json,urllib.request as u;r=u.Request('${project.stagingUrl}/api/<endpoint>',data=json.dumps({'0':{'json':{}}}).encode(),headers={'authorization':'Bearer <token>','content-type':'application/json'});print(json.dumps(json.load(u.urlopen(r)),indent=2))"
```

**SSE leak / listener count probe:** hold the stream open and read it line by line, then disconnect
and check the server's `listener.attach` / `listener.detach` pairs for that wid. Same reason as
above — a backgrounded `curl -N` is two POSIX-only constructs, the alias and the trailing `&`:
```bash
python -X utf8 -c "import urllib.request as u;r=u.Request('${project.stagingUrl}/api/<stream-endpoint>',headers={'authorization':'Bearer <token>'});[print(l.decode('utf-8','replace').rstrip()) for l in u.urlopen(r)]"
```

**Third-party integration repro:** when the project ships a skill for the integration, load it; otherwise reproduce against the provider's sandbox before touching code.

---

## Step 2 — Reproduce & Minimise (P2)

### Self-interrogation (write the answers)
```
1. What SHOULD happen? (expected behavior, exact values)
2. What ACTUALLY happens? (observed behavior, exact values)
3. WHERE do they diverge? (specific point)
```
Read the stack trace to the end first — line numbers, paths and error codes often carry the answer.

### Reproduce consistently — run the loop 3×
Acceptance:
- All 3 runs fail in the **identical** way (same error message, exit code, stack frame), **OR**
- The runs vary and you have captured the **variance source** as a parameter of the loop (timing window, ordering, env var, request ID, tenant ID, day-of-week).

If you cannot reach either state: **stop. Gather more data. Do not guess.** Common failure modes:
- "Only fails in prod" → add structured logging at component boundaries, replay the failing request locally with the captured payload.
- "Flaky in CI, never local" → assume test pollution; run `python scripts/find_polluter.py`.
- "Customer says it's broken, I see nothing" → demand exact steps + tenant ID + timestamp; pull logs for that exact window.

### Minimise the reproducer
Shrink the repro systematically — remove inputs, callers, config, data, and steps **one at a time**, re-running the loop after each cut. Done when every remaining element is load-bearing: removing any one makes it pass. Minimising shrinks the hypothesis space before Step 3.

### When investigation reveals "no root cause"
Almost every case where an agent concludes "there is no root cause" is an incomplete investigation. If you reach that feeling:
1. List what you HAVE checked (boundaries logged? `git diff HEAD~5` read? recent changes mapped? the full error message read?).
2. List what you have NOT checked yet.
3. If there are gaps, close them before declaring the bug "environmental / timing / flaky".

Only after a complete investigation is it legitimate to classify something as `environmental`, `flaky` or an `external dependency` — and even then, instrument for the next occurrence (structured logging, a metric, an alert). "I could not reproduce it" without added instrumentation is not the same as "there is no root cause".

### Check recent changes
```bash
git diff HEAD~5
git log --oneline -10
```
Then the changes git does not show: a dependency bumped in the lockfile, a config value, an environment difference between where it works and where it fails.

### Multi-component tracing
Log **at every boundary**, not only where it breaks. In a typical full-stack path: client → request context → service → data layer → driver. Each boundary records INPUT (what arrived), OUTPUT (what leaves) and CONTEXT (user, tenant, timestamp).
```typescript
console.error("=== tRPC input ===", { input, userId: ctx.userId });
console.error("=== Service args ===", { tenantId, filters });
console.error("=== Query params ===", { where: conditions });
console.error("=== Result ===", { count: result.length });
```

### Pattern analysis — compare with what works
Before hypothesising, find the nearest **working** example of the same pattern in this codebase — the sibling procedure that does not 500, the component that hydrates cleanly. If the broken code implements a documented pattern, read the reference implementation **completely**, every line, not the snippet. List **every** difference between working and broken, however small: "that can't matter" is where the cause hides. Then write down what the broken path depends on that the working one does not — config, environment, middleware order, an assumption about data shape. Each difference is a hypothesis candidate for Step 3.

### Exit criteria
- [ ] Reproducer command is one shell line (or one script invocation), no human steps
- [ ] 3 consecutive runs produce identical failure OR variance is parameterized
- [ ] Repro is minimised (every element load-bearing)
- [ ] Reproducer saved to `.graph-powers/logs/<bug-id>-repro.{sh,py,ts}` for hand-off
- [ ] If browser-driven: snapshot + console + errors + network logs under `.graph-powers/logs/<bug-id>-*`
- [ ] If DB-driven: `psql` query saved that reads the offending row(s)

---

## Step 3 — Hypothesise (P3)

Before reading source code, write **≥3 falsifiable hypotheses**, each in the form:

> *If `<X>` is the cause, then `<Y>` will eliminate the bug (or `<Z>` will make it worse).*

Each hypothesis must:
1. Name a **specific code path / config / env / data condition** as the suspected cause.
2. Name a **specific probe** (debugger breakpoint, tagged log, REPL inspection, differential test, schema query) that would **disprove** it if the value/state isn't what the hypothesis predicts.
3. Be **falsifiable** — if no probe can disprove it, it's a guess, not a hypothesis. *Discard vibes.*

Rank the hypotheses by probability and **checkpoint with the user** for domain knowledge before instrumenting (Step 4).

### Example (API 500 on a list procedure)
> **H1:** If caused by an unguarded cross-tenant join in the router that serves the failing procedure, adding `eq(child.tenantId, ctx.tenant.id)` to the child SELECT eliminates the 500.
> **Probe:** log the generated SQL and confirm the tenant predicate is absent.
>
> **H2:** If caused by an unbounded `.returning()` destructure after a failed insert, adding `if (!row) throw new TRPCError(...)` eliminates the 500.
> **Probe:** logs show `Cannot read properties of undefined` right before the 500.
>
> **H3:** If caused by the auth middleware not running for this route matcher (no user on the context), extending the matcher eliminates the UNAUTHORIZED masquerading as a 500.
> **Probe:** `console.error("DEBUG_BUG_C500_CTX", { userId: ctx.userId })` logs `undefined` for the failing request.

### Cognitive biases to avoid
| Bias | Symptom | Countermeasure |
|------|---------|----------------|
| **Confirmation** | Seeking proof, ignoring disproof | Ask: "What would disprove this?" |
| **Anchoring** | Fixating on first error | Read ENTIRE output before hypothesis |
| **Fixation** | Persisting with wrong approach | 2-strike rule: change approach after 2 failures |
| **Ownership** | "My code is fine" | Same scrutiny for your code as unfamiliar code |
| **Optimism** | "That should fix it" | Run gates EVERY time |

### Rationalizations vs reality
Rationalisation is the **conscious** excuse for skipping process under pressure — unlike bias, which is unconscious:

| Excuse | Reality |
|--------|---------|
| "A simple bug does not need process" | A simple bug has a simple root cause — the process takes five minutes |
| "It is an emergency, there is no time" | Systematic debugging is faster than a guess-and-check loop |
| "I will try first and investigate if it fails" | The first approach sets the session's pattern — start right |
| "I will test once the fix is confirmed" | An untested fix does not hold; the test is what proves it |
| "Several fixes at once saves time" | You lose the ability to isolate what worked — and create new bugs |
| "I do not need the whole doc, just the snippet" | Partial understanding guarantees a problem |
| "Visible symptom = root cause found" | Seeing a symptom is not understanding its origin |
| "One more attempt after two failures" | Three or more failures means the wrong architecture, not the wrong hypothesis |

### Anti-patterns
- **Single hypothesis** = confirmation-bias trap. Always ≥3.
- **"It's probably X"** without a probe = guess. Add the probe or drop the hypothesis.
- **Hypothesis that maps to the symptom, not the cause** = symptomatic. Push one 5-Whys step deeper.
- **Pretending to know.** If you cannot state what X does, say "I do not understand X" and research or ask the user before ranking — a hypothesis built on a guess about X is a guess twice over.

### Choose the Step 4 tag prefix
Pick a unique tag, e.g., `DEBUG_BUG_C500` (≤24 chars, no spaces, ALL_CAPS). Every probe / log / breakpoint added in Step 4 must include this prefix verbatim, so Step 6 cleanup is a single grep:
```bash
# Grep tool: pattern `DEBUG_BUG_C500` under ${paths.backendRoot} and ${paths.frontendRoot}
# — must return 0 hits at commit time
```

---

## Hand-off (Steps 4–6)

With the reproducer minimised and the leading hypothesis chosen, Step 4 hands over to
`references/methodology.md` — instrument, root-cause trace, bisect, defense-in-depth, postmortem.
Which gate opens which Step is in `Skill("debugger") § Engine`; the RED test exercises
the **real production seam** (`references/methodology.md § Fix Verification Criteria`).

---

## Gate to Step 4

On top of the Step 2 exit criteria above: the loop is rank 1–4 (5–8 needs a stated reason), ≥3
falsifiable hypotheses are written and ranked with a disproving probe each, the user has seen the
ranking, and the tag prefix is chosen. Then enter Step 4 with the reproducer and the hypotheses
handed to the sub-agents (`references/pack-guides.md § Parallel-research templates`).
