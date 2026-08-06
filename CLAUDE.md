# CLAUDE.md

Este arquivo orienta o Claude Code (claude.ai/code) ao trabalhar com o código deste repositório.

## Visao Geral

Ferramenta de automacao para analise e desativacao de usuarios inativos no **SAP Analytics Cloud (SAC)**. Le arquivos CSV exportados (usuarios + logs de atividade) da pasta Downloads do usuario, identifica quem esta inativo ha mais de 40 dias, gera relatorios (CSV/Excel) e, opcionalmente, desativa via API SCIM do SAC.

## Como Executar

```bash
pip install -r requirements.txt
python main.py
```

**Pre-requisitos:** Colocar os arquivos `user*.csv` e `atividade*.csv` exportados do SAC na pasta `~/Downloads`. Criar um arquivo `.env` na raiz com `CLIENT_ID` e `CLIENT_SECRET` do OAuth do SAC.

## Arquitetura

- **`main.py`** — Ponto de entrada. Localiza os CSVs mais recentes de usuarios e atividades, filtra inativos, aplica a lista de usuarios protegidos, exporta resultados e dispara a desativacao via SCIM.
- **`config.py`** — Toda a configuracao: URLs OAuth, URL do tenant SAC, mapeamento de colunas dos CSVs, lista de usuarios protegidos (`USERS_PROTEGIDOS`) e flags de desativacao (`DESATIVAR`, `DESATIVAR_APENAS_UM`).
- **`sac_utils.py`** — Integracao com a API do SAC: obtencao de token OAuth, busca de token CSRF, busca de usuario por email via SCIM (paginada) e desativacao via PUT.
- **`export_utils.py`** — Geracao de relatorio Excel. Cruza usuarios inativos com timestamps de ultimo acesso, calcula dias sem acesso e mapeia dominios de email para nomes de empresa.

## Configuracoes Importantes (config.py)

- `DESATIVAR = True/False` — Chave mestra para ativar/desativar a desativacao real via API.
- `DESATIVAR_APENAS_UM = True/False` — Flag de seguranca para desativar apenas o primeiro usuario (para testes).
- `USERS_PROTEGIDOS` — Lista de usernames que nunca serao desativados.
- Constantes de colunas dos CSVs (`COL_USER_ID_USERS`, `COL_TIMESTAMP`, etc.) devem corresponder exatamente aos cabecalhos dos arquivos exportados.

## Fluxo da API

1. Grant client_credentials OAuth → access token
2. Busca token CSRF em `/api/v1/csrf`
3. Busca usuario por email via SCIM (`/api/v1/scim/Users`) com paginacao
4. Desativacao: GET do objeto do usuario → seta `active: false` → PUT de volta (com token CSRF + cookies)
