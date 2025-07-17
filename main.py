import pandas as pd
import os
from config import *
from sac_utils import get_token, get_csrf_token, buscar_usuario_por_email, desativar_usuario
from export_utils import exportar_inativos_para_xlsx

def arquivo_mais_recente(pasta, prefixo):
    import glob
    arquivos = glob.glob(os.path.join(pasta, f"{prefixo}*.csv"))
    if not arquivos:
        raise FileNotFoundError(f"Nenhum arquivo com prefixo '{prefixo}' encontrado na pasta {pasta}")
    return max(arquivos, key=os.path.getmtime)

if not os.path.exists(PASTA_DOWNLOADS):
    print(f"Pasta {PASTA_DOWNLOADS} não encontrada. Criando agora...")
    os.makedirs(PASTA_DOWNLOADS)

USERS_CSV = arquivo_mais_recente(PASTA_DOWNLOADS, "user")
ATIVIDADE_CSV = arquivo_mais_recente(PASTA_DOWNLOADS, "atividade")

print(f"Lendo usuários de: {USERS_CSV}")
df_users = pd.read_csv(USERS_CSV)
if COL_IS_DEACTIVATED in df_users.columns:
    df_users = df_users[df_users[COL_IS_DEACTIVATED].isna()]

print(f"Lendo atividades de: {ATIVIDADE_CSV}")
df_atividade = pd.read_csv(ATIVIDADE_CSV, skiprows=1)
df_atividade.columns = [col.strip() for col in df_atividade.columns]
print("\nColunas de atividade:", df_atividade.columns.tolist())
if COL_OBJECT_TYPE not in df_atividade.columns:
    raise Exception(f"Coluna '{COL_OBJECT_TYPE}' não encontrada nas atividades! Corrija para o nome real.")
df_atividade = df_atividade[df_atividade[COL_OBJECT_TYPE] == "User"]

ultimas_atividades = df_atividade.groupby(COL_USER_ID_ATIVIDADE)[COL_TIMESTAMP].max().reset_index()
active_user_ids = set(ultimas_atividades[COL_USER_ID_ATIVIDADE].astype(str).unique())
df_inactive = df_users[~df_users[COL_USER_ID_USERS].astype(str).isin(active_user_ids)]

protegidos = set([u.lower() for u in USERS_PROTEGIDOS])
def eh_protegido(row):
    email = str(row.get(COL_USER_EMAIL, "")).lower()
    user_name = str(row.get(COL_USER_ID_USERS, "")).lower()
    return (email in protegidos) or (user_name in protegidos)
df_inactive['eh_protegido'] = df_inactive.apply(eh_protegido, axis=1)
df_inactive_ok = df_inactive[~df_inactive['eh_protegido']]

print(f"\nTotal de usuários ativos no CSV: {len(df_users)}")
print(f"Usuários ativos nos últimos 40 dias: {len(active_user_ids)}")
print(f"Usuários inativos há mais de 40 dias (antes do filtro de proteção): {len(df_inactive)}")
print(f"Usuários realmente passíveis de desativação: {len(df_inactive_ok)}\n")
print("Inativos (exceto protegidos):")
print(df_inactive_ok[[COL_USER_ID_USERS, COL_USER_NAME, COL_USER_EMAIL]])

df_inactive_ok.to_csv("usuarios_inativos_para_desativar.csv", index=False)
print("\nLista salva em usuarios_inativos_para_desativar.csv")

exportar_inativos_para_xlsx(
    caminho_csv_inativos="usuarios_inativos_para_desativar.csv",
    caminho_atividade_csv=ATIVIDADE_CSV,
    caminho_saida_xlsx="usuarios_inativos_para_desativar.xlsx"
)

if df_inactive['eh_protegido'].sum() > 0:
    print("\nUsuários protegidos (não serão desativados):")
    print(df_inactive[df_inactive['eh_protegido']][[COL_USER_ID_USERS, COL_USER_NAME, COL_USER_EMAIL]])

if DESATIVAR and len(df_inactive_ok) > 0:
    print("\nObtendo token e CSRF token...")
    token = get_token(OAUTH_TOKEN_URL, CLIENT_ID, CLIENT_SECRET)
    csrf_token, cookies = get_csrf_token(CSRF_URL, token)
    print("Desativando usuários inativos (exceto protegidos)...")
    lista_emails = df_inactive_ok[COL_USER_EMAIL].tolist()
    if DESATIVAR_APENAS_UM:
        lista_emails = lista_emails[:1]
    for email in lista_emails:
        print(f"\nBuscando usuário pelo email: {email}")
        user = buscar_usuario_por_email(SAC_SCIM_API_URL, token, email)
        if user:
            print("Usuário encontrado!")
            print("userName:", user.get("userName"))
            print("displayName:", user.get("displayName"))
            print("emails:", [e.get("value") for e in user.get("emails", [])])
            print("ID SCIM:", user.get("id"))
            print("Ativo:", user.get("active"))
            if user.get("active", True):
                print(f"Desativando usuário: {user.get('id')} ...")
                desativar_usuario(SAC_SCIM_API_URL, token, user.get("id"), csrf_token, cookies)
            else:
                print("Usuário já está desativado.")
        else:
            print("Nenhum usuário com esse email encontrado.")
    print("\nTodos os inativos processados!")
else:
    print("\nModo seguro ativado ou nenhum usuário a desativar. Nenhum usuário foi desativado.")
