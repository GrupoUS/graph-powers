## Section 8: Sequential Phase Gating pattern

When phases have dependencies (Phase N requires Phase N-1 output):

```
Phase N-1 → produce artifact → checkpoint gate → Phase N → ...
```

Each gate verifies:
- Required artifact present (file written, agent returned, tests passed)
- Quality threshold met (gate output matches contract)
- No regression in prior phase output

If a gate fails → STOP. Don't proceed silently. Either:
- Re-run prior phase with corrected scope
- Escalate to evaluator (Mode 3)
- Switch to `/debug recover`

Never collapse phases when their outputs feed each other (e.g., schema → API → UI).
