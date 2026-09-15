# Graph Powers: integracao nativa Kilo e LSP

## Destino e decisoes

Implementar suporte reproduzivel ao Kilo para configuracao, hooks, agentes, comandos, skills, planejamento, orquestracao e LSP. Provar descoberta e execucao reais, nao somente existencia dos arquivos.

- Usuario confirmou reutilizar conexoes autenticadas atuais. Nao criar gateway, alterar credenciais ou configurar OmniRoute.
- Preservar modelo principal escolhido manualmente. Modelos auxiliares e preferencias pessoais ficam no config global nativo; nao versionar IDs pessoais no harness compartilhado.
- Claude continua fonte canonica; projecoes Kilo sao geradas. Reutilizar utilitarios existentes sem renomear a integracao Codex e declarar equivalencia.
- Usar `.kilo/agent/`, `.kilo/command/` e equivalentes globais em `~/.config/kilo/`. Nao criar diretorios legados.
- Config compartilhada global; projeto guarda contratos, dependencias locais e excecoes indispensaveis.
- [ASSUMED] Alvo e runtime moderno Kilo CLI/extensao. Registrar versoes testadas; extensao legada fora do escopo.
- Nao alterar configuracoes de outros clientes/editores, indexacao, MCPs, credenciais, worktrees ou Agent Manager por efeito colateral.
- Este arquivo e o unico artefato desta fase. `docs/plans`, declarado pelo projeto, foi negado pelas permissoes; usado o diretorio autorizado `.kilo/plans`.

## Evidencia inicial

- `git status --short` estava limpo no inicio.
- `bin/graph-powers.mjs` e `bin/verify-hook-clients.py` nao oferecem target Kilo. Inventario encontrado: 12 agentes, 14 skills, 13 comandos canonicos.
- `~/.kilo/` possui skills, sem agentes; catalogo desta sessao expoe somente `explore`. Algumas skills instaladas ainda contêm caminhos/invocacoes Codex.
- `~/.config/kilo/kilo.jsonc` nao declara agentes, modelos, plugins ou LSP; preservar suas permissoes e indexacao existentes.
- Reuso: `codex/install.mjs`, `codex/lib.mjs`, `codex/model-policy.*`, `cursor/install.mjs`, politicas em `hooks/`, contratos SDD em `skills/planning/`.
- Politica `references/shared/130-typescript7-oxc-gates.md`: vtsls, Oxlint e Oxfmt locais, sem downloads em hooks/edicao. `package.json` declara Oxlint/Oxfmt/TS7, nao vtsls.
- Kilo localizado no PATH; servidores pesquisados nao encontrados no PATH. Isso nao prova ausencia em dependencias/cache.

## Preflight runtime (2026-09-14)

Executado nesta sessao, sem contornar permissoes:

