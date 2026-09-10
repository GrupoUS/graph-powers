# Adaptação segura do Graph Powers ao Hermes

## Conclusão

O bloqueio ocorreu no scanner de instalação, antes de o pacote ser colocado no destino. O receipt registra `DANGEROUS`, 518 achados e código de saída 1. Isso não demonstra 518 vulnerabilidades: o scanner reconhece padrões estáticos em código, testes, exemplos e instruções.

A integração nativa já existe no commit analisado. Ela registra skills, documentos de comando e contratos de agentes. Não registra ferramentas nem hooks executáveis do Graph Powers. O trabalho necessário é revisar a distribuição, adaptar os contratos usados no Hermes e provar o comportamento pelo caminho nativo, mantendo o scanner e as aprovações.

Recomendação: planejar uma distribuição realmente específica para Hermes, derivada das fontes canônicas e com dependências completas. Caso falsos positivos demonstrados ainda impeçam a instalação, encaminhar uma correção contextual do scanner upstream, separadamente. Nenhuma dessas propostas garante zero alertas ou autoriza contornar o bloqueio atual.

Entregável complementar: [OpenAI Codex Planning Prompt](PROMPT-CODEX.md). Ele começa em modo somente leitura e exige aprovação antes de desenvolvimento, testes que executem o plugin ou instalação.

## Escopo e evidências

Nota de portabilidade: `<HERMES_HOME>` representa o diretório de dados Hermes da máquina inspecionada. Os caminhos foram normalizados posteriormente; revisões, comandos e resultados abaixo continuam sendo registros da inspeção original, não execuções novas.

Público: Maurício, autor do Graph Powers. Decisão esperada: aprovar um plano de adaptação, não instalar ou ativar o pacote.

