# SAC User Automation

Automacao para identificar, gerar relatorios e desativar usuarios inativos no **SAP Analytics Cloud (SAC)**.

Extrai dados diretamente via API (SCIM + Activity Log), identifica usuarios sem acesso nos ultimos 30 dias, gera relatorios em CSV e Excel, envia por email e opcionalmente desativa os usuarios via API SCIM.

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

Na raiz do projeto, crie um arquivo chamado `.env` com suas credenciais OAuth do SAC:

```
CLIENT_ID=seu_client_id_aqui
CLIENT_SECRET=seu_client_secret_aqui
```

> Essas credenciais sao obtidas no SAP BTP Cockpit, no service key do XSUAA vinculado ao SAC.

### 4. Configurar o `config.py`

Abra o arquivo `config.py` e ajuste conforme necessario:

**URLs do tenant** (altere para o seu tenant SAC):
```python
OAUTH_TOKEN_URL = "https://SEU_TENANT.authentication.br10.hana.ondemand.com/oauth/token/alias/SEU_TENANT.cf-br10"
TENANT_URL = "https://SEU_TENANT.br10.hcs.cloud.sap"
```

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

**Destinatarios do email**:
```python
EMAIL_SMTP_HOST = "smtp.seuservidor.com.br"
EMAIL_SMTP_PORT = 25
EMAIL_FROM = "bi@seuservidor.com.br"
EMAIL_DESTINATARIOS = [
    "seu.email@empresa.com",
    # Adicione outros destinatarios aqui
]
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
4. **Identifica inativos** - usuarios sem acesso nos ultimos 30 dias
5. **Aplica protecao** - remove da lista os usuarios definidos em `USERS_PROTEGIDOS`
6. **Gera relatorios**:
   - `usuarios_inativos_para_desativar.csv`
   - `usuarios_inativos_para_desativar.xlsx`
   - Ambos incluem: usuario, nome, email, ultimo acesso, dias sem acesso e empresa
7. **Envia email** com resumo e relatorios em anexo
8. **Desativa usuarios** via API SCIM (se `DESATIVAR = True`)

---

## Estrutura do projeto

```
├── main.py                    # Script principal - orquestra todo o fluxo
├── service.py                 # Wrapper para rodar como servico Windows (NSSM)
├── config.py                  # Configuracoes: URLs, credenciais, usuarios protegidos, email
├── sac_utils.py               # Funcoes de integracao com as APIs do SAC (SCIM, CSRF, Activities)
├── export_utils.py            # Geracao do relatorio Excel
├── email_utils.py             # Envio de email com anexos via SMTP
├── requirements.txt           # Dependencias Python
├── agendar_tarefa.bat         # Agendamento via Windows Task Scheduler
├── instalar_servico_nssm.bat  # Instalacao como servico via NSSM
├── .env                       # Credenciais OAuth (nao versionado)
├── testes/                    # Scripts de teste e validacao
└── final/                     # Versoes anteriores do script
```

---

## Agendamento automatico (Windows)

Existem duas opcoes para agendar a execucao toda sexta-feira as 10h:

### Opcao 1: NSSM (recomendado)

Instala como servico Windows usando o [NSSM](https://nssm.cc/). O servico fica rodando em segundo plano e executa o script no horario agendado. Reinicia automaticamente com o Windows.

**Instalacao:**

1. Baixe o NSSM em [nssm.cc/download](https://nssm.cc/download) e coloque o `nssm.exe` no PATH do sistema
2. Clique com botao direito em `instalar_servico_nssm.bat` > **Executar como administrador**

**Comandos uteis:**

```bash
nssm status SAC_Usuarios_Inativos      # ver status do servico
nssm restart SAC_Usuarios_Inativos     # reiniciar
nssm stop SAC_Usuarios_Inativos        # parar
nssm remove SAC_Usuarios_Inativos      # remover servico
```

**Logs:** o servico grava logs em `service.log` na raiz do projeto (rotacao automatica em 5MB).

### Opcao 2: Windows Task Scheduler

Cria uma tarefa agendada que executa o script diretamente. Mais simples, mas depende do usuario estar logado.

1. Clique com botao direito em `agendar_tarefa.bat` > **Executar como administrador**

Para verificar ou editar:
- Abra o **Agendador de Tarefas** (`taskschd.msc`) e procure por `SAC_Usuarios_Inativos`

Para remover:
```bash
schtasks /delete /tn "SAC_Usuarios_Inativos" /f
```

---

## Fluxo das APIs do SAC

```
1. POST /oauth/token (client_credentials) --> access_token
2. GET  /api/v1/scim/Users                --> lista de usuarios (paginado)
3. GET  /api/v1/csrf                      --> CSRF token + cookies
4. POST /api/v1/audit/activities/exportActivities --> log de atividades (paginado)
5. GET  /api/v1/scim/Users/{id}           --> objeto do usuario (para desativacao)
6. PUT  /api/v1/scim/Users/{id}           --> desativa usuario (active: false)
```

---

## Aviso importante

- **Revise os relatorios** antes de ativar `DESATIVAR = True`
- Teste primeiro com `DESATIVAR_APENAS_UM = True` para validar com um unico usuario
- Adicione usuarios criticos na lista `USERS_PROTEGIDOS`
- Nunca compartilhe o arquivo `.env` publicamente