- `kilo --version` = **7.6.2** (binario compilado em `@kilocode/cli-linux-x64`; tipos `@kilocode/plugin` instalados em `~/.config/kilo/node_modules`).
- Catalogo: `kilo models` confirma `kilo/~openai/gpt-astra-latest` (Astra), `kilo/~openai/gpt-luna-latest` (Luna) e `kilo/deepseek/deepseek-v4.1-flash` (candidato "Flash 4.1"). Resolucao por ID exato, nao por alias.
- Diretorios comprovados em HOME isolado: config global `~/.config/kilo/kilo.jsonc`; agentes `~/.config/kilo/agent/*.md`; comandos `~/.config/kilo/command/*.md`; plugin `~/.config/kilo/plugin/*.ts`; skills globais `~/.kilo/skills/` (o runtime tambem le `~/.config/kilo/skill/`). Projeto: `kilo.jsonc` na **raiz do repo git** (nao `.kilo/`), `.kilo/agent/` (e `agents/`), `.kilo/command/`, `.kilo/skills/`, `.kilo/plugin/`.
- Config aceita e preserva no `debug config`: `subagent_model`, `lsp: true`, `agent.<id>` JSON com `permission.task`. Schema instalado: `lsp: false | { [id]: {command, extensions?, disabled?, env?, initialization?} }`; `formatter`; `instructions`; `experimental.hook.file_edited`/`session_completed`.
- API de plugin instalada: `export default { id, server }`; hooks `tool.execute.before/after`, `permission.ask`, `event`, `chat.*`, `command.execute.before`, `shell.env`, `config`; sem `Stop` nativo.
- Ferramenta `task`: `{ description, prompt, subagent_type, background }`; filho nao interativo; `hidden` so oculta autocomplete.
- Comandos Kilo: `$ARGUMENTS` e `@file`; frontmatter `description`, `agent`, `model`, `variant`, `subtask`. Skills: `name` deve igualar o diretorio; invocadas pela ferramenta `skill`; casam por `description`; compat `.agents/skills/` e `.claude/skills/`.
- Agentes embutidos: `ask`, `code`/`build`, `plan`, `debug`, `compaction`, `explore`, `general`, `orchestrator` (deprecado), `summary`, `title`. Delegacao e por `task` em primarios com tool access; nao ha "codificador" separado.
- `~/.kilo/skills/graph-powers-*` instalados sao projecoes **Codex** (referenciam `~/.codex/graph-powers/...`): errados para Kilo. Auditar proveniencia antes de substituir (Task 2).

## Arquitetura

Artefatos canonicos -> adaptador `kilo/` -> projecoes validadas -> instalador global com ownership -> descoberta Kilo -> comando/skill -> `task` por agente registrado -> modelo nativo configurado -> handoff ao pai -> gates.

Politicas existentes -> plugin Kilo -> eventos suportados -> entrada normalizada -> decisao. Permissoes nativas sao a primeira barreira; hooks complementam, nao concedem consentimento.

Arquivo -> servidor LSP por extensao e raiz -> executavel do projeto/instalacao existente -> diagnosticos e simbolos. Formatacao tem um dono por caminho.

Nao copiar hooks/frontmatter Claude literalmente nem executar `Workflow(...)` como se fosse API Kilo.

## Tarefas

### 1. Preflight de contratos e modelos

- Ler AGENTS proximos, config e gates; identificar versoes CLI/extensao, caminhos efetivos e overrides sem expor segredos.
- Executar `kilo --version`, `kilo agent list` e `kilo models` sem `--refresh` quando permitido. Consultar metadados seguros, nao dumps de credenciais/config efetiva.
- Verificar na versao instalada: diretorios singulares, precedencia, exports/plugins, servidores LSP embutidos, permissoes e variantes de modelos.
- Registrar matriz SUPPORTED/UNSUPPORTED/UNVERIFIED. Documentacao menciona `subagent_model`, mas schema publico consultado nao o declara: nao emitir sem suporte comprovado.
- Permissoes: paginas oficiais dizem ultima regra correspondente; referencia local contem contradicao. Testar negativos antes de confiar na ordenacao.
- Resolver Astra/Luna como IDs reais `provider/model-id`; testar chamada minima com ferramentas e metadados. Falha bloqueia ativacao, nao provoca fallback silencioso.

Aceite: contratos e IDs comprovados; versao desconhecida ou contrato insuficiente bloqueia somente a capacidade dependente. Nao contornar permissoes para executar probes.

### 2. Adaptador e instalacao Kilo

Owns: novo `kilo/`, integracao em `bin/graph-powers.mjs`, testes de instalacao.

