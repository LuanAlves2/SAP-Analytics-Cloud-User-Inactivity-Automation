import os
import socket
import sys
import traceback
from datetime import datetime, timedelta

import pandas as pd

from config import *
from sac_utils import (
    get_token, get_csrf_token, desativar_usuario,
    buscar_todos_usuarios, exportar_atividades,
)
from export_utils import preparar_df_saida, exportar_relatorios
from email_utils import enviar_email, montar_email_relatorio, montar_email_erro

LABEL_RESULTADO = {
    "desativado": "Desativado",
    "ja_desativado": "Ja estava desativado",
    "nao_encontrado": "Nao encontrado",
    "erro": "Falha",
}


def validar_config():
    faltando = [n for n, v in {
        "CLIENT_ID": CLIENT_ID, "CLIENT_SECRET": CLIENT_SECRET,
        "OAUTH_TOKEN_URL": OAUTH_TOKEN_URL, "TENANT_URL": TENANT_URL,
    }.items() if not v]
    if faltando:
        raise RuntimeError(f"Variaveis obrigatorias ausentes no .env: {', '.join(faltando)}")


def formatar_data(dt):
    return "NUNCA ACESSOU" if pd.isna(dt) else dt.strftime("%d/%m/%Y %H:%M")


def executar():
    agora = datetime.now()
    data_corte = agora - timedelta(days=DIAS_INATIVIDADE)
    data_carencia = agora - timedelta(days=DIAS_CARENCIA_USUARIO_NOVO)
    print(f"Inicio: {agora:%d/%m/%Y %H:%M:%S} | criterio: sem atividade desde {data_corte:%d/%m/%Y}")

    validar_config()

    # --- Token OAuth ---
    etapa = "autenticacao OAuth"
    print("\nObtendo token OAuth...")
    token = get_token(OAUTH_TOKEN_URL, CLIENT_ID, CLIENT_SECRET)

    # --- Usuarios via SCIM ---
    etapa = "extracao de usuarios (SCIM)"
    print("\nExtraindo usuarios via SCIM API...")
    df_users = buscar_todos_usuarios(SAC_SCIM_API_URL, token)
    total_contas = len(df_users)
    if COL_IS_DEACTIVATED in df_users.columns:
        df_users = df_users[df_users[COL_IS_DEACTIVATED].isna() | (df_users[COL_IS_DEACTIVATED] == "")].copy()
    print(f"Contas no SAC: {total_contas} | habilitadas: {len(df_users)}")

    # --- Atividades ---
    etapa = "extracao do log de atividades"
    print("\nExtraindo atividades via API...")
    df_atv = exportar_atividades(SAC_ACTIVITIES_URL, token, CSRF_URL)
    if COL_OBJECT_TYPE not in df_atv.columns or COL_TIMESTAMP not in df_atv.columns:
        raise RuntimeError(
            f"Colunas '{COL_OBJECT_TYPE}'/'{COL_TIMESTAMP}' nao encontradas nas atividades. "
            f"Colunas disponiveis: {df_atv.columns.tolist()}"
        )
    df_atv = df_atv[df_atv[COL_OBJECT_TYPE] == "User"].copy()
    df_atv["_ts"] = pd.to_datetime(
        df_atv[COL_TIMESTAMP].astype(str).str.strip(), format=FORMATO_TIMESTAMP_ATIVIDADE, errors="coerce"
    )
    invalidos = int(df_atv["_ts"].isna().sum())
    if invalidos:
        print(f"Aviso: {invalidos} linhas de atividade com timestamp invalido foram ignoradas.")
    ultimo_acesso = (
        df_atv.dropna(subset=["_ts"])
        .assign(_uid=lambda d: d[COL_USER_ID_ATIVIDADE].astype(str).str.strip())
        .groupby("_uid")["_ts"].max()
    )

    # --- Classificacao ---
    etapa = "classificacao dos usuarios"
    df_users["ULTIMO_ACESSO_DT"] = df_users[COL_USER_ID_USERS].astype(str).str.strip().map(ultimo_acesso)
    criado_em = pd.to_datetime(df_users[COL_USER_CREATED], errors="coerce", utc=True)
    df_users["CRIADO_EM_DT"] = criado_em.dt.tz_convert(None)

    protegidos = {u.lower() for u in USERS_PROTEGIDOS}
    eh_protegido = (
        df_users[COL_USER_EMAIL].astype(str).str.lower().isin(protegidos)
        | df_users[COL_USER_ID_USERS].astype(str).str.lower().isin(protegidos)
    )
    acesso_recente = df_users["ULTIMO_ACESSO_DT"] >= data_corte          # NaT -> False
    usuario_novo = df_users["CRIADO_EM_DT"] >= data_carencia            # NaT -> False

    df_users["STATUS"] = "inativo"
    df_users.loc[eh_protegido & ~acesso_recente, "STATUS"] = "protegido"
    df_users.loc[usuario_novo & ~acesso_recente & ~eh_protegido, "STATUS"] = "novo"
    df_users.loc[acesso_recente, "STATUS"] = "ativo"

    df_users["ULTIMO_ACESSO"] = df_users["ULTIMO_ACESSO_DT"].apply(formatar_data)
    df_users["DIAS_SEM_ACESSO"] = df_users["ULTIMO_ACESSO_DT"].apply(
        lambda dt: "NUNCA ACESSOU" if pd.isna(dt) else (agora - dt).days
    )

    df_inativos = df_users[df_users["STATUS"] == "inativo"].copy()
    df_protegidos = df_users[df_users["STATUS"] == "protegido"].copy()
    total_ativos = int((df_users["STATUS"] == "ativo").sum())
    total_novos = int((df_users["STATUS"] == "novo").sum())

    print(f"\nUsuarios habilitados no SAC: {len(df_users)}")
    print(f"Com acesso nos ultimos {DIAS_INATIVIDADE} dias: {total_ativos}")
    print(f"Inativos protegidos (nao desativar): {len(df_protegidos)}")
    print(f"Contas novas em carencia (ignoradas): {total_novos}")
    print(f"Passiveis de desativacao: {len(df_inativos)}\n")
    if len(df_inativos):
        print(df_inativos[[COL_USER_ID_USERS, COL_USER_NAME, COL_USER_EMAIL, "ULTIMO_ACESSO", "DIAS_SEM_ACESSO"]].to_string(index=False))
    if len(df_protegidos):
        print("\nProtegidos inativos:")
        print(df_protegidos[[COL_USER_ID_USERS, COL_USER_NAME, COL_USER_EMAIL, "ULTIMO_ACESSO"]].to_string(index=False))

    # --- Desativacao ---
    etapa = "desativacao"
    modo = "desativacao" if DESATIVAR else "relatorio"
    resultados = {}
    erro_desativacao = None
    if DESATIVAR and len(df_inativos) > 0:
        ids = df_inativos[COL_USER_ID_USERS].astype(str).tolist()
        if DESATIVAR_APENAS_UM:
            ids = ids[:1]
            print("\nMODO TESTE: apenas o primeiro usuario sera desativado.")
        try:
            print("\nObtendo CSRF token para desativacao...")
            csrf_token, cookies = get_csrf_token(CSRF_URL, token)
            for i, uid in enumerate(ids, 1):
                status, msg = desativar_usuario(SAC_SCIM_API_URL, token, uid, csrf_token, cookies)
                resultados[uid] = status
                print(f"[{i}/{len(ids)}] {uid}: {msg}")
        except Exception as e:
            erro_desativacao = f"{type(e).__name__}: {e}"
            print(f"\nERRO na desativacao: {erro_desativacao}")
            traceback.print_exc()
        df_inativos["RESULTADO"] = df_inativos[COL_USER_ID_USERS].astype(str).map(
            lambda u: LABEL_RESULTADO.get(resultados.get(u), "Nao processado")
        )
    elif DESATIVAR:
        print("\nNenhum usuario a desativar.")
    else:
        df_inativos["RESULTADO"] = "Nao desativado (modo relatorio)"
        print("\nModo relatorio (DESATIVAR = False): nenhum usuario foi desativado.")

    qtd = lambda s: sum(1 for v in resultados.values() if v == s)
    qtd_desativados, qtd_ja, qtd_falhas = qtd("desativado"), qtd("ja_desativado"), qtd("erro") + qtd("nao_encontrado")

    # --- Relatorios ---
    etapa = "geracao dos relatorios"
    df_saida = preparar_df_saida(df_inativos)
    df_prot_saida = preparar_df_saida(df_protegidos) if len(df_protegidos) else None
    exportar_relatorios(df_saida, ARQUIVO_SAIDA_CSV, ARQUIVO_SAIDA_XLSX, df_prot_saida)

    # --- Email ---
    etapa = "envio do email"
    if EMAIL_DESTINATARIOS:
        total_users = len(df_users)
        ctx = {
            "data_hoje": agora.strftime("%d/%m/%Y"),
            "hora": agora.strftime("%H:%M"),
            "data_corte": data_corte.strftime("%d/%m/%Y"),
            "dias_inatividade": DIAS_INATIVIDADE,
            "dias_carencia": DIAS_CARENCIA_USUARIO_NOVO,
            "total_users": total_users,
            "total_ativos": total_ativos,
            "total_inativos": len(df_inativos),
            "total_protegidos": len(df_protegidos),
            "total_novos": total_novos,
            "pct_inativos": round(len(df_inativos) / total_users * 100, 1) if total_users else 0,
            "modo": modo,
            "apenas_um": bool(DESATIVAR and DESATIVAR_APENAS_UM),
            "qtd_desativados": qtd_desativados,
            "qtd_ja_desativados": qtd_ja,
            "qtd_falhas": qtd_falhas,
            "erro_desativacao": erro_desativacao,
            "df_saida": df_saida,
            "protegidos": df_prot_saida.to_dict("records") if df_prot_saida is not None else [],
            "anexos": [os.path.basename(ARQUIVO_SAIDA_XLSX), os.path.basename(ARQUIVO_SAIDA_CSV)],
            "max_linhas_tabela": EMAIL_MAX_LINHAS_TABELA,
            "host": socket.gethostname(),
        }
        assunto, corpo = montar_email_relatorio(ctx)
        anexos = [ARQUIVO_SAIDA_XLSX, ARQUIVO_SAIDA_CSV]
        try:
            enviar_email(EMAIL_SMTP_HOST, EMAIL_SMTP_PORT, EMAIL_FROM, EMAIL_DESTINATARIOS, assunto, corpo, anexos)
        except Exception as e:
            print(f"Erro ao enviar email: {e}")
    else:
        print("EMAIL_DESTINATARIOS vazio: email nao enviado.")

    print(f"\nFim: {datetime.now():%d/%m/%Y %H:%M:%S}")
    return erro_desativacao is None and qtd_falhas == 0


