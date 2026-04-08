import pandas as pd
import os
from datetime import datetime, timedelta
from config import *
from sac_utils import (
    get_token, get_csrf_token,
    buscar_usuario_por_email, desativar_usuario,
    buscar_todos_usuarios, exportar_atividades,
)
from export_utils import exportar_inativos_para_xlsx
from email_utils import enviar_relatorio

# --- Obter token para extrair dados via API ---
print("Obtendo token OAuth...")
token = get_token(OAUTH_TOKEN_URL, CLIENT_ID, CLIENT_SECRET)

# --- Extrair usuarios via SCIM API ---
print("\nExtraindo usuarios via SCIM API...")
df_users = buscar_todos_usuarios(SAC_SCIM_API_URL, token)
if COL_IS_DEACTIVATED in df_users.columns:
    df_users = df_users[df_users[COL_IS_DEACTIVATED].isna() | (df_users[COL_IS_DEACTIVATED] == "")]

# --- Extrair TODAS as atividades via API (para calcular dias sem acesso) ---
print("\nExtraindo todas as atividades via API...")
df_atividade_full = exportar_atividades(SAC_ACTIVITIES_URL, token, CSRF_URL)

print("\nColunas de atividade:", df_atividade_full.columns.tolist())
if COL_OBJECT_TYPE not in df_atividade_full.columns:
    raise Exception(f"Coluna '{COL_OBJECT_TYPE}' nao encontrada nas atividades! Colunas disponiveis: {df_atividade_full.columns.tolist()}")
df_atividade_full = df_atividade_full[df_atividade_full[COL_OBJECT_TYPE] == "User"]

# --- Filtrar usuarios ativos nos ultimos 30 dias ---
data_30_dias = (datetime.now() - timedelta(days=30)).strftime("%Y.%m.%d %H:%M:%S")
df_atividade_recente = df_atividade_full[df_atividade_full[COL_TIMESTAMP] >= data_30_dias]

ultimas_atividades = df_atividade_recente.groupby(COL_USER_ID_ATIVIDADE)[COL_TIMESTAMP].max().reset_index()
active_user_ids = set(ultimas_atividades[COL_USER_ID_ATIVIDADE].astype(str).unique())
df_inactive = df_users[~df_users[COL_USER_ID_USERS].astype(str).isin(active_user_ids)]

protegidos = set([u.lower() for u in USERS_PROTEGIDOS])
def eh_protegido(row):
    email = str(row.get(COL_USER_EMAIL, "")).lower()
    user_name = str(row.get(COL_USER_ID_USERS, "")).lower()
    return (email in protegidos) or (user_name in protegidos)
df_inactive = df_inactive.copy()
df_inactive['eh_protegido'] = df_inactive.apply(eh_protegido, axis=1)
df_inactive_ok = df_inactive[~df_inactive['eh_protegido']]

print(f"\nTotal de usuarios ativos no SAC: {len(df_users)}")
print(f"Usuarios ativos nos ultimos 30 dias: {len(active_user_ids)}")
print(f"Usuarios inativos ha mais de 30 dias (antes do filtro de protecao): {len(df_inactive)}")
print(f"Usuarios realmente passiveis de desativacao: {len(df_inactive_ok)}\n")
print("Inativos (exceto protegidos):")
print(df_inactive_ok[[COL_USER_ID_USERS, COL_USER_NAME, COL_USER_EMAIL]])

# Adicionar ultimo acesso e dias sem acesso ao CSV
df_atividade_user = df_atividade_full[df_atividade_full[COL_OBJECT_TYPE] == "User"]
ultimos_acessos_full = (
    df_atividade_user.groupby(COL_USER_ID_ATIVIDADE)[COL_TIMESTAMP].max()
    .reset_index()
    .rename(columns={COL_TIMESTAMP: "ULTIMO_ACESSO"})
)
df_inactive_ok = df_inactive_ok.copy()
df_inactive_ok = df_inactive_ok.merge(
    ultimos_acessos_full, left_on=COL_USER_ID_USERS, right_on=COL_USER_ID_ATIVIDADE, how="left"
)
if COL_USER_ID_ATIVIDADE in df_inactive_ok.columns and COL_USER_ID_ATIVIDADE != COL_USER_ID_USERS:
    df_inactive_ok.drop(columns=[COL_USER_ID_ATIVIDADE], inplace=True)

hoje = datetime.now()
def calcular_dias_csv(dt_str):
    if pd.isna(dt_str) or dt_str == "":
        return "NUNCA ACESSOU"
    try:
        dt = datetime.strptime(str(dt_str).strip(), "%Y.%m.%d %H:%M:%S")
        return (hoje - dt).days
    except Exception:
        return "NUNCA ACESSOU"

