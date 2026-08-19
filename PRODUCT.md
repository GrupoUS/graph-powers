# PRODUCT.md — the spec for the host project's product brief

> **This file is not a document about Graph Powers.** It is the specification the agent applies when
> it creates or improves the `PRODUCT.md` of the project the plugin is installed into.
>
> Read by: `AGENT_SETUP.md § 5`, `/plan`, `uxmaster`, `project-planner`.

---

## What the project's `PRODUCT.md` is for

One question, answered once: **when a change is technically fine but the product is worse, what
catches it?**

An agent given a feature request will build the feature. It will not ask whether the feature serves
the person the product is for, because it has no way to know who that is. This file is that way.

It is **not** a marketing page, not a roadmap, and not a spec for one feature. It is the standing
context that makes a scope decision reviewable.

**Where it lives:** `PRODUCT.md` at the project root. If the project already keeps this in a README
section, a wiki, or a brief under another name, that is the authority — improve it in place. Do not
create a second one.

---

## Required sections

### 1. What this is, in one paragraph

What the product does, for whom, instead of what. Written so someone who has never seen the
repository can tell whether a proposed feature belongs.

The test: read the paragraph, then read a feature request. If you cannot tell whether it fits, the
paragraph is too vague — usually because it describes the technology instead of the job.

### 2. Who it is for — and who it is not

```markdown
| | |
|---|---|
| Primary user | <who, concretely — a role, a situation, not a demographic> |
| The job they hire it for | <the outcome they want, in their words> |
| What they use today | <the incumbent, including "a spreadsheet" and "nothing"> |
| Explicitly not for | <the user this product will not serve, and why> |
```

**The "not for" row is the one that does work.** Without it, every request looks in scope.

### 3. The critical paths

The two to five flows the product exists to deliver. Named, in order, with what breaks if each one
breaks.

```markdown
| Flow | Entry point | Breaks how |
|---|---|---|
| Sign-up → first value | / | Nobody ever becomes a user |
| <domain action> | /app | The product does nothing |
```

This is what `/verify` and `/pr-review` treat as the blast radius. A change that touches a critical
path is reviewed harder — but only if the paths are written down.

### 4. Voice

How the product speaks: to whom, at what register, in what language, with what it never says.
Two or three lines plus one before/after example.

```markdown
Direct, second person, no jargon the user did not bring.
Never: "oops", exclamation marks in errors, blaming the user.
  Bad:  "Oops! Something went wrong 😅"
  Good: "We could not save that. Your changes are still here — try again."
```

Agents write UI copy constantly, and without this section they default to a voice that belongs to
no product.

### 5. The honesty gate `[HARD]`

Non-negotiable, and ahead of any conversion target:

- No false urgency — a counter that resets, "only 2 left" that is untrue, a deadline that does not
  exist.
- Consent is never pre-checked.
- The exit is visible: cancel, close and back exist and are findable.
- Total cost appears before the commitment, not at the last step.
- No pattern that depends on the user not noticing in order to work.

If a technique needs the person not to notice, it does not ship. That is not abstract ethics: it is
the difference between a metric that holds and one that collapses the moment users work it out.

### 6. What this product will not do

The refused scope, with reasons. The features requested repeatedly and declined; the adjacent market
deliberately not entered; the integration that would change what the product is.

Without this section, an agent treats every request as a requirement, and the roadmap becomes the
union of everything anyone ever asked for.

### 7. How success is measured

The two or three numbers that actually decide whether this is working, with their current value and
the date it was read. Not a dashboard inventory — the numbers a decision would turn on.

A number with no date is a number nobody will trust in six months.

---

## How the agent builds it

**Most of this file cannot be derived from the code.** That is the point, and it is why this step
asks more questions than the others.

1. **Extract what the repository already says.** README, landing copy, marketing pages, route names,
   the domain vocabulary in the schema. That is the draft.
2. **Ask about what only a person knows** — one question at a time, never a questionnaire: who is
   this for, what do they use instead, what have you deliberately refused.
3. **Never invent a user.** "Small businesses that want to grow" is not a user; it is filler. If the
   answer is unknown, write `Not decided — <what would settle it>` and move on.
4. **Quote, do not paraphrase.** When the user describes their product, their words go in. A
   paraphrase loses the distinction they were making.

---

## Improving a `PRODUCT.md` that already exists

1. `diff` against the required sections: which exist, which are missing, which live elsewhere.
2. **Preserve every existing claim verbatim.** A product statement is a decision, and it is often
   the residue of an argument that already happened.
3. Where the existing file and the repository disagree — the brief describes a flow the code no
   longer has — **report the drift, do not silently correct it.** Which one is stale is the user's
   call, and it is usually interesting.
4. Add only the missing sections.
5. Show the diff before writing.

---

## Quality bar

- [ ] The "not for" row is filled, and it excludes someone real
- [ ] The critical paths match routes that exist in the repository
- [ ] The voice section has one before/after example
- [ ] Every number has a date
- [ ] Nothing was invented — each claim traces to the repository or to the user's own words
- [ ] Unknowns are marked as unknown, not filled with plausible defaults
- [ ] Under 150 lines

---

## What follows from it

- `/plan` reads it before scoping any feature — it is what makes "out of scope" a citable answer;
- `uxmaster` uses the critical paths and the honesty gate as the frame for every UX judgement;
- `.claude/rules/ux.md` points at it rather than restating the honesty gate.
