## Section 0.5: Superpowers Bootstrap

Every command **MUST** invoke the superpowers meta-router as the first skill load, before any other skill, agent, or Bash call:

```typescript
Skill("superpowers:using-superpowers"); // meta-router — sets discipline + announce pattern
```

This loads the discipline-skill index and the "announce-before-action" rule. Domain skills load **after** the method layer, in the order `120-skill-invocation-order.md` sets.

Exceptions:
- `/prime` is a context loader — it only **recommends** the next command run the bootstrap.
- Subagents skip the bootstrap (superpowers `<SUBAGENT-STOP>` directive).