- Derivar inventario de `agents/`, `commands/`, `skills/`, `references/`; reutilizar pequenos utilitarios existentes.
- Emitir agentes nativos, comandos finos e deltas de skills. Traduzir invocacoes/caminhos especificos de cliente, preservando nomes publicos e links.
- Compartilhar skills ja compativeis; nao manter segunda copia manual. Auditar colisao e proveniencia de `~/.kilo/skills/` antes de substituir.
- Target Kilo explicito, dry-run, instalacao idempotente e manifesto de arquivos/chaves gerenciados. Nao expandir silenciosamente instalacoes automaticas existentes.
- Registrar `kilo` nas enumeracoes de cliente comprovadas pela pesquisa: `bin/graph-powers.mjs` (`VALID_TARGETS`, help, probes, steps, verify), `bin/verify-hook-clients.py` (choices, loop `all`, `package_layout`, `client_is_in_use`, `verify_one`), `.github/check_clone.py`, `.github/check_version_bump.py`, `.github/check_file_references.py`, `.github/check_portability.py`, `.github/test_hook_clients.py` e os donos de versao.
- Preservar JSONC, comentarios, campos pessoais e arquivos de terceiros. Conflito sem ownership interrompe escrita, nao autoriza sobrescrita.
- Gerar candidato em home temporario; testar repeticao, conflito, interrupcao, mudanca de raiz e rollback limitado.

Aceite: geracao deterministica e cadeia caller -> gerador -> destino -> descoberta verificavel, sem duplicar inventario.

### 3. Modelos e permissoes por papel

Owns: projecao dos agentes e configuracao global Kilo gerenciada.

| Perfil | Agentes | Preferencia |
|---|---|---|
| Planejamento/julgamento | project-planner, evaluator, security-reviewer, skill-improver, ui-ux-designer | Astra |
| Execucao | debugger, frontend-specialist, mobile-developer, performance-optimizer | Luna |
| Verificacao | verification | Luna, preservando restricoes do papel |
| Pesquisa | explorer, librarian | Luna inicialmente, sujeito a medicao |

- Uma fonte global por atribuicao. Prompts/comandos nao repetem modelo pessoal; `agent.<id>.model` ou superficie equivalente comprovada governa o filho.
- DeepSeek chamado "Flash 4.1 flash" e candidato, nao ID confirmado. Somente ativar com correspondencia inequivoca no catalogo e teste; se ambiguo, solicitar ID antes de habilitar e manter fora da configuracao ativa.
- Nao transportar aliases Claude, slugs Codex ou effort `max` por analogia. Variant/effort somente quando suportados pelo provider real.
- Falha de modelo informa papel/ID/causa segura; nao herdar Astra nem trocar provider silenciosamente.
- Filhos leaf: negar `task` e limitar profundidade quando suportado. Pesquisa/revisao sem edicao e sem shell generico mutavel; incluir ferramentas alternativas/MCPs no exame de permissao.
- Modelo nao e argumento demonstrado da ferramenta `task`; provar resolucao pelo agente em sessao nova.
- Comparar Luna/DeepSeek nas mesmas tarefas por gates, custo, latencia e retrabalho; nao declarar superioridade sem medicao.

Aceite: cada papel aparece e executa com modelo esperado; negativos comprovam restricoes de escrita/delegacao.

### 4. Hooks nativos

Owns: plugin Kilo e ajustes minimos em normalizacao/politicas `hooks/`; ler `hooks/AGENTS.md`.

- Mapear cada politica para evento comprovado; registrar omissoes e impacto. Nao copiar manifesto Claude como se fosse Kilo.
- Usar API nativa `@kilocode/plugin`, `tool.execute.before`/`after` conforme versao. Bloqueio ocorre antes; after nao desfaz efeitos.
- Reutilizar politicas Python quando viavel via subprocesso portavel, stdin JSON limitado e timeout; sem shell construido com entrada do modelo.
- Config/payload malformado ou falha operacional: fail-open com aviso seguro conforme regra do repo; violacao identificada: bloqueio explicito. Permissoes nativas continuam vigentes em falha do hook.
- Nao autoaprovar `permission.ask`, criar loops Stop, supervisao de transcritos ou spawn em hooks.
- Formatacao somente do arquivo alterado, uma vez, sem recursao nem downloads.

