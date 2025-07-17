import os
from dotenv import load_dotenv


load_dotenv()  # Carrega variáveis do .env

PASTA_DOWNLOADS = os.path.join(os.path.expanduser("~"), "Downloads")
OAUTH_TOKEN_URL = "https://refrescosbandeirantes.authentication.br10.hana.ondemand.com/oauth/token/alias/refrescosbandeirantes.cf-br10"
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TENANT_URL = "https://refrescosbandeirantes.br10.hcs.cloud.sap"
SAC_SCIM_API_URL = f"{TENANT_URL}/api/v1/scim/Users"
CSRF_URL = f"{TENANT_URL}/api/v1/csrf"

COL_USER_ID_USERS = "USER_NAME"
COL_USER_NAME = "DISPLAY_NAME"
COL_USER_EMAIL = "EMAIL"
COL_IS_DEACTIVATED = "IS_USER_DEACTIVATED"
COL_USER_ID_ATIVIDADE = "User Name"
COL_OBJECT_TYPE = "Object Type"
COL_TIMESTAMP = "Timestamp"

USERS_PROTEGIDOS = [
    "LUANARANTES",
    "DIEGO_OLIVEIRA",
    "LUCASGUIMARAES",
    "MARCOS_LOBO",
    "GERARDO_FILHO",
    # Adicione outros aqui
]

DESATIVAR = True
DESATIVAR_APENAS_UM = True  # True só para testar um
