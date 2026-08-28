# Plano: verificação com baixo consumo de recursos

## Destination

Reduzir processos, CPU, RAM e fan-out durante edição/verificação sem remover gates, segurança ou
compatibilidade entre Claude Code, Codex, Cursor e Grok:

- JS/TS usa Oxlint para diagnósticos e Oxfmt para formatação; o pacote local TypeScript 7 permanece
  declarado para compatibilidade do toolchain e para o gate final explícito.
- Vitest continua Vitest; Bun Test fica restrito a projetos que o declaram e recebe limites baixos.
- Stop/PostToolUse executam somente um processo local curto sobre os caminhos relevantes, sem cache ou
  perfil adicional.
- `/verify` rápido permanece barato; revisão/fix loop continuam explícitos e limitados.

## Out of scope

- Não trocar o runner de um projeto host, alterar lockfiles, instalar dependências ou modificar outro repositório.
- Não remover `graph_guardrails`, `protect_files`, trust/approval, git gates ou floors de segurança.
- Não ativar dispatcher, fan-out recursivo, commit, push, merge ou qualquer operação irreversível.

## Reuse ledger

| Decisão | Asset existente | Uso |
|---|---|---|
| PRESERVE | `hooks/_change_set.py` | Reusar somente o cache atômico já existente para o gate de pre-commit; Stop/format não criam cache.
| EXTEND | `hooks/_config.py` + `schema/config.schema.json` | Manter os comandos declarados como a única autoridade do projeto, sem defaults de perfil.
| PRESERVE | `graph_guardrails.py`, `protect_files.py`, `command_trust.py` | Rails de segurança e aprovação permanecem inalterados em comportamento.
| EXTEND | `workflows/ultra-verify.js` | Batching pelo `maxParallelWave`, sem nova camada de orquestração.

## Regression watchlist

| Comportamento | Prova |
|---|---|
| Hook fail-open e paridade de clientes | `python3 hooks/test_hooks.py`; `python3 .github/test_hook_clients.py` |
| Type-aware Oxlint fica reservado ao gate final | casos positivos/negativos em `hooks/test_hooks.py` |
| Vitest não vira Bun Test e testes Bun ficam limitados | testes do aprovador + gate de wiring |
| Stop só verifica JavaScript/TypeScript alterado | casos de mudanças relevantes, rede e ferramenta ausente |
| Manifesto e contagem de hooks permanecem coerentes | `bun .github/check_workflows.mjs` + gate nativo da CI |

## Execution graph

1. Diagnóstico e baseline já coletados; confirmar contratos/schema e registrar medições.
2. Implementar Oxc, TypeScript 7, limites de runners e políticas de hooks.
3. Limitar workflow e atualizar comandos, exemplos, templates e documentação ativa.
4. Executar gates completos, benchmark disponível e inspeção final de diff.

## Tasks

- [x] T1 — Adotar Oxc, declarar TypeScript 7 e separar Vitest/Bun Test.
  CHECK: `python3 hooks/test_hooks.py`
  EVIDENCE: `hooks/test_hooks.py` exit 0; `EVERY GUARANTEE HELD`, incluindo type-aware Oxlint fora do gate final, lançadores de rede, Vitest sem limites, Node test runner e Bun sem teto.
- [x] T2 — Aplicar Stop por arquivo relevante e formatter Oxfmt local.
  CHECK: `python3 hooks/test_hooks.py`
  EVIDENCE: `hooks/test_hooks.py` exit 0; Stop sem fallback amplo, rede ou cache novo e PostToolUse limitado a um arquivo.
- [x] T3 — Batching de Ultra/verify/debug/perf e corrigir contagem do manifesto na CI.
  CHECK: `bun .github/check_workflows.mjs`
  EVIDENCE: exit 0; 2 workflows parseados, batching limitado e nomes consistentes.
- [x] T4 — Atualizar referências, exemplos e versão sincronizada.
  CHECK: `python3 .github/check_version_bump.py`
  EVIDENCE: exit 0; versão `1.12.1 -> 1.13.0`, referências sem dangling e fonte única `references/shared/130-typescript7-oxc-gates.md`.
- [x] T5 — Rodar a matriz de gates e comparar o benchmark local antes/depois.
  CHECK: `python3 .github/check_wiring.py`
  EVIDENCE: matriz final exit 0; `check_wiring` 449 referências/0 unresolved, `check_context_budget` 265.739 B, benchmark self-test PASS e melhor comparação próxima com 3 warmups/20 samples: cadeia p50 189,241 ms / p95 189,424 ms após a mudança versus baseline p50 188,960 ms / p95 189,254 ms; falhas 0. Execuções posteriores ocorreram sob loadavg aproximado de 12 em 8 CPUs e foram tratadas como ruidosas, sem alegar ganho de latência.

## Rollback

Reverter somente os arquivos deste plano com o diff salvo pelo revisor; não remover caches de
projetos host, lockfiles ou dados persistentes. Os comandos declarados continuam sendo a autoridade
do projeto; os hooks permanecem fail-open e não criam cache novo nem alteram a lógica de aprovação.