def main():
    try:
        ok = executar()
        return 0 if ok else 2
    except Exception as e:
        tb = traceback.format_exc()
        # 'etapa' e atualizada dentro de executar(); recuperamos do frame da excecao
        etapa = _etapa_do_frame(sys.exc_info()[2]) or "desconhecida"
        print(f"\nERRO FATAL na etapa '{etapa}': {type(e).__name__}: {e}")
        print(tb)
        if EMAIL_DESTINATARIOS and EMAIL_SMTP_HOST:
            agora = datetime.now()
            try:
                assunto, corpo = montar_email_erro(
                    etapa, f"{type(e).__name__}: {e}", tb, agora.strftime("%d/%m/%Y"), agora.strftime("%H:%M")
                )
                enviar_email(EMAIL_SMTP_HOST, EMAIL_SMTP_PORT, EMAIL_FROM, EMAIL_DESTINATARIOS, assunto, corpo)
            except Exception as e2:
                print(f"Nao foi possivel enviar o email de erro: {e2}")
        return 1


def _etapa_do_frame(tb):
    """Recupera a variavel local 'etapa' do frame de executar() na pilha da excecao."""
    while tb is not None:
        if tb.tb_frame.f_code.co_name == "executar":
            return tb.tb_frame.f_locals.get("etapa")
        tb = tb.tb_next
    return None


if __name__ == "__main__":
    sys.exit(main())
