# SAC User Automation

Automacao para identificar, gerar relatorios e desativar usuarios inativos no **SAP Analytics Cloud (SAC)**.

Extrai dados diretamente via API (SCIM + Activity Log), identifica usuarios sem acesso nos ultimos 30 dias (configuravel em `DIAS_INATIVIDADE`), gera relatorios em CSV e Excel, envia por email um resumo com o resultado de cada usuario e opcionalmente desativa os usuarios via API SCIM. Se a execucao falhar, um email de erro e enviado com o motivo.

---

## Pre-requisitos

- **Python 3.9+** instalado ([python.org/downloads](https://www.python.org/downloads/))
- **Credenciais OAuth** do SAC (Client ID e Client Secret) com permissao para SCIM API e Activity Log API
- Acesso ao servidor SMTP para envio de email (caso queira receber os relatorios)

---

## Passo a passo - Configuracao inicial

### 1. Clonar o repositorio

```bash
git clone https://github.com/LuanAlves2/SAP-Analytics-Cloud-User-Inactivity-Automation.git
cd SAP-Analytics-Cloud-User-Inactivity-Automation
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

Dependencias: `pandas`, `requests`, `python-dotenv`, `openpyxl`, `schedule`

### 3. Criar o arquivo `.env`

Na raiz do projeto, crie um arquivo chamado `.env` com todas as configuracoes sensiveis:

```
CLIENT_ID=seu_client_id_aqui
CLIENT_SECRET=seu_client_secret_aqui
OAUTH_TOKEN_URL=https://SEU_TENANT.authentication.br10.hana.ondemand.com/oauth/token/alias/SEU_TENANT.cf-br10
TENANT_URL=https://SEU_TENANT.br10.hcs.cloud.sap
EMAIL_SMTP_HOST=smtp.seuservidor.com.br
EMAIL_SMTP_PORT=25
EMAIL_FROM=bi@seuservidor.com.br
EMAIL_DESTINATARIOS=email1@empresa.com,email2@empresa.com,email3@empresa.com
```

> As credenciais OAuth sao obtidas no SAP BTP Cockpit, no service key do XSUAA vinculado ao SAC.

### 4. Configurar o `config.py`

Abra o arquivo `config.py` e ajuste:

**Usuarios protegidos** (nunca serao desativados):
```python
USERS_PROTEGIDOS = [
    "LUANARANTES",
    "MARCOS_LOBO",
    # Adicione outros aqui
]
```

**Flags de desativacao**:
```python
DESATIVAR = False        # True = desativa usuarios via API / False = apenas gera relatorio
DESATIVAR_APENAS_UM = False  # True = desativa apenas o primeiro (para teste)
```

**Regra de inatividade**:
```python
DIAS_INATIVIDADE = 30             # sem atividade ha mais de N dias = inativo
DIAS_CARENCIA_USUARIO_NOVO = 30   # contas criadas ha menos de N dias nunca sao desativadas
```

### 5. Executar

```bash
python main.py
```

---

## O que o script faz

1. **Autentica** no SAC via OAuth (client_credentials)
2. **Extrai todos os usuarios** via SCIM API (`/api/v1/scim/Users`)
3. **Extrai o log de atividades** via Activity Export API (`/api/v1/audit/activities/exportActivities`)
4. **Classifica cada usuario habilitado**:
   - `ativo` — teve atividade nos ultimos `DIAS_INATIVIDADE` dias
   - `protegido` — inativo, mas esta em `USERS_PROTEGIDOS` (nunca desativado)
   - `novo` — inativo, mas a conta foi criada ha menos de `DIAS_CARENCIA_USUARIO_NOVO` dias (ignorado)
   - `inativo` — passivel de desativacao
5. **Desativa usuarios** `inativo` via API SCIM (se `DESATIVAR = True`), registrando o resultado de cada um
6. **Gera relatorios** na pasta do projeto:
   - `usuarios_inativos_para_desativar.csv`
   - `usuarios_inativos_para_desativar.xlsx` (aba *Inativos* + aba *Protegidos*)
   - Colunas: usuario, nome, email, empresa, ultimo acesso, dias sem acesso, licenca e resultado da desativacao
7. **Envia email** com resumo (frase em linguagem simples, status da execucao, metricas, tabela de usuarios com o resultado, observacoes sobre protegidos/contas novas e explicacao do criterio) e relatorios em anexo
8. **Em caso de erro fatal**, envia um email de falha indicando a etapa e o erro, e encerra com exit code 1 (exit code 2 = concluiu mas alguma desativacao falhou)

---

## Estrutura do projeto

```
├── main.py                    # Script principal — orquestra todo o fluxo
├── service.py                 # Wrapper para rodar como servico Windows (NSSM)
├── config.py                  # Configuracoes: usuarios protegidos, flags, colunas CSV
├── sac_utils.py               # Integracao com as APIs do SAC (SCIM, CSRF, Activities)
├── export_utils.py            # Geracao do relatorio Excel
├── email_utils.py             # Envio de email com anexos via SMTP
├── requirements.txt           # Dependencias Python
├── agendar_tarefa.bat         # Agendamento via Windows Task Scheduler
├── instalar_servico_nssm.bat  # Instalacao como servico via NSSM
├── .env                       # Credenciais e configuracoes sensiveis (nao versionado)
├── testes/                    # Scripts de teste e validacao
└── final/                     # Versoes anteriores do script
```

---

## Configuracao do `.env`

Todas as configuracoes sensiveis ficam no `.env` (nao versionado no git):

| Variavel | Descricao |
|----------|-----------|
| `CLIENT_ID` | Client ID do XSUAA (SAP BTP) |
| `CLIENT_SECRET` | Client Secret do XSUAA |
| `OAUTH_TOKEN_URL` | URL do endpoint OAuth do tenant |
| `TENANT_URL` | URL base do tenant SAC |
| `EMAIL_SMTP_HOST` | Servidor SMTP para envio de email |
| `EMAIL_SMTP_PORT` | Porta do SMTP (padrao: 25) |
| `EMAIL_FROM` | Email remetente |
| `EMAIL_DESTINATARIOS` | Lista de destinatarios separados por virgula |

---

## Agendamento automatico (Windows)

Existem duas opcoes para agendar a execucao toda sexta-feira as 10h:

### Opcao 1: NSSM (recomendado)

Instala como servico Windows usando o [NSSM](https://nssm.cc/). O servico fica rodando em segundo plano e executa o script no horario agendado. Reinicia automaticamente com o Windows.

**Instalacao:**

1. Baixe o NSSM em [nssm.cc/download](https://nssm.cc/download)
2. Edite o `instalar_servico_nssm.bat` com os caminhos corretos do Python e do projeto no servidor
3. Execute como administrador

**Comandos uteis:**

```bash
nssm status SAC_Usuarios_Inativos      # ver status do servico
nssm restart SAC_Usuarios_Inativos     # reiniciar
nssm stop SAC_Usuarios_Inativos        # parar
nssm remove SAC_Usuarios_Inativos      # remover servico
```

**Logs:** o servico grava logs em `service.log` na raiz do projeto (rotacao automatica em 5MB).

**Teste rapido:** `python service.py --agora` executa o `main.py` imediatamente e depois segue agendado.

**Nota para Python embeddable:** Se usar a versao embeddable do Python no servidor, edite o arquivo `python3XX._pth` e adicione o caminho completo do projeto para que os modulos sejam encontrados.

### Opcao 2: Windows Task Scheduler

Cria uma tarefa agendada que executa o script diretamente. Mais simples, mas depende do usuario estar logado.

1. Clique com botao direito em `agendar_tarefa.bat` > **Executar como administrador** (usa a pasta do projeto e o `python` do PATH automaticamente)

Para verificar ou editar:
- Abra o **Agendador de Tarefas** (`taskschd.msc`) e procure por `SAC_Usuarios_Inativos`

Para remover:
```bash
schtasks /delete /tn "SAC_Usuarios_Inativos" /f
```

---

## Fluxo das APIs do SAC

```
1. POST /oauth/token (client_credentials)            --> access_token
2. GET  /api/v1/scim/Users                           --> lista de usuarios (paginado)
3. GET  /api/v1/csrf                                 --> CSRF token + cookies
4. POST /api/v1/audit/activities/exportActivities     --> log de atividades (paginado)
5. GET  /api/v1/scim/Users/{id}                      --> objeto do usuario (para desativacao)
6. PUT  /api/v1/scim/Users/{id}                      --> desativa usuario (active: false)
```

---

## Aviso importante

- **Revise os relatorios** antes de ativar `DESATIVAR = True`
- Teste primeiro com `DESATIVAR_APENAS_UM = True` para validar com um unico usuario
- Adicione usuarios criticos na lista `USERS_PROTEGIDOS`
- Nunca compartilhe o arquivo `.env` publicamente
