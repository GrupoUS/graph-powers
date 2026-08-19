# DESIGN.md — the spec for the host project's design authority

> **This file is not a document about Graph Powers.** It is the specification the agent applies when
> it creates or improves the `DESIGN.md` of the project the plugin is installed into.
>
> Read by: `AGENT_SETUP.md § 5`, `/design`, `ui-ux-designer`, `frontend-specialist`.

---

## What the project's `DESIGN.md` is for

One question, answered once: **when two visual decisions conflict, which one wins?**

Without that file, every design decision is re-litigated per component, and the answer depends on
who is at the keyboard. With it, an agent has an authority to cite and a person has something to
disagree with.

It is **not** a style guide, not a component catalogue, and not a screenshot gallery. It is the set
of decisions that constrain the next decision.

**Where it lives:** `DESIGN.md` at the project root, or wherever the project already keeps its
design authority. If a design source already exists under another name (`docs/design-system.md`, a
Figma link in the README, a token file), that is the authority — this spec improves it in place
rather than creating a second one. **Two design authorities is worse than none**, because now
"which one wins" has to be answered about the files themselves.

---

## Required sections

Each one exists because its absence causes a specific, observed failure. A section that cannot be
filled with a real answer is deleted, not filled with a placeholder — an invented token is worse
than an absent one, because agents will use it.

### 1. Tokens — the only names allowed in code

The palette, the type scale, the spacing scale, the radii, the shadows, the motion durations. **By
semantic name, with the literal value beside it**, and a pointer to the file that defines them.

```markdown
| Token | Value | Use for |
|---|---|---|
| `--surface` | #0B0F14 | Page and card backgrounds |
| `--text` | #E6EDF3 | Body copy |
| `--accent` | #F5B301 | One primary action per view |
```

The rule this section exists to enforce: **a colour literal in a component is a decision nobody can
change later.** If the codebase has hex values scattered through it, say so here — the gap is a
finding, not something to hide.

### 2. Named rules — the decisions with IDs

The constraints that keep coming back, each with a short identifier so a review can cite one instead
of re-explaining it.

```markdown
| ID | Rule | Why it exists |
|---|---|---|
| D1 | One primary action per view | Two primaries measured as no primary |
| D2 | Never colour alone as a state carrier | Fails for 8% of men |
| D3 | Motion animates transform/opacity only | Everything else forces relayout |
```

**Give each rule a reason that names a cost.** A rule whose "why" is "it looks better" is a
preference, and preferences do not survive contact with a deadline.

### 3. Hierarchy and density

How the project decides what is loud: type scale steps, weight range, the maximum simultaneous
emphases per view, the default information density (is this a dashboard or a landing page?).

The most common defect an agent produces without this section is a screen where everything is
emphasised, which reads as nothing emphasised.

### 4. Component authority

Which component library, where the primitives live, and — the important part — **the extend-versus-
create policy.** When is a new component justified, and when is it a variant of one that already
exists?

```markdown
Primitives: `src/components/ui/` — do not fork one, extend it.
A new primitive needs: three call sites, or one that cannot be expressed as a variant.
```

### 5. Non-negotiables

The accessibility floor, restated here because designers read this file and not the safety floor:
contrast ratio, focus ring, keyboard operability, `prefers-reduced-motion`, minimum touch target,
minimum font size. Numbers, not adjectives.

### 6. What this project deliberately does not do

The refused patterns. Carousels, modals over modals, infinite scroll on a task surface, animated
counters on financial data — whatever this project decided against, with the reason. Without this
section the same rejected idea returns every quarter.

---

## How the agent builds it

**Never invent a value.** Every number in this file comes from the repository or from the user.

1. **Read what exists first.** The token file, the theme config, the component directory, the
   existing design document under any name. `grep` for hex literals and count them — that number is
   the honest starting state.
2. **Derive, do not decide.** If the codebase uses a 4 px spacing grid in 90% of places, the grid is
   4 px and the other 10% is a finding. If it uses three greys with no name, say there are three
   unnamed greys.
3. **Ask about anything genuinely undecided.** Brand colour, tone, density preference — these are
   the user's to answer, one question at a time.
4. **Mark the gaps.** A section with no real answer gets one line: `Not decided — <what would settle
   it>`. That is a working document. A section filled with plausible defaults is a fiction that
   agents will then enforce.

---

## Improving a `DESIGN.md` that already exists

The default is **improve, never replace**.

1. `diff` the existing file against this spec: which required sections exist, which are missing,
   which exist under another name.
2. **Every existing decision is preserved verbatim.** Somebody made it, probably after something
   went wrong, and the reason may not be written down. Rewording it loses the reason.
3. Add only the missing sections, sourced per the rules above.
4. Where the existing file contradicts itself — two spacing scales, a rule stated twice with
   different numbers — **surface the contradiction and ask.** Do not pick the newer one.
5. Show the diff before writing. Then write.

---

## Quality bar

Before the file is considered done:

- [ ] Every token in the file exists in the codebase, and every token in the codebase is in the file
- [ ] Every named rule has a reason that names a cost
- [ ] No `{{PLACEHOLDER}}` survives
- [ ] No number was invented — each traces to a file or to an answer from the user
- [ ] Under 200 lines. Longer than that and it stops being read, which makes it decorative
- [ ] The accessibility floor is stated as numbers
- [ ] Gaps are marked as gaps, not filled with defaults

---

## What follows from it

Once the project has this file, three things reference it and none of them duplicate it:

- `.claude/rules/design.md` — the auto-loaded rule, generated from `templates/rules/design.md`,
  which **points at** `DESIGN.md` rather than restating it;
- `/design` — loads it before any visual work;
- `ui-ux-designer` — cites its rule IDs in every critique.

If any of those three ends up restating a decision from `DESIGN.md`, the copies will diverge. One
thing, one place.