def formatar_acesso_csv(dt_str):
    if pd.isna(dt_str) or dt_str == "":
        return "NUNCA ACESSOU"
    try:
        dt = datetime.strptime(str(dt_str).strip(), "%Y.%m.%d %H:%M:%S")
        return dt.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return "NUNCA ACESSOU"

df_inactive_ok["DIAS_SEM_ACESSO"] = df_inactive_ok["ULTIMO_ACESSO"].apply(calcular_dias_csv)
df_inactive_ok["ULTIMO_ACESSO"] = df_inactive_ok["ULTIMO_ACESSO"].apply(formatar_acesso_csv)

df_inactive_ok.to_csv("usuarios_inativos_para_desativar.csv", index=False)
print("\nLista salva em usuarios_inativos_para_desativar.csv")

exportar_inativos_para_xlsx(
    df_inativos=df_inactive_ok,
    caminho_saida_xlsx="usuarios_inativos_para_desativar.xlsx"
)

if df_inactive['eh_protegido'].sum() > 0:
    print("\nUsuarios protegidos (nao serao desativados):")
    print(df_inactive[df_inactive['eh_protegido']][[COL_USER_ID_USERS, COL_USER_NAME, COL_USER_EMAIL]])

if DESATIVAR and len(df_inactive_ok) > 0:
    print("\nObtendo CSRF token para desativacao...")
    csrf_token, cookies = get_csrf_token(CSRF_URL, token)
    print("Desativando usuarios inativos (exceto protegidos)...")
    lista_emails = df_inactive_ok[COL_USER_EMAIL].tolist()
    if DESATIVAR_APENAS_UM:
        lista_emails = lista_emails[:1]
    for email in lista_emails:
        print(f"\nBuscando usuario pelo email: {email}")
        user = buscar_usuario_por_email(SAC_SCIM_API_URL, token, email)
        if user:
            print("Usuario encontrado!")
            print("userName:", user.get("userName"))
            print("displayName:", user.get("displayName"))
            print("emails:", [e.get("value") for e in user.get("emails", [])])
            print("ID SCIM:", user.get("id"))
            print("Ativo:", user.get("active"))
            if user.get("active", True):
                print(f"Desativando usuario: {user.get('id')} ...")
                desativar_usuario(SAC_SCIM_API_URL, token, user.get("id"), csrf_token, cookies)
            else:
                print("Usuario ja esta desativado.")
        else:
            print("Nenhum usuario com esse email encontrado.")
    print("\nTodos os inativos processados!")
else:
    print("\nModo seguro ativado ou nenhum usuario a desativar. Nenhum usuario foi desativado.")

