# Plano: verificação mais rápida (Bash, Bun, tsgo)

> **Só plano.** Sem implementação neste turno.
> Trabalho em `~/Projects` (graph-powers + neondash). Sem commit/push.

**Goal:** Cortar tempo e RAM dos comandos de verificação sem trocar o contrato dos gates.

**Arquitetura:** O gargalo não é o Bash. É (1) o `/verify` completo disparar 3–4 agentes LLM e (2) o Turbo rodar o monorepo inteiro. As ferramentas certas já estão no NeonDash: Bun, tsgo, oxlint, Biome, Vitest via `bun run test`.

**Stack alvo:** Omarchy 4 · 9800X3D · Bun 1.4.0 no host · NeonDash pin `bun@1.3.9` · `tsgo` 7 nativo.

---

## Diagnóstico (evidência deste PC)

### O que o agente chama de “Bash”

No Claude Code / Graph Powers, **Bash é só o lançador** do processo (`python3 …`, `bun run …`, `tsgo …`). Spawn de shell no Linux é ~1 ms. Trocar Bash por dash, fish, systemd-run ou “Go puro” **não** muda o tempo de um type-check.

No Hermes o equivalente é a tool `terminal` — mesma história.

**Conclusão:** não reescrever o harness para “sair do Bash”.

### NeonDash (onde a verificação pesa)

Já está no caminho certo (`AGENTS.md` + `.claude/config.json`):

| Gate | Comando real | Motor |
|---|---|---|
| Types | `bun run type-check` → `turbo run check` → `tsgo --noEmit` | **tsgo** (Go), não `tsc` Node |
| Lint | `bun run lint:oxlint:check` → `oxlint` | **oxlint** (Rust) |
| Format | `bunx biome …` | **Biome** |
| Teste | `bun run test` → `turbo run test` → **Vitest** | proposital; `bun test` nu é **proibido** (ignora o config) |

Host já tem Bun **1.4.0**. O repo ainda pede `packageManager: bun@1.3.9`.

### Graph Powers (o plugin)

Gates oficiais são **Python stdlib** (`hooks/test_hooks.py`) + uns `node *.mjs` de wiring. `packageManager: npm` aqui é correto: o repo não é app JS. Forçar `bun test` nesse repo seria o fallback errado do `bun-verify`.

### O que realmente come RAM/CPU

1. **`/verify` full** (não `quick`): dispara em paralelo explorer + evaluator + security + designer. Cada um é um modelo. Isso é o pico de RAM, não o oxlint.
2. **`turbo run test` / `turbo run check` sem `--filter`**: type-check e Vitest dos dois apps mesmo quando o diff é um arquivo.
3. **Playwright / agent-browser** se alguém mistura E2E no gate unitário.
4. **Fan-out de agentes** no Graph Engineering L4+ para um gate que devia ser um processo.

---

## Pesquisa: o que é mais rápido em 2026

| Camada | Melhor no seu hardware | Não fazer |
|---|---|---|
| Shell do agente | Bash/terminal (irrelevante) | Reescrever em Go “pra ser rápido” |
| Type-check | **tsgo** (já no NeonDash) | `npx tsc` / `typescript@5` |
| Unit/integration | **Vitest via `bun run test`** (já) | `bun test` nu; Jest; `node --test` |
| Lint | **oxlint** (já) | ESLint default |
| Format | **Biome** (já) | Prettier+ESLint |
| Runtime | **Bun 1.4** (menos RAM, `test --parallel`) | Node 26 só para Playwright Windows IPC |
| Orquestração monorepo | Turbo **com `--filter` no change set** | Turbo na raiz a cada save |

Bun 1.4 (blog 20/08/2026): −35% RAM, idle CPU 5×, startup Linux +50%, `bun test --parallel`. Útil no **host** e depois de alinhar o pin 1.3.9→1.4. **Não** substitui o Vitest do NeonDash.

---

## O que aprimorar (ordem)

### 1. Hábitos do `/verify` — ganho imediato, zero código

