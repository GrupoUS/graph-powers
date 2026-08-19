# {{PROJECT_NAME}}

> Graph Powers template for the root `AGENTS.md` — read by Codex CLI from the git root down to the
> working directory, and by other agent tools that follow the same convention. Replace the
> `{{PLACEHOLDERS}}` and remove this line.
>
> Codex stops reading at 32 KiB of combined instruction files. Keep this short enough that the
> project's own rules still fit underneath it.

## What this project is

{{ONE_PARAGRAPH}}

| | |
|---|---|
| Stack | {{STACK}} |
| Package manager | {{PACKAGE_MANAGER}} |
| Work branch | {{WORK_BRANCH}} |
| Protected | {{PROTECTED_BRANCHES}} |

## Invariants `[HARD]`

Each one exists because a violation already cost something.

{{CARDINAL_RULES}}

## Gates

Run these before claiming anything is done, and quote the output:

```bash
{{TOOLING_COMMANDS}}
```

A gate this project does not declare is reported as not declared — never as passing.

## Where things live

{{ROUTING_TABLE}}

<!-- The Graph Powers installer maintains a delimited block below. Do not hand-edit inside the
     markers: the next install rewrites it. -->
