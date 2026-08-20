## Section 1.5: Verification Gate (evidence before completion)

Before any command (or phase inside a command) claims success, invoke:

```typescript
Skill("superpowers:verification-before-completion");
```

The skill enforces: a verification command was actually run, its full stdout + exit code are captured, and the claim of "done / fixed / passing" cites that evidence. No claim without evidence.

Apply at:
- Tail of any command that mutates code (`/implement`, `/debug` fix mode, `/design` Phase 2, `/perf fix`, `/evolve`).
- Inside `/verify` Phase 0 — gates pass condition becomes evidence-bound, not assumption-bound.
- Per-phase tail inside `/implement` Mode B and `/debug` fix mode.

Anti-pattern: marking a task complete after only inspecting code; running `bun run type-check` then forgetting to check exit code; assuming a fix worked because the diff "looks right".