- Dia a dia: **`/verify quick`** (só gates + floor).
- Full (agentes) só em PR / L4+.
- Hermes: L1–L2 sem `delegate_task` de verification.

### 2. Escopo Turbo no NeonDash — maior ganho de wall-clock

Hoje `bun run type-check` = `turbo run check` em **web+api**.

Proposta: o `/verify` e o Step 5 resolvem o change set e chamam:

```text
bunx turbo run check test --filter=<app tocado>
```

Diff só em `apps/web` → não type-checka a API. Contrato do gate continua `tsgo` + Vitest.

Arquivos: `Projects/neondash/.claude/config.json` (`tooling.commands` ou `verify-supplements`), skill `bun-verify` documentando `--filter`.

### 3. Alinhar Bun 1.4 no NeonDash — experimental, A/B

1. Medir `bun run type-check` e `cd apps/api && bun run test` no 1.3.9 (via pin).
2. Subir pin para `bun@1.4.0`, `bun install --frozen-lockfile` só depois de regenerar lock **como tarefa própria**.
3. Comparar tempo + RAM. Manter se ≥10% mais rápido e suite igual.
4. Continuar **proibindo** `bun test` nu.

### 4. Graph Powers plugin

- Manter testes em `python3 hooks/test_hooks.py`.
- Trocar só os `node .github/check_*.mjs` por `bun .github/check_*.mjs` se o A/B mostrar diferença (provavelmente mínima).
- Não inferir `bun test` neste repo (`testRunner` já é Python).

### 5. O que **não** fazer

- Trocar Bash.
- Trocar Vitest por `bun test` no NeonDash.
- Voltar para `tsc`.
- Instalar Ananicy/mais um runner.
- Ligar `/verify` full em todo save.
- `bun test --no-isolate` para “ir mais rápido” (contamina testes).

---

## Tarefas (quando autorizar)

### Task 1 — Documentar `/verify quick` como default no eixo bun-verify

**Files:** `Projects/graph-powers/skills/bun-verify/SKILL.md`, `commands/verify.md` (1 parágrafo).

Critério: o texto diz explicitamente que full = agentes = caro.

### Task 2 — Resolver `--filter` a partir do change set (NeonDash)

**Files:** `Projects/neondash/.claude/config.json` ou um wrapper `scripts/verify_scoped.py` (Python stdlib, já é o estilo do repo).

Critério: diff só em `apps/api` não dispara `tsgo` da web. Medir 3× antes/depois.

### Task 3 — A/B Bun 1.4 no NeonDash

**Files:** `package.json` `packageManager` + `bun.lock` (protegido — precisa autorização).

Critério: tabela tempo/RAM; rollback = pin 1.3.9 + lock antigo.

### Task 4 — Hermes Step 5

**Files:** `~/.hermes/plugins/graph-powers/skills/graph-engineering/SKILL.md` (espelho) e a skill em Projects.

Critério: L1–L2 não dispara agente de verification.

---

## Validação

Medir no mesmo 9800X3D, 3 corridas:

| Comando | Hoje (baseline) | Depois |
|---|---|---|
| `bun run type-check` | | |
| `cd apps/api && bun run test` | | |
| `bun run lint:oxlint:check` | | |
| `/verify quick` (só processos) | | |
| `/verify` full (com agentes) | | |

Não declarar ganho dentro da variação.

---

## Riscos

- `turbo --filter` mal calibrado = gate verde sem type-checkar o pacote vizinho. Mitigar: filter por `apps/*` tocado + `packages/*` se o diff entra em package.
- Bun 1.4 lockfile v2/v3 quebra CI em runner 1.3. Mitigar: subir Bun no CI no mesmo PR.
- Alguém “otimiza” para `bun test` e a suite Vitest some. Mitigar: HARD rule já existe — não mexer.

## Decisão pedida

Autoriza só Task 1+2 (doc + filter), ou também o A/B do Bun 1.4 (mexe em lockfile)?
