# CLAUDE.md

Este arquivo orienta o Claude Code (claude.ai/code) ao trabalhar com o código deste repositório.

## Visao Geral

Automacao para analise e desativacao de usuarios inativos no **SAP Analytics Cloud (SAC)**. Extrai usuarios (SCIM API) e o log de atividades (Activity Export API) direto do tenant, identifica quem esta sem acesso ha mais de `DIAS_INATIVIDADE` dias (padrao 30), gera relatorios (CSV/Excel), envia um email HTML com o resumo e o resultado por usuario e, opcionalmente, desativa via API SCIM. Roda toda sexta as 10h como servico Windows (NSSM) via `service.py`.

## Como Executar

```bash
pip install -r requirements.txt
python main.py
```

**Pre-requisitos:** arquivo `.env` na raiz com `CLIENT_ID`, `CLIENT_SECRET`, `OAUTH_TOKEN_URL`, `TENANT_URL` e, para email, `EMAIL_SMTP_HOST`, `EMAIL_SMTP_PORT`, `EMAIL_FROM`, `EMAIL_DESTINATARIOS`. Nao ha testes automatizados; para validar sem tocar na API, simule `get_token`, `buscar_todos_usuarios`, `exportar_atividades`, `desativar_usuario` e `smtplib.SMTP` e chame `main.main()`.

## Arquitetura

- **`main.py`** — Ponto de entrada. `executar()` faz o fluxo completo; `main()` envolve tudo em try/except, envia email de erro se algo falhar e retorna o exit code (0 ok, 1 erro fatal, 2 concluiu com falhas de desativacao).
- **`config.py`** — Toda a configuracao: URLs, regra de inatividade (`DIAS_INATIVIDADE`, `DIAS_CARENCIA_USUARIO_NOVO`), colunas, caminhos de saida (sempre na pasta do projeto), `USERS_PROTEGIDOS`, `DESATIVAR`, `DESATIVAR_APENAS_UM` e email.
- **`sac_utils.py`** — Integracao com a API do SAC: token OAuth, CSRF, paginacao SCIM, export de atividades e `desativar_usuario` (retorna `(status, mensagem)`, nunca lanca excecao).
- **`export_utils.py`** — `preparar_df_saida` monta o DataFrame final (mesmas colunas para CSV, Excel e email) e `exportar_relatorios` grava CSV + Excel (abas Inativos e Protegidos).
- **`email_utils.py`** — `enviar_email` (SMTP) e os montadores de HTML `montar_email_relatorio` / `montar_email_erro`.
- **`service.py`** — Loop com `schedule` que roda `main.py` em subprocesso toda sexta 10h (forca UTF-8 no filho). `python service.py --agora` executa imediatamente.

## Regras de classificacao (main.executar)

Cada usuario habilitado recebe um STATUS: `ativo` (atividade >= data de corte), `protegido` (inativo mas em `USERS_PROTEGIDOS`), `novo` (inativo mas criado ha menos de `DIAS_CARENCIA_USUARIO_NOVO` dias) ou `inativo` (passivel de desativacao). So `inativo` e desativado. A desativacao usa o `id` SCIM direto (coluna `USER_NAME`), sem busca por email.

## Configuracoes Importantes (config.py)

- `DESATIVAR = True/False` — Chave mestra da desativacao real via API.
- `DESATIVAR_APENAS_UM = True/False` — Desativa apenas o primeiro usuario (teste).
- `USERS_PROTEGIDOS` — userNames ou emails que nunca serao desativados.
- Prints no console devem ficar em ASCII (sem acentos/emojis): o servico roda com stdout em pipe no Windows.

## Fluxo da API

1. Grant client_credentials OAuth → access token
2. GET `/api/v1/csrf` → token CSRF + cookies
3. GET `/api/v1/scim/Users` (paginado) → usuarios
4. POST `/api/v1/audit/activities/exportActivities` (paginado, CSV) → atividades
5. Desativacao: GET `/api/v1/scim/Users/{id}` → `active: false` → PUT (CSRF + cookies)