Aceite: positivos/negativos, payload invalido, timeout, caminhos com espacos e ferramentas alternativas; prova de evento real apos reload.

### 5. Planejamento e orquestracao

Owns: deltas Kilo dos metodos e call sites; contrato comum permanece canonico.

- Preservar `/plan -> planning -> aprovacao -> /implement -> /verify` e SDD existente; sem runtime `Workflow(...)` Claude presumido.
- Pai escolhe especialista, fornece contexto delimitado, aguarda/consolida. Background somente para escopos independentes e capability comprovada; nao significa isolamento de filesystem.
- Preservar caps declarados, ownership, reserva de revisao, retomada e leaf.
- Modelos pertencem aos perfis nativos, nao a prose de skills. Escalacao apenas por limitacao observada e registrada.
- Reconciliar skill pessoal `agent-orchestration` e execution floor sem exportar preferencias pessoais a todos os clientes.

#### 5.1 Cadeia real de papeis (corrige "planner -> coder -> debugger")

Nao existe agente `coder`, `planner` nem `orchestrator` no plugin. A cadeia canonica e:

| Etapa | Comando | Skill | Agentes |
|---|---|---|---|
| Pesquisa | `/research`, `/prime` | dominio | `explorer`, `librarian` (background) |
| Planejamento | `/plan`, `/issue-improve` | `planning` | `project-planner` (sintese) + `evaluator` (revisao independente) |
| Execucao | `/implement` (Phase C) | `planning` | escritores: `debugger` (generalista/coder), `frontend-specialist`, `performance-optimizer`, `mobile-developer`; UI apos o codigo: `verification` |
| Debug | `/debug` | `debugger` | `debugger` (packs B/C/D) + `explorer`; frontend: `frontend-specialist` |
| Verificacao | `/verify` | dominio | `evaluator` sempre; `security-reviewer` (auth/api/schema); `ui-ux-designer` (web) |
| Revisao | `/pr-review` | dominio | `evaluator`, `security-reviewer`, `ui-ux-designer` |
| Alta garantia | `/gauntlet` (opt-in, L3+) | `planning` | builder != inspector (`evaluator`) |

`/issue-improve` e **plan-only** (comenta no issue, nunca implementa); nao existem `/issue` nem `/improve` separados.

#### 5.2 Equivalencia Claude -> Kilo (obrigatoria nos artefatos gerados)

| Literal canonico | Kilo | Regra |
|---|---|---|
| `Skill("graph-powers:planning")`, `Skill("debugger")` | ferramenta `skill`, nome = diretorio (`planning`, `debugger`) | remover prefixo/namespace; `name` deve igualar o diretorio |
| `graph-powers:<agente>` | `subagent_type: "<agente>"` / `@<agente>` | remover o prefixo `graph-powers:` |
| `Task(...)`, `Agent(...)`, `subagent_type` | ferramenta `task` `{description, prompt, subagent_type, background}` | mapear campos 1:1 |
| `Workflow({name:'graph-powers:ultra-plan'\|'ultra-verify'})` | inexistente | usar o fallback ja declarado; **nunca** retentar nome que nao resolve |
| frontmatter `tools: Read, Glob, ...` / `disallowedTools` | `permission` (`edit`/`bash`/`webfetch`/`external_directory`) e/ou mapa `tools` boolean | revisor/pesquisa -> `edit: deny`; leaf -> `task` negado |
| `model: opus/haiku/...`, `effort: xhigh` | `model: <provider/model>` real ou omissao; `variant`/`options` so com suporte comprovado | nao transportar alias Claude nem `max`/`ultra` por analogia |
| `$ARGUMENTS` | `$ARGUMENTS` | compativel |

#### 5.3 O que impede o roteamento automatico hoje

