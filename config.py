import os
from dotenv import load_dotenv


# Pasta do projeto: .env e relatorios ficam aqui, independente de onde o script foi chamado
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# --- Conexao com o SAC (valores sensiveis vem do .env) ---
OAUTH_TOKEN_URL = os.getenv("OAUTH_TOKEN_URL")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TENANT_URL = (os.getenv("TENANT_URL") or "").rstrip("/")
SAC_SCIM_API_URL = f"{TENANT_URL}/api/v1/scim/Users"
SAC_ACTIVITIES_URL = f"{TENANT_URL}/api/v1/audit/activities/exportActivities"
CSRF_URL = f"{TENANT_URL}/api/v1/csrf"

# Timeout (segundos) de cada chamada HTTP ao SAC
HTTP_TIMEOUT = 120

# --- Regra de inatividade ---
# Usuario sem nenhuma atividade registrada nesse periodo e considerado inativo.
DIAS_INATIVIDADE = 30
# Usuarios criados ha menos dias que isso nunca sao considerados inativos,
# mesmo sem acesso (periodo de carencia para contas novas).
DIAS_CARENCIA_USUARIO_NOVO = DIAS_INATIVIDADE

# --- Nomes das colunas internas (DataFrames) ---
COL_USER_ID_USERS = "USER_NAME"
COL_USER_NAME = "DISPLAY_NAME"
COL_USER_EMAIL = "EMAIL"
COL_IS_DEACTIVATED = "IS_USER_DEACTIVATED"
COL_USER_CREATED = "CRIADO_EM"
COL_USER_ID_ATIVIDADE = "User Name"
COL_OBJECT_TYPE = "Object Type"
COL_TIMESTAMP = "Timestamp"
FORMATO_TIMESTAMP_ATIVIDADE = "%Y.%m.%d %H:%M:%S"

# --- Arquivos de saida (gerados na pasta do projeto) ---
ARQUIVO_SAIDA_BASE = "usuarios_inativos_para_desativar"
ARQUIVO_SAIDA_CSV = os.path.join(BASE_DIR, f"{ARQUIVO_SAIDA_BASE}.csv")
ARQUIVO_SAIDA_XLSX = os.path.join(BASE_DIR, f"{ARQUIVO_SAIDA_BASE}.xlsx")

# Usuarios (userName ou email) que NUNCA serao desativados
USERS_PROTEGIDOS = [
    "SAPSUPPORT",
    "LUANARANTES",
    "DIEGO_OLIVEIRA",
    "LUCASGUIMARAES",
    "MARCOS_LOBO",
    "GERARDO_FILHO",
    "JOHN",
    "BND_ANA_PAULA",
    "LUCIANO_BELLUZO",
    "HD_HENRIQUE_GONZAGA",
    "ALFA_NELSON",
    "HELDER_ADORNO",
    "CAROLINA_LIMA",
    # Adicione outros aqui
]

DESATIVAR = True  # True = desativa via API / False = apenas gera relatorio
DESATIVAR_APENAS_UM = False  # True = desativa so o primeiro da lista (teste)

# --- Configuracao de email ---
EMAIL_SMTP_HOST = os.getenv("EMAIL_SMTP_HOST", "")
EMAIL_SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT", "25"))
EMAIL_FROM = os.getenv("EMAIL_FROM", "")
EMAIL_DESTINATARIOS = [
    e.strip() for e in os.getenv("EMAIL_DESTINATARIOS", "").split(",") if e.strip()
]
# Quantidade maxima de usuarios listados no corpo do email (o restante fica nos anexos)
EMAIL_MAX_LINHAS_TABELA = 60