| Fonte | Revisão ou localização |
|---|---|
| Graph Powers, fonte G | [`b24f390a24c9229d24c17924e165ba6fd1512928`](https://github.com/GrupoUS/graph-powers/tree/b24f390a24c9229d24c17924e165ba6fd1512928), manifest 1.19.3 |
| Hermes, fonte H | `<HERMES_HOME>/hermes-agent`, HEAD `22488b8c62d3c92f25149053ae8df68fb0afcb35`; working tree sem alterações nos dois checks desta inspeção |
| Bloqueio anterior | `<HERMES_HOME>/reports/graph-powers-install-blocked.json` |
| Receipt anterior | `<HERMES_HOME>/cache/exec/stdout-5e80e8f13d96.txt` |
| Backup anterior | `<HERMES_HOME>/backups/graph-powers-s7n68rw9` |
| Contrato oficial consultado | [Plugins do Hermes](https://hermes-agent.nousresearch.com/docs/user-guide/features/plugins#install-time-security-scanning) |

As referências G abaixo usam o commit fixo; as H apontam para arquivos do checkout local nessa revisão. A inspeção foi estática e somente leitura. Não importei nem executei o plugin, não repeti a instalação e não alterei repos, configurações ou perfis operacionais. Arquivos de planejamento e validação ficam nesta pasta de relatório.

A comparação de bytes entre config atual e backup confirmou igualdade em `default`, `ayla`, `custodio`, `divo`, `emilio`, `estrela` e `laura`. Em todos eles, `plugins/graph-powers` estava ausente e `plugins/.install-metadata.json` não existia. O relatório anterior registra os mesmos sete perfis com configuração/metadata inalterados. Essa baseline comprova a ausência da instalação nesses destinos, não o funcionamento do plugin.

## O que explica o bloqueio

O fluxo nativo observado é:

1. Clonar a fonte e verificar a revisão pedida.
2. Resolver o subdiretório, quando houver, e ler o manifest.
3. Escanear o alvo antes de substituí-lo no diretório de plugins.
4. Somente após aprovação da política, mover o pacote e gravar metadata.

Fontes H: `hermes_cli/plugins_cmd.py:543-561,600-660`. A decisão fica em `tools/plugin_guard.py:147-159`: `safe` permite; `caution` pede confirmação; `dangerous` bloqueia. `--no-enable` não dispensa scan. `--force` não supera um veredito perigoso.

O scanner percorre a árvore, excetuando diretórios técnicos específicos, aplica padrões por linha e faz ajustes próprios para plugins. Não limita a análise ao que `register()` importa. Testes, README, referências e arquivos de outros clientes também entram se estiverem na árvore e tiverem extensão escaneável. Há tratamento parcial de contexto, inclusive docstrings e algumas exceções por tipo de arquivo, mas não uma análise completa do fluxo de execução.

Fontes H: `tools/plugin_guard.py:23-46,54-78,124-144`; `tools/skills_guard.py:394-418`. A política de severidade está em `tools/skills_guard.py:626-629`: basta um achado critical para `dangerous`. Medium/low isolados não bloqueiam. Portanto, diminuir o número total não é o critério correto de sucesso.

### Contagem reconciliada do receipt

A análise programática encontrou exatamente 518 registros, igual ao total declarado:

| Severidade | Ocorrências |
|---|---:|
| CRITICAL | 31 |
| HIGH | 11 |
| MEDIUM | 195 |
| LOW | 281 |
| Total | 518 |

Por categoria: persistence 287; execution 155; destructive 22; supply_chain 20; traversal 16; exfiltration 9; obfuscation 4; injection 2; privilege_escalation 2; credential_exposure 1. Essas são categorias do scanner, não diagnósticos de incidentes.

No `__init__.py`, o receipt contém dois achados LOW, nas linhas 72 e 79, que comparam nomes com `AGENTS.MD` para ignorar esses arquivos no registro. Não há achado associado ao `plugin.yaml` no receipt. Nenhum desses fatos torna o restante da árvore seguro por consequência.

### Amostras com classificação contextual

| Local G | O que a fonte mostra | Leitura técnica |
|---|---|---|
| [`hooks/smart_bash_approver.py:68-80`](https://github.com/GrupoUS/graph-powers/blob/b24f390a24c9229d24c17924e165ba6fd1512928/hooks/smart_bash_approver.py#L68-L80) | Expressões regulares de operações destrutivas na lista de bloqueio | Match estático em regra defensiva. Essa expressão não executa o comando. O arquivo também contém lógica executável, que precisaria de revisão própria se fosse utilizado. |
| [`hooks/test_hooks.py:724-727`](https://github.com/GrupoUS/graph-powers/blob/b24f390a24c9229d24c17924e165ba6fd1512928/hooks/test_hooks.py#L724-L727) | Dicionários de entrada sintética para testes, incluindo comando destrutivo | A linha é dado de fixture, não chamada de shell. Não prova que todos os achados do arquivo sejam falsos positivos, nem autoriza executar o runner sem inspeção. |
| [`README.md:662-674`](https://github.com/GrupoUS/graph-powers/blob/b24f390a24c9229d24c17924e165ba6fd1512928/README.md#L662-L674) | Exemplos de operações recusadas; depois, uma opção que remove a proteção do próprio Graph Powers | Parte dos matches aparece em explicação de bloqueio. Já a instrução permissiva adjacente é material operacional que não deve ser transposto para o Hermes. |
| [`commands/evolve.md:18-24`](https://github.com/GrupoUS/graph-powers/blob/b24f390a24c9229d24c17924e165ba6fd1512928/commands/evolve.md#L18-L24) | Orienta gravar aprendizados e atualizar regra de projeto quando apropriado | Instrução funcional de escrita/persistência, disponível como contrato. Não é código executado ao importar; também não é texto inerte que possa ser descartado da revisão de segurança. |
| [`skills/debugger/references/diagnose.md:20-25`](https://github.com/GrupoUS/graph-powers/blob/b24f390a24c9229d24c17924e165ba6fd1512928/skills/debugger/references/diagnose.md#L20-L25) | Exemplo de HTTP POST com URL de staging parametrizada e token mascarado | Não demonstra exfiltração real. Se seguido, pode causar efeito externo; exige alvo sintético ou autorização adequada. |

Conclusão limitada às amostras: existem correspondências em conteúdo defensivo e fixtures, mas também instruções que podem provocar ações quando carregadas. A classificação causal completa dos 518 itens permanece pendente. Não há evidência aqui de ataque executado, nem uma certificação de ausência de risco.

## O que o Hermes realmente carrega

Em G [`__init__.py:38-95`](https://github.com/GrupoUS/graph-powers/blob/b24f390a24c9229d24c17924e165ba6fd1512928/__init__.py#L38-L95), `planned_registrations()` enumera:

- `hermes/skills/*/SKILL.md` e `skills/*/SKILL.md`;
- `commands/*.md`, exceto `AGENTS.md`;
- `agents/*.md`, exceto `AGENTS.md`, com prefixo `agent-`.

Há verificação de colisão de nomes e existência dos arquivos. `register()` chama somente `ctx.register_skill`. Os imports diretos do entrypoint são de biblioteca padrão; não há importação automática de `hooks/smart_bash_approver.py` nessa cadeia observada.

O loader H executa o módulo e depois `register(ctx)` (`hermes_cli/plugins_loader.py:264-329,423-458`). O conteúdo registrado só se torna instrução quando servido ao agente. `register_skill` gera o namespace do plugin (`hermes_cli/plugins.py:974-998`). O servidor de skills lê o texto, aplica controles/preprocessamento e retorna conteúdo e arquivos relacionados (`tools/skills_tool_plugin.py:123-172`).

Consequências:

- `graph-powers:planning` é uma skill; `graph-powers:plan` é um documento de comando registrado como skill; `graph-powers:agent-explorer` é um contrato de agente registrado como skill.
- Registro não instala automaticamente `/plan` como slash command, não cria um agente executável e não transforma o frontmatter de outro cliente em restrição efetiva de ferramentas/modelo.
- Documentos e referências continuam dentro da superfície de confiança: o agente pode seguir suas instruções ou executar scripts mencionados depois.
- `provides_hooks: []` e `capabilities: []` descrevem o pacote; não constituem sandbox para qualquer código Python que venha a ser incluído nele.

O próprio [`AGENT_SETUP.md:333-344`](https://github.com/GrupoUS/graph-powers/blob/b24f390a24c9229d24c17924e165ba6fd1512928/AGENT_SETUP.md#L333-L344) manda reportar hooks Graph Powers como `NOT ENFORCED`, verificar o pacote instalado com Doctor e carregar skill, documento de comando e contrato de agente em sessão nova. Isso não significa que os controles nativos do Hermes estejam ausentes.

## Lacunas da adaptação atual

| Lacuna | Evidência | Mudança proposta, ainda não implementada |
|---|---|---|
| Distribuição mistura conteúdo de vários clientes | Scan da raiz completa; G `hermes/install.mjs:104-182` apenas projeta manifesto/registro | Definir um produto Hermes autocontido, derivado das fontes canônicas e validado como artefato final. |
| Contratos ainda carregam sintaxe de outros clientes | G `commands/plan.md:8-12`, `agents/explorer.md:1-27`, `skills/planning/SKILL.md:36-38` | Conferir resolução de raízes/referências, `Skill(...)`, argumentos e ferramentas reais; adaptar sem duplicar o inventário. Compatibilidade completa ainda não foi exercitada. |
| Documentação generaliza capacidade e permissões | G `plugin.yaml:3`; adaptador `hermes/skills/graph-engineering/SKILL.md:18-46` | Declarar precisamente o que Hermes suporta e conservar política do host; não importar autonomia permissiva ou suposto enforcement de frontmatter. |
| Verificação pode terminar em SKIPPED com exit 0 | G `bin/verify-hook-clients.py:419-425`; `.github/test_hermes.py:86-125` | Separar teste estático, pacote instalado, runtime presente e sessão nova. SKIPPED nunca satisfaz aceite de runtime. |
| O verificador executa o entrypoint | G `bin/verify-hook-clients.py:334-355,427-444` | Só executá-lo depois de revisão e autorização em ambiente isolado; seu nome não o torna inspeção estática. |
| Dependências do gerador/verificador atravessam a árvore | G `hermes/install.mjs:19,36-45`; `bin/verify-hook-clients.py:381-387` | Preservar ou substituir explicitamente essas dependências na distribuição. Retirar diretórios sem fechar referências quebra o produto. |

O diretório `hermes/` atual contém adaptador/gerador, não um pacote nativo completo com manifest e entrypoint próprios. Instalar esse subdiretório sem outro desenho não é uma solução comprovada. O instalador suporta resolução de subdiretório, mas isso não resolve dependências por si só (H `hermes_cli/plugins_cmd.py:625-638`).

## Proposta de melhoria e limites

### Distribuição Hermes mínima, mas completa

A redução deve decorrer da função do produto, não da lista de padrões que disparam o scanner. Antes de excluir um arquivo, identificar se ele é importado, registrado, lido por referência ou invocado por um workflow suportado.

A distribuição candidata precisa manter manifesto, entrypoint, contratos aprovados, dependências transitivas, scripts necessários, licenças, NOTICE e proveniência da revisão canônica. A geração deve ser determinística e preservar nomes públicos, anchors e frontmatter. Testes e histórico podem permanecer no repositório de desenvolvimento quando não forem parte do produto distribuído, mas nenhuma proteção, referência necessária ou conteúdo problemático pode ser escondido para obter aprovação. Não buscar depois da instalação aquilo que foi retirado do scan.

Para o mínimo útil, manter zero hooks/tools/capabilities novos. Respeitar o namespace `graph-powers`, prefixo `agent-`, colisões explícitas e carga sob demanda. A instalação deve conservar configuração, identidade, permissões e isolamento do perfil, sem modificar o cache de prompt ou toolset no meio da conversa.

### Correção upstream do scanner, somente se demonstrada

Uma proposta upstream pode distinguir uma expressão defensiva de uma chamada perigosa, desde que apresente reprodução mínima, justificativa contextual e testes que preservem detecção de execução maliciosa e prompt injection. Não basta chamar um arquivo de teste, comentário ou documentação: esses locais podem conter instruções consumidas pelo agente.

Manter casos negativos para exfiltração, execução destrutiva, traversal/symlink, conteúdo perigoso mascarado como fixture e adulteração de instruções. O Hermes já possui exemplos de pares benigno/malicioso em `tests/tools/test_plugin_guard.py:128-145`. Ambiguidade deve continuar visível, não ser suprimida globalmente. Essa mudança depende de revisão upstream e não autoriza alterar o scanner instalado neste Mac.

Fora de escopo: desativar scanner, usar force como atalho, codificar/ocultar strings, criar allowlist ampla, apagar arquivos apenas para reduzir alertas, copiar manualmente para plugins, criar hooks próprios para contornar o bloqueio, instalar em outro perfil para tentar obter resultado diferente ou prometer aprovação futura.

## Critérios de aceite e execução posterior

Todos os itens abaixo são propostas de validação, não testes executados nesta inspeção:

1. Revisão G fixada; pacote final reproduzível e com referências transitivas completas. Nomes e funções aprovados preservados.
2. Scanner padrão aplicado ao artefato exato antes de qualquer importação. DANGEROUS interrompe; CAUTION exige decisão humana explícita; ausência de achados não é certificação geral de segurança.
3. Pacote benigno passa; fixtures maliciosas continuam bloqueadas/sinalizadas. Payload perigoso nunca é executado para testar o scanner.
4. Instalação nativa primeiro em HOME/HERMES_HOME descartáveis, sem credenciais, com `--no-enable` e SHA completo. Metadados e destino lidos de volta.
5. Doctor do pacote instalado, verificador revisado e carga em processo/sessão nova de `graph-powers:planning`, `graph-powers:plan` e `graph-powers:agent-explorer`. Provar referências reais; não aceitar source checkout no lugar do pacote instalado.
6. Mesmo nome de plugin em dois perfis sintéticos não mistura caminhos, registries, módulos/cache ou configurações. `register()` não muda permissões nem configuração do host. Perfis operacionais permanecem intocados sem autorização específica.
7. Hooks Graph Powers continuam declarados `NOT ENFORCED`; SKIPPED/UNVERIFIED não contam como comprovação de runtime.

Gates existentes identificados em G: `bun hermes/install.mjs --check`; `python3 -X utf8 .github/test_hermes.py`; `python3 .github/test_file_references.py`; `python3 .github/check_file_references.py`; `python3 .github/check_portability.py`. A CI os referencia em `.github/workflows/ci.yml:80-83,192-194,221-224`. Se conteúdo compartilhado ou guardrails mudar, revisar e executar também `python3 hooks/test_hooks.py` em sandbox autorizado.

Para H, o runner prescrito pelo repositório é `scripts/run_tests.sh`. As suítes identificadas incluem `tests/tools/test_plugin_guard.py` e `tests/hermes_cli/test_plugins_cmd.py`. Alguns testes criam repositórios e commits de fixture; essa execução precisa de autorização restrita ao sandbox e nunca concede autorização de commit no projeto real.

Rollback futuro: desfazer somente o diff aprovado e preservar trabalho alheio. Para instalação autorizada, usar remoção nativa e restauração restrita do pacote/config/metadata do alvo, comparando com backup e mudanças concorrentes. Não restaurar todos os perfis por causa de uma falha isolada. Restart de gateway, instalação real, commit, push, PR e deploy exigem autorização específica.

## Comandos, resultados e limitações desta inspeção

| Ação efetivamente executada | Resultado |
|---|---|
| Leitura do receipt da tentativa anterior `hermes plugins install GrupoUS/graph-powers --ref b24f390a24c9229d24c17924e165ba6fd1512928 --no-enable` | O receipt preserva exit 1 e DANGEROUS/518. A instalação não foi repetida. |
| `git -C <HERMES_HOME>/hermes-agent rev-parse HEAD` | Exit 0, revisão H indicada acima. |
| `git -C <HERMES_HOME>/hermes-agent status --short` | Exit 0 e saída vazia nos dois checks. |
| GETs `curl -fsSL --max-time 25 https://raw.githubusercontent.com/GrupoUS/graph-powers/<SHA>/<arquivo>` | Exit 0 para as fontes usadas; downloads tratados como texto, sem execução. |
| GET da árvore GitHub `/repos/GrupoUS/graph-powers/git/trees/<SHA>?recursive=1` | Exit 0; `truncated: false`; localizou os caminhos corretos de testes e adaptador. |
| Python 3, `ast.literal_eval` do receipt + contagem por regex | Exit 0; 518 registros, severidades/categorias reconciliadas; entrypoint com dois LOW. |
| Python 3, comparação de bytes de config e existência de destinos/metadata | Exit 0; os sete perfis corresponderam à baseline descrita acima. Nenhum valor de configuração foi exposto. |
| Validação estrutural do prompt e auditoria editorial | Exit 0: `PASS tier=complex lines=96/250`; auditoria estrita do relatório, prompt e prosa extraída: `files=3 errors=0 warnings=0 ok=true`. O registro `RESULTADOS.md` pertence aos artefatos locais da inspeção original e não está incluído neste repositório. |

Ocorrências de pesquisa: duas URLs inicialmente presumidas retornaram HTTP 404 (`https://raw.githubusercontent.com/GrupoUS/graph-powers/b24f390a24c9229d24c17924e165ba6fd1512928/.github/check_hermes.py` e `https://raw.githubusercontent.com/GrupoUS/graph-powers/b24f390a24c9229d24c17924e165ba6fd1512928/hermes/skills/doctor/SKILL.md`). A árvore pinada revelou `.github/test_hermes.py` e `hermes/skills/graph-engineering/SKILL.md`. Uma leitura da CI falhou com erro TLS/exit 35 e passou no retry. Uma busca local retornou `Operation not permitted`; a busca mais específica passou. Nenhum desses erros foi apresentado como evidência de código ausente ou falha do plugin.

Limites: não houve nova execução do scanner, dos testes do plugin, do Doctor ou de carga nativa. A análise não auditou todas as dependências/scripts, não mediu compatibilidade em outros sistemas e não validou um pacote corrigido, que ainda não existe nesta entrega. O bloqueador operacional permanece o veredito perigoso da revisão analisada. O próximo passo autorizado pelo prompt é produzir/revisar o plano, não realizar a instalação.