# --- Envio de email com relatorio ---
if EMAIL_DESTINATARIOS:
    data_hoje = datetime.now().strftime("%d/%m/%Y")
    total_users = len(df_users)
    total_ativos = len(active_user_ids)
    total_inativos = len(df_inactive_ok)
    pct_inativos = round((total_inativos / total_users * 100), 1) if total_users > 0 else 0
    status_desativacao = "Desativacao executada" if DESATIVAR else "Apenas relatorio (modo seguro)"

    assunto = f"[SAC] {total_inativos} usuarios inativos identificados - {data_hoje}"
    corpo = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
    </head>
    <body style="margin:0; padding:0; background-color:#f4f6f9; font-family: 'Segoe UI', Arial, sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f6f9; padding:30px 0;">
            <tr>
                <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" style="background-color:#ffffff; border-radius:8px; overflow:hidden; box-shadow:0 2px 8px rgba(0,0,0,0.08);">

                        <!-- Header -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #0a1628 0%, #1a3a5c 100%); padding:30px 40px; text-align:center;">
                                <h1 style="color:#ffffff; margin:0; font-size:22px; font-weight:600; letter-spacing:0.5px;">
                                    SAP Analytics Cloud
                                </h1>
                                <p style="color:#7eb8e0; margin:6px 0 0; font-size:14px;">
                                    Relatorio de Usuarios Inativos
                                </p>
                            </td>
                        </tr>

                        <!-- Data -->
                        <tr>
                            <td style="padding:24px 40px 0;">
                                <p style="color:#6b7280; font-size:13px; margin:0;">
                                    Gerado em <strong style="color:#374151;">{data_hoje}</strong>
                                </p>
                            </td>
                        </tr>

                        <!-- Cards de metricas -->
                        <tr>
                            <td style="padding:20px 40px;">
                                <table width="100%" cellpadding="0" cellspacing="0">
                                    <tr>
                                        <td width="33%" style="padding:0 6px 0 0;">
                                            <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f0fdf4; border-radius:8px; border: 1px solid #bbf7d0;">
                                                <tr>
                                                    <td style="padding:16px; text-align:center;">
                                                        <p style="font-size:28px; font-weight:700; color:#16a34a; margin:0;">{total_users}</p>
                                                        <p style="font-size:11px; color:#4b5563; margin:6px 0 0; text-transform:uppercase; letter-spacing:0.5px;">Total usuarios</p>
                                                    </td>
                                                </tr>
                                            </table>
                                        </td>
                                        <td width="33%" style="padding:0 3px;">
                                            <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#eff6ff; border-radius:8px; border: 1px solid #bfdbfe;">
                                                <tr>
                                                    <td style="padding:16px; text-align:center;">
                                                        <p style="font-size:28px; font-weight:700; color:#2563eb; margin:0;">{total_ativos}</p>
                                                        <p style="font-size:11px; color:#4b5563; margin:6px 0 0; text-transform:uppercase; letter-spacing:0.5px;">Ativos (30d)</p>
                                                    </td>
                                                </tr>
                                            </table>
                                        </td>
                                        <td width="33%" style="padding:0 0 0 6px;">
                                            <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#fef2f2; border-radius:8px; border: 1px solid #fecaca;">
                                                <tr>
                                                    <td style="padding:16px; text-align:center;">
                                                        <p style="font-size:28px; font-weight:700; color:#dc2626; margin:0;">{total_inativos}</p>
                                                        <p style="font-size:11px; color:#4b5563; margin:6px 0 0; text-transform:uppercase; letter-spacing:0.5px;">Inativos</p>
                                                    </td>
                                                </tr>
                                            </table>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>

                        <!-- Barra de porcentagem -->
                        <tr>
                            <td style="padding:0 40px 24px;">
                                <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f9fafb; border-radius:8px; border:1px solid #e5e7eb;">
                                    <tr>
                                        <td style="padding:14px 18px;">
                                            <p style="font-size:12px; color:#6b7280; margin:0 0 8px; text-transform:uppercase; letter-spacing:0.5px;">Taxa de inatividade</p>
                                            <table width="100%" cellpadding="0" cellspacing="0">
                                                <tr>
                                                    <td style="background-color:#e5e7eb; border-radius:4px; height:8px;">
                                                        <table width="{pct_inativos}%" cellpadding="0" cellspacing="0">
                                                            <tr>
                                                                <td style="background-color:#dc2626; border-radius:4px; height:8px;"></td>
                                                            </tr>
                                                        </table>
                                                    </td>
                                                    <td width="50" style="text-align:right; padding-left:12px;">
                                                        <span style="font-size:14px; font-weight:700; color:#374151;">{pct_inativos}%</span>
                                                    </td>
                                                </tr>
                                            </table>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>

                        <!-- Status -->
                        <tr>
                            <td style="padding:0 40px 24px;">
                                <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#fffbeb; border-radius:8px; border:1px solid #fde68a;">
                                    <tr>
                                        <td style="padding:12px 18px;">
                                            <p style="font-size:13px; color:#92400e; margin:0;">
                                                <strong>Status:</strong> {status_desativacao}
                                            </p>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>

                        <!-- Anexos -->
                        <tr>
                            <td style="padding:0 40px 30px;">
                                <p style="font-size:14px; color:#374151; margin:0 0 8px;">
                                    <strong>Anexos:</strong>
                                </p>
                                <p style="font-size:13px; color:#6b7280; margin:0; line-height:1.8;">
                                    &#128206; usuarios_inativos_para_desativar.xlsx<br>
                                    &#128206; usuarios_inativos_para_desativar.csv
                                </p>
                            </td>
                        </tr>

                        <!-- Footer -->
                        <tr>
                            <td style="background-color:#f9fafb; padding:16px 40px; border-top:1px solid #e5e7eb; text-align:center;">
                                <p style="font-size:11px; color:#9ca3af; margin:0;">
                                    Enviado automaticamente pelo sistema SAC User Automation
                                </p>
                            </td>
                        </tr>

                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    anexos = [
        os.path.abspath("usuarios_inativos_para_desativar.xlsx"),
        os.path.abspath("usuarios_inativos_para_desativar.csv"),
    ]
    try:
        enviar_relatorio(EMAIL_SMTP_HOST, EMAIL_SMTP_PORT, EMAIL_FROM, EMAIL_DESTINATARIOS, assunto, corpo, anexos)
    except Exception as e:
        print(f"Erro ao enviar email: {e}")
