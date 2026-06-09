import os
from dotenv import load_dotenv


load_dotenv()  # Carrega variáveis do .env

PASTA_DOWNLOADS = os.path.join(os.path.expanduser("~"), "Downloads")
OAUTH_TOKEN_URL = os.getenv("OAUTH_TOKEN_URL")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TENANT_URL = os.getenv("TENANT_URL")
SAC_SCIM_API_URL = f"{TENANT_URL}/api/v1/scim/Users"
SAC_ACTIVITIES_URL = f"{TENANT_URL}/api/v1/audit/activities/exportActivities"
CSRF_URL = f"{TENANT_URL}/api/v1/csrf"

COL_USER_ID_USERS = "USER_NAME"
COL_USER_NAME = "DISPLAY_NAME"
COL_USER_EMAIL = "EMAIL"
COL_IS_DEACTIVATED = "IS_USER_DEACTIVATED"
COL_USER_ID_ATIVIDADE = "User Name"
COL_OBJECT_TYPE = "Object Type"
COL_TIMESTAMP = "Timestamp"

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
    "CAROLINA_LIMA"
    # Adicione outros aqui
]

DESATIVAR = True # Mudar para True para ativar a desativação
DESATIVAR_APENAS_UM = False # True só para testar um

# --- Configuracao de email ---
EMAIL_SMTP_HOST = os.getenv("EMAIL_SMTP_HOST", "")
EMAIL_SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT", "25"))
EMAIL_FROM = os.getenv("EMAIL_FROM", "")
EMAIL_DESTINATARIOS = [
    e.strip() for e in os.getenv("EMAIL_DESTINATARIOS", "").split(",") if e.strip()
]
