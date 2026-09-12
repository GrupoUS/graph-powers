## Implementação da issue 25

Implementação no checkout local, sem commit/push nesta issue.

- G4 coordena leases por sessão/run e caminhos; planos disjuntos podem trabalhar na mesma branch e no mesmo checkout.
- Escrita sobre caminho reservado por outro run vivo é negada com identificação do dono; caminhos livres e leitura continuam permitidos.
- SDD recebe identidade de sessão em aquisição, consulta, renovação, liberação e reserva de despachos. TTL de 45 minutos, renovação explícita e limpeza dos registros expirados.
- Aquisição verifica conflitos sob lock curto liberado pelo sistema operacional em caso de encerramento do processo.
- Migração do lease antigo preserva run e limites de despacho; progresso passa a ser por plano. A retomada mantém a revisão do Gauntlet.
- Documentação e distribuição gerada atualizadas para 1.20.8, preservando as alterações da issue 24.

### Validação

- `python3 skills/planning/scripts/test_sdd.py`: **71 testes, OK**.
- `python3 hooks/test_hooks.py`: **EVERY GUARANTEE HELD**.
- Regressões RED/GREEN para aquisição simultânea, conflitos, sessão/TTL, migração, processo interrompido, disputa dispatch/release e timestamps malformados.
- Pacote Hermes: **39 registros**, geração/check e provas estáticas aprovados.
- **27/28 grupos de verificações aprovados**. A falha restante é o limite de tamanho do checkout: `yaml.ps`, arquivo externo a esta issue com 12.221.795 bytes, excede o orçamento de source. Foi preservado. Não há declaração de checkout integralmente verde nem de versão publicada.
- A revisão independente identificou um P2 de overflow em timestamps; corrigido e aprovado na confirmação independente.
- **Revisão final: PASS/READY**, sem achados pendentes. Retomada em `/prime` e liberação final também preservam a identidade da sessão.

Plano e evidências no checkout: `docs/plans/2026-09-12-issue-25-session-leases/`.

### Limites

Leases são cooperativos: não isolam filhos da mesma sessão, não interceptam escrita via shell e não serializam o índice Git. Execução nativa em clientes instalados e Windows não foi verificada nesta tarefa. Nenhum worktree foi criado.