1. Prefixo `graph-powers:` nao existe no Kilo; `graph-powers:explorer` nao resolve.
2. `Skill(...)` e `Workflow(...)` sao exclusivos do Claude; nao ha runtime equivalente.
3. Skills canonicas nao estao instaladas para Kilo: `~/.kilo/skills/graph-powers-*` sao projecoes Codex apontando para `~/.codex/graph-powers/...`.
4. Comandos projetados ainda nao definem `agent:`/`subtask`; sem isso o primario decide sozinho.
5. Agentes embutidos `explore`/`plan`/`debug`/`general` competem com `explorer`/`project-planner`/`debugger`; a delegacao automatica casa por `description` e nao e deterministica.
6. Sem `permission.task` por agente, o limite leaf (ex.: `evaluator`) fica apenas advisory.

#### 5.4 Requisitos de implementacao do roteamento

- Traduzir os literais da tabela 5.2 na projecao dos comandos e skills (nao basta copiar bytes).
- Emitir cada comando Kilo em `.kilo/command/<nome>.md` (global `~/.config/kilo/command/`) com frontmatter `description` + `agent` explicito e corpo com `$ARGUMENTS`, preservando nomes publicos.
- Instalar as skills canonicas (dir == `name`) em `~/.kilo/skills/` com `${CLAUDE_PLUGIN_ROOT}` reescrito para o caminho Kilo; nunca reusar as projecoes Codex.
- Instalar os 12 agentes em `~/.config/kilo/agent/<nome>.md` com `mode: subagent`, `permission` traduzido e `description` que desambigue dos embutidos.
- Definir agente primario/router (ou instruir `code`/`plan`) que nomeia `subagent_type` exatos e um allow-list `permission.task`; garantir que `/plan` use `project-planner`+`evaluator`, `/implement` use os escritores, `/debug` use `debugger`, `/verify` use `evaluator`.
- Provar negativos: leaf sem `task`; revisores/pesquisa sem `edit`; nenhum literal `graph-powers:` ou `Workflow(` sobrevive nos artefatos instalados.

Aceite: em sessao Kilo nova, `/plan` roteia `planning`+`project-planner`+`evaluator`, `/implement` roteia escritores da Phase C, `/debug` roteia `debugger`, `/verify` roteia `evaluator`, `/issue-improve` permanece plan-only e `/gauntlet` permanece opt-in; `kilo debug agent <papel>` confirma cada alvo; cenarios mostram filhos reais, papel/modelo correto e tratamento explicito de agente/revisor ausente.

### 6. LSP e formatacao

Owns: configuracao global gerenciada, dependencias locais estritamente necessarias, adaptacao Kilo do setup e testes LSP.

- LSP auxilia diagnostico/navegacao; nao e requisito de descoberta de skills/agentes nem substituto de testes.
- Schema consultado: `lsp` booleano/objeto; campos `command`, `extensions`, `env`, `initialization`, `disabled`. Objeto habilita embutidos mais overrides: identificar/desabilitar concorrentes por IDs reais.
- JS/TS/MJS/CJS/JSX/TSX: vtsls para semantica/navegacao; Oxlint local para diagnosticos rapidos, sem typed lint no loop. Nao apontar vtsls para SDK TS7 sem prova; bloqueio do adapter Zed nao prova bloqueio Kilo.
- Python: reutilizar servidor nativo existente; se ausente, Pyright como candidato validado contra interpretador/imports dos hooks. Nao instalar Pyright e BasedPyright juntos.
- JSON/JSONC: servidor JSON para schemas Graph Powers/Kilo. YAML somente para workflows/configs reais. Frontmatter Markdown continua coberto pelos validadores existentes; LSP Markdown fora do escopo sem lacuna concreta.
- Oxfmt unico formatador dos formatos cobertos. Preferir `formatter` nativo se validado; se hook for dono, nao duplicar formatacao automatica. Nao habilitar Prettier/ESLint concorrentes.
- Instalar somente dependencias necessarias na implementacao autorizada, com versoes controladas e runner apropriado. Config global resolve por projeto; nao fixa caminho deste checkout para todos os repositorios.
- Nao baixar pacotes no startup/hook/diagnostico. Servidor ausente gera UNAVAILABLE acionavel.
- Provar `kilo debug lsp diagnostics <file>`, `kilo debug lsp document-symbols <uri>` e navegacao quando exposta. Fixtures isoladas: erro conhecido, correcao, import Python entre arquivos, JSON invalido contra schema.

