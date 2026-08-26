## Section 1.5: Verification Gate (evidence before completion)

No claim of done, fixed or passing without fresh evidence from this session. Before any command (or phase inside one) claims success:

1. **IDENTIFY** the command that proves the claim.
2. **RUN** it, fresh and complete — not a previous run, not a partial one.
3. **READ** the full output and the exit code; count the failures.
4. **VERIFY** that the output confirms the claim. If it does not, state the actual status, with the evidence.
5. **Only then** claim — and cite the evidence.

Skipping a step is asserting, not verifying.

| Claim | Requires | Not enough |
|---|---|---|
| Tests pass | test output: 0 failures | a previous run, "should pass" |
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
- Per-phase tail inside `/implement` Mode B and `/debug` fix mode.

Anti-pattern: marking a task complete after only inspecting code; running `bun run type-check` then forgetting to check exit code; assuming a fix worked because the diff "looks right".
