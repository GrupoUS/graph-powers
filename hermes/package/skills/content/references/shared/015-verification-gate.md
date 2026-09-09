> Hermes auxiliary: `content/` paths are `file_path` values relative to the registered-document parent. Apply the loaded graph-engineering mapping and host policy; this file is served without template expansion.

## Section 1.5: Verification Gate (evidence before completion)

No claim of done, fixed or passing without command evidence that still covers the changed boundary.
Reuse a green result from this session when neither its inputs nor environment changed; rerun it
when the diff, dependency, environment, or a new failure can invalidate it.

1. **IDENTIFY** the command that proves the claim.
2. **RUN or reuse** the complete applicable result.
3. **READ** the full output and the exit code; count the failures.
4. **VERIFY** that the output confirms the claim. If it does not, state the actual status, with the evidence.
5. **Only then** claim — and cite the evidence.

Skipping a step is asserting, not verifying.

| Claim | Requires | Not enough |
|---|---|---|
| Tests pass | applicable test output: 0 failures | "should pass" |
| Build succeeds | build command: exit 0 | linter clean, logs look fine |
| Bug fixed | the original symptom re-tested | code changed, assumed fixed |
| Regression test works | red-green: fails with the fix reverted, passes with it | passes once |
| Agent completed | the diff shows the change | the agent's report |
| Requirements met | line-by-line checklist against the plan | tests passing |

| Excuse | Reality |
|---|---|
| "Should work now" | Run it. |
| "I'm confident" | Confidence is not evidence. |
| "Linter passed" | Linter ≠ compiler. |
| "The agent said success" | Verify independently. |
| "A partial check is enough" | Partial proves nothing. |

Apply at:
- Tail of any command that mutates code (`/implement`, `/debug` fix mode, `/design` Phase 2, `/perf fix`, `/evolve`).
- Inside `/verify` Phase 0 — gates pass condition becomes evidence-bound, not assumption-bound.
- Per-phase tail inside `/implement` Mode B and `/debug` fix mode when the prior result no longer
  covers the phase.

Anti-pattern: marking a task complete after only inspecting code; running `bun run type-check` then forgetting to check exit code; assuming a fix worked because the diff "looks right".