Aceite: inicializacao/diagnosticos/simbolos reais, erros desaparecem apos correcao, sem providers duplicados. Repetir apos reinicio e em duas raizes para provar resolucao local. Separar evidencia CLI/extensao.

### 7. Gates, rollout e rollback

- Declarar novos gates Kilo em `.claude/rules/verify-supplements.md` e CI. Separar prova estatica, instalacao e runtime; gates antigos nao certificam Kilo.
- Adicionar `.github/check_kilo.py` (paralelo a `check_cursor.py`/`check_grok.py`): reexecutar o gerador e provar equivalencia de roteamento (5.2), frontmatter traduzido, JSONC preservado, idempotencia, preservacao de terceiros e ausencia de `graph-powers:`/`Workflow(`. Job CI `kilo` paralelo aos jobs codex/cursor/grok.
- Gates existentes aplicaveis: `python3 hooks/test_hooks.py`, `python3 .github/test_hook_clients.py`, `python3 .github/check_wiring.py`, `python3 .github/test_file_references.py`, `python3 .github/check_file_references.py`, `python3 .github/check_portability.py`, `python3 .github/check_machine_paths.py`, `python3 .github/check_context_budget.py`, `python3 .github/check_listing_budget.py`, `python3 .github/check_placeholders.py`.
- Se alterar SDD: `python3 skills/planning/scripts/test_sdd.py`. Se alterar helpers comuns: gates declarados Codex/Cursor/Grok. Executar demais gates exigidos pelas superficies alteradas.
- Revisao independente das permissoes/contratos antes da ativacao. Especialista ausente significa BLOCKED, nao autorrevisao anunciada como PASS.
- Sequencia: candidato isolado -> gates -> diff e backup limitado -> instalacao global -> nova sessao -> smoke agentes/modelos/hooks/LSP -> relatorio com comandos, exit codes e lacunas.
- Rollback restaura somente artefatos/chaves gerenciados, verificando alteracoes posteriores de terceiros. Sem reset de worktree, sobrescrita total do config ou remocao de skills por suspeita.
- Sem commit, push, publicacao, deploy ou worktree neste escopo.

## Riscos e bloqueios de ativacao

- Versao local, IDs Astra/Luna e disponibilidade DeepSeek nao verificados. Preflight bloqueia ativacao dependente; nao inventa substituto. DeepSeek pode permanecer explicitamente nao configurado.
- Docs e schema divergem; runtime instalado e testes determinam campos suportados.
- LSP global pode resolver dependencias erradas; testar duas raizes e preservar configuracao anterior.
- Skills pessoais sem ownership comprovado exigem confronto de conteudo antes de migracao.
- Revisao especializada indisponivel no catalogo atual. Nenhum gate/runtime aprovado nesta fase.

## Fontes oficiais consultadas em 2026-09-14

- https://kilo.ai/docs/customize/custom-subagents
- https://kilo.ai/docs/customize/agent-permissions
- https://kilo.ai/docs/automate/extending/plugins
- https://kilo.ai/docs/automate/tools
- https://kilo.ai/docs/code-with-ai/platforms/cli
- https://kilo.ai/docs/code-with-ai/platforms/cli-reference
- https://kilo.ai/docs/code-with-ai/agents/model-selection
- https://app.kilo.ai/config.json

Paginas consultadas diretamente ou via snapshot oficial `https://kilo.ai/docs/llms.txt`. Evidencia documental nao substitui prova runtime.
