```markdown
# OpenAI Codex Planning Prompt: Graph Powers no Hermes

## 1. Executive Summary e Early Gate
Atue como Planner no OpenAI Codex. Tier Complex/L6: empacotamento, carregamento e fronteiras de segurança entre plugin e host. Produza um plano, não uma instalação.
[USER] Pedido literal: “então faço um relatório e faço um prompt para eu aprimorar esse plugin, porque eu criei ele para que ele não leve bloqueio mais do Hermes e ele seja adaptado para o Hermes.” (confidence 5/5 quanto à intenção).
Objetivo verificável: adaptar a distribuição e os contratos do Graph Powers ao Hermes, mantendo scanner e aprovações nativos; sem prometer zero alertas.
Early Gate: permaneça read-only. Não escreva, não edite, não implemente, não instale, não importe código do plugin nem execute seus testes/verificadores antes da aprovação explícita `OK`, `approve` ou `proceed` ao plano apresentado.
Inspecione fontes e produza o plano completo na resposta. Se uma ambiguidade mudar o desenho, apresente exatamente uma pergunta bloqueante, preferencialmente com alternativas, e pare a dependência. Caso contrário, rotule premissas e prossiga com a leitura.
Ao terminar o plano, peça aprovação e pare. Silêncio não é aprovação. Aprovar o plano só autoriza o escopo de desenvolvimento explicitado; instalação/ativação em perfil real, commit, push, PR, publicação, deploy, alteração de credenciais e restart exigem autorização própria.

## 2. Codebase Findings
Fonte G: https://github.com/GrupoUS/graph-powers/tree/b24f390a24c9229d24c17924e165ba6fd1512928 . Preserve esse SHA completo. Descubra o checkout local; não suponha `/workspace` nem troque a revisão silenciosamente.
Fonte H: `/Users/mauricio/.hermes/hermes-agent`, HEAD observado `22488b8c62d3c92f25149053ae8df68fb0afcb35`. Reconfirme HEAD/status e regras aplicáveis antes de planejar mudanças.
[EVIDENCE] `/Users/mauricio/.hermes/reports/graph-powers-install-blocked.json` e receipt indicado nele: instalação nativa com `--ref` e `--no-enable` saiu 1, DANGEROUS, 518 ocorrências; 31 CRITICAL, 11 HIGH, 195 MEDIUM, 281 LOW. São achados estáticos, não 518 vulnerabilidades demonstradas (confidence 5/5).
[REPO] G `__init__.py:38-95`: descobre skills, documentos de comando e contratos de agente; chama apenas `ctx.register_skill`. `plugin.yaml:1-21`: versão 1.19.3, sem tools/hooks/capabilities declarados (confidence 5/5).
Contrato: [REPO] G `AGENT_SETUP.md:333-344` exige prova do pacote instalado, Doctor e carga em sessão nova; hooks Graph Powers = `NOT ENFORCED` (confidence 5/5).
[REPO] H `hermes_cli/plugins_cmd.py:625-654`: clone pinado, scan do alvo e só então troca/metadata. `tools/plugin_guard.py:124-159`: community, scan estático e DANGEROUS bloqueado mesmo com force (confidence 5/5).
Motor estático: [REPO] H `tools/skills_guard.py:394-418,626-629` usa padrões por linha e severidade máxima; não prova alcançabilidade em execução (confidence 5/5).
[REPO] H `hermes_cli/plugins.py:974-998`: namespace automático `graph-powers:<nome>`; registro de skill não cria slash command nem executa agente (confidence 5/5).
Portabilidade: [REPO] G `commands/plan.md:8-12`, `agents/explorer.md:1-27` e `hermes/skills/graph-engineering/SKILL.md:18-46` precisam de tradução de ferramentas, caminhos e limites de delegação; compatibilidade completa não foi exercitada (confidence 4/5).
Verificação: [REPO] G `bin/verify-hook-clients.py:334-355,419-444` importa o entrypoint e executa Doctor; `.github/test_hermes.py:86-125` aceita SKIPPED quando falta runtime. Esse sucesso não prova instalação funcional (confidence 5/5).

## 3. Assumptions & Unknowns e protocolo de pesquisa
Fase 1, repo-first: leia AGENTS.md, README, manifests, gerador, loader, scanner, CI, testes e chamadas reais. Não replique instruções do harness. Toda conclusão determinante precisa de `path:line`, revisão e confidence 1-5/5.
Fase 2, web condicional: só para fato determinante ainda com confidence ≤3 após leitura local. Documentação oficial: https://hermes-agent.nousresearch.com/docs/user-guide/features/plugins . Use GET raw pinado se o checkout G não existir; não faça clone/fetch com escrita antes do gate.
Fase 3, reconciliação: código define comportamento atual; documentação oficial define contrato externo. Registre divergências e revise a confiança. Governance: Rollback N/A | Risk premissa falsa | Approval somente leitura.
[UNVERIFIED] Classificação causal completa dos 518 achados, fechamento transitivo das referências, compatibilidade mínima do Hermes e distribuição candidata ainda não estão provados.
[UNVERIFIED] Não há execução do plugin, smoke de carga nem scanner de um pacote corrigido neste relatório. Dependência crítica com confidence ≤2 fica BLOCKED até obter a evidência exata.

## 4. ADLC Intent / Discover / Design / Validation Gate
| Lens | Directive |
|---|---|
| Intent | Preserve o objetivo e identifique o resultado mínimo. |
| Discover | Repositório primeiro; diferencie fato, inferência e lacuna. |
| Design | Reuse a projeção Hermes existente; menor alteração reversível. |
| Validate | Após aprovação, capture comando, exit code e saída real de cada gate. |
| Govern | Em cada fase registre Governance: Rollback, Risk e Approval. |
| Observe | Declare risco residual e o teste que detecta sua regressão. |

## 5. Layer Map
G/service: entrypoint, gerador e contratos. G/presentation: manifest e guia de instalação. G/verification: pacote, referências e testes. H/cross-cutting: scanner e políticas, somente numa mudança upstream separada e autorizada.
Invariantes: `graph-powers`, nomes públicos e prefixo `agent-` preservados; colisões falham explicitamente; carga sob demanda; nenhuma alteração do prompt cache/toolset no meio da conversa; nenhuma invasão de perfil, configuração, identidade ou permissões do host.
Mantenha zero tools/hooks/capabilities adicionais no escopo mínimo. Contratos de agentes são instruções, não enforcement de modelo, ferramentas ou acesso somente leitura. Não importe políticas permissivas de outro cliente.

## 6. Recommended Approach + Alternative
Preferência a confirmar: distribuição Hermes genuína e autocontida, derivada das fontes canônicas, com conteúdo operacional adaptado, referências/scripts necessários, licenças/NOTICE e proveniência. Aproveite `hermes/install.mjs`; não crie inventário paralelo manual.
O diretório `hermes/` atual não é por si só o pacote completo. Escolha a raiz distribuível depois de mapear dependências e preservar nomes/funcionalidade; documente cada inclusão e exclusão por necessidade do produto, nunca pelo resultado do scanner.
Não remova testes/docs/regras para maquiar o scan, não oculte/codifique strings, não use cópia manual em plugins, allowlist ampla, force, desativação de scanner ou carregamento tardio de conteúdo excluído. O pacote final continua sujeito ao scanner padrão.
Alternativa: preservar a distribuição completa e propor correção upstream contextual do scanner para falsos positivos demonstrados, com repro mínimo e regressões maliciosas. Não isente diretórios, extensões, fences ou strings só porque se chamam teste/documentação. Contexto incerto continua sinalizado; aprovação e versão upstream são dependências, não atalhos locais.

## 7. Hierarchical Atomic Task Plan
L0: Graph Powers instalável e utilizável pelo caminho nativo, sem reduzir as proteções do Hermes.
L1-A: diagnóstico e contrato de distribuição. L1-B: adaptação do conteúdo e pacote. L1-C: prova de segurança e compatibilidade. L2 contém os únicos itens que podem propor alterações de código, sempre após aprovação.
TASK-01 | cross-cutting | G `__init__.py:38`, H `tools/plugin_guard.py:124`, receipt | 1) reconciliar SHA/achados; 2) mapear importação, registro, carga de texto e scripts referenciados; 3) classificar exemplos por risco/componente | Depends nenhum; leitura paralela permitida | Validation tabela com evidência; Rollback N/A | Acceptance falsos positivos locais separados de riscos instrucionais; Risk classificação incompleta; Approval leitura.
TASK-02 | service | G `hermes/install.mjs:104-182`, `plugin.yaml:1`, `AGENTS.md:8-28` | 1) fechar dependências; 2) definir raiz/proveniência; 3) derivar manifesto/registro sem duplicar inventário | Depends 01 | Validation geração determinística e pacote autocontido; Rollback reverter somente diff próprio | Acceptance nenhum conteúdo necessário omitido ou baixado depois do scan; Risk pacote incompleto; Approval desenvolvimento.
TASK-03 | service | G `hermes/skills/graph-engineering/SKILL.md:18-85`, `commands/plan.md:8-12`, `agents/explorer.md:1-27` | 1) mapear APIs/caminhos reais; 2) adaptar contratos necessários; 3) preservar nomes e política do host | Depends 02 | Validation cargas reais sem tokens/caminhos inválidos e sem execução automática; Rollback projeção anterior | Acceptance skill/comando-documento/agente-contrato distinguíveis; Risk permissões indevidas; Approval desenvolvimento.
TASK-04 | verification | G `.github/test_hermes.py:40-125`, `bin/verify-hook-clients.py:334-444`, `.github/workflows/ci.yml:80-83` | 1) separar prova estática de runtime; 2) testar pacote distribuído; 3) tornar SKIPPED/NOT ENFORCED explícitos | Depends 02-03 | Validation gates existentes + falha esperada sem runtime/pacote/referência; Rollback diff de testes/verificador | Acceptance source checkout não substitui pacote instalado; Risk falso PASS; Approval desenvolvimento.
TASK-05 | verification | H `tests/tools/test_plugin_guard.py:41-159,171-227`; G CI | 1) escanear pacote candidato sem importá-lo; 2) testar casos benignos e maliciosos; 3) manter bloqueio antes de efeitos | Depends 02; não exige executar conteúdo G | Validation matriz da seção 9; Rollback descartar artefatos de teste autorizados | Acceptance DANGEROUS bloqueia e CAUTION exige decisão explícita; Risk reduzir detecção; Approval sandbox de testes.
TASK-06 | cross-cutting | H `tools/plugin_guard.py:69-78`, `tools/skills_guard.py:394-418`, testes correlatos | 1) só se 05 comprovar falso positivo impeditivo, preparar repro; 2) propor regra contextual restrita; 3) exigir revisão upstream e regressões negativas | Depends 05; opcional, não paralelizar mudança de política | Validation detecção maliciosa preservada; Rollback versão anterior | Acceptance nenhuma exceção específica Graph Powers; Risk scanner enfraquecido; Approval upstream separada.
TASK-07 | verification | G `AGENT_SETUP.md:333-344`, H loader/instalador | 1) instalar nativamente em ambiente descartável; 2) Doctor + cargas novas; 3) simular isolamento e rollback | Depends 03-05 e 06 se necessário | Validation estado antes/depois e recibos da seção 9; Rollback nativo e restauração restrita de backup | Acceptance nenhum perfil real alterado; Risk vazamento/cache; Approval sandbox explícito, perfil real separado.

## 8. Sprint Contracts
Sprint 1: diagnóstico | Scope 01 e decisões de 02 | Done when plano citado completo | Verified edge case achado em deny-rule não é execução | Out of scope instalação | Gate aprovação do plano; Governance: Rollback N/A | Risk atribuição errada | Approval leitura.
Sprint 2: pacote e contratos | Scope 02-04 | Done when artefato reproduzível com dependências completas | Verified edge case colisão e referência ausente falham | Out of scope hooks executáveis | Gate revisão do diff; Governance: Rollback diff próprio | Risk perda de contrato | Approval desenvolvimento.
Sprint 3: segurança e prova nativa | Scope 05, 07; 06 só se necessário | Done when todas as evidências obrigatórias existem | Verified edge case pacote perigoso não altera destino | Out of scope rollout em produção | Gate scanner + runtime; Governance: Rollback sandbox/backup do alvo | Risk falso positivo ou falso PASS | Approval por ambiente.

## 9. Validation Plan
Antes de autorizar execução, confirme os comandos existentes e seus efeitos. Não chame programa remoto de read-only só porque o nome contém verify/doctor; verifique importações e subprocessos. Use interpretador do Hermes e Bun para JS, sem instalar dependências nesta fase.
Após aprovação, gates G existentes: `bun hermes/install.mjs --check`; `python3 -X utf8 .github/test_hermes.py`; `python3 .github/test_file_references.py`; `python3 .github/check_file_references.py`; `python3 .github/check_portability.py`. Se alterar conteúdo compartilhado/rails, acrescente `python3 hooks/test_hooks.py` após revisão do runner e isolamento.
Para H, use o runner obrigatório: `scripts/run_tests.sh tests/tools/test_plugin_guard.py`; se tocar o instalador, `scripts/run_tests.sh tests/hermes_cli/test_plugins_cmd.py`. Descubra testes de namespace/multiprofile no checkout atual, sem inventar nomes. Testes que criam commits de fixture precisam de autorização restrita ao sandbox; nunca ao projeto real.
Matriz positiva: pacote benigno passa política padrão; geração repetida idêntica; referências locais completas; namespace/cargas reais; nenhuma mudança de configuração/permissão no register; versão e revisão registradas coincidem com a fonte aprovada.
Matriz negativa: execução destrutiva alcançável, exfiltração de segredo fictício, prompt injection em documentação carregável, symlink/traversal, colisão, dependência ausente e conteúdo perigoso disfarçado de teste continuam rejeitados/sinalizados. Nunca execute payloads perigosos; forneça bytes sintéticos ao scanner e use mocks para testar decisões.
Prova nativa posterior: em HOME/HERMES_HOME descartáveis e sem credenciais, use `hermes plugins install <FONTE_APROVADA> --ref <SHA_COMPLETO_APROVADO> --no-enable`; os marcadores são placeholders, não comandos prontos. Pare em DANGEROUS; CAUTION requer revisão/consentimento, nunca force automático.
Leia o alvo via `hermes plugins show graph-powers`; confirme source, SHA, metadata e estado desabilitado. Só então, no sandbox autorizado, `hermes plugins doctor <PACOTE_INSTALADO> --ci` e o verificador revisado com `--client hermes --plugin-root <FONTE_REVISADA> --package-root <PACOTE_INSTALADO> --project-dir <PROJETO_TEMP> --expected-version <VERSAO> --json`.
Em processo/sessão nova autorizado, carregue `skill_view("graph-powers:planning")`, `skill_view("graph-powers:plan")` e `skill_view("graph-powers:agent-explorer")`; valide referências reais e ausencia de hooks/tools/slash commands não prometidos. Qualquer enable necessário fica restrito ao sandbox; Doctor não certifica gateway existente.
Isolamento: simule dois homes/perfis com o mesmo nome de plugin, caminhos distintos e instâncias novas; nada deve cruzar cache, registry, configs, identidades, skills ou credenciais. Capture hashes sem mostrar conteúdos sensíveis. Nos perfis reais default, ayla, custodio, divo, emilio, estrela e laura, o resultado esperado nesta fase é nenhuma alteração.
Cada gate retorna comando exato, cwd, revisão, exit code, saída relevante e estado PASS/FAIL/SKIPPED/UNVERIFIED. Exit 0 com SKIPPED não satisfaz runtime. Não declare testes futuros como executados.

## 10. Risk, Security & Rollback
Riscos prioritários: instruções carregadas mudarem permissões; pacote perder dependências; scanner ganhar exceções amplas; verificador confundir registro com execução; cache/perfis misturarem estado.
Não habilite hooks Graph Powers para resolver o bloqueio. `NOT ENFORCED` descreve esses hooks, não ausência das proteções nativas Hermes. Qualquer enforcement futuro exige desenho e autorização próprios.
Rollback: em código, reverta apenas o diff autorizado, preservando trabalho alheio. Em sandbox, remova a instalação pelo caminho nativo e compare com a baseline. Em eventual perfil real autorizado, restaure só config/metadata/pacote do alvo a partir do backup verificado, preservando permissões, links e mudanças concorrentes; não restaure a frota inteira.

## 11. Acceptance Criteria
Plano entregue com evidências, dependências, riscos e decisão de distribuição; implementação continua bloqueada até autorização.
Pacote futuro mantém funcionalidade/namespaces aprovados e referências completas, sem operações de rede/importação surpresa nem mudanças de política. O scanner padrão permanece ativo; a instalação só prossegue conforme seu veredito real.
Doctor do pacote instalado, carga nova de skill/comando-documento/agente-contrato, regressões negativas e isolamento têm evidências próprias; hooks = NOT ENFORCED. Nenhum critério é substituído por contagem histórica, mock isolado ou registro em lista.

## 12. Implementation Order e condições de parada
Ordem: 01 → plano/aprovação → 02 → 03 → 04; 05 após existir candidato; 06 somente se bloqueio demonstrado; 07 após gates anteriores. Não misture correção do plugin com autorização para modificar Hermes upstream.
Pare se SHA divergir sem conciliação, fonte estiver truncada, requisito crítico não tiver evidência, pacote perder referência, scanner bloquear, runtime faltar, cache cruzar perfil, teste obrigatório falhar ou ação exceder autorização. Retorne bloqueador exato e menor evidência necessária; não repita instalação em outro perfil.

## 13. Tool / Permission Allowlist
Antes de aprovação: leitura/busca de arquivos não sensíveis; Git status/rev-parse/show/diff sem escrita; GET de fontes oficiais/pinadas; análise estática sem imports do plugin. Sem execução de scripts G, testes, clone, fetch, geração, installs ou alterações de repo/profile/config.
Depois de aprovação: apenas arquivos/TASKs, testes e sandbox explicitamente autorizados; package manager Bun quando aplicável. Sem credenciais, rede mutável, alterações de scanner local em produção, Kanban, commit/push/PR/deploy/publicação ou restart implícitos.
Approval Checkpoint: entregue o plano verificável e solicite aprovação explícita para o escopo seguinte. Não execute a primeira TASK de desenvolvimento na mesma resposta sem essa aprovação.
```
