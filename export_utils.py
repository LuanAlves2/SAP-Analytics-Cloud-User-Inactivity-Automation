import pandas as pd
from datetime import datetime
import os

def exportar_inativos_para_xlsx(df_inativos, df_atividade, caminho_saida_xlsx):
    """Gera Excel com dias sem acesso. Recebe DataFrames diretamente."""
    df_inativos = df_inativos.copy()

    # Ultimos acessos por usuario (coluna "User Name" das atividades)
    df_user_ativ = df_atividade[df_atividade["Object Type"] == "User"].copy()
    ultimos_acessos = (
        df_user_ativ.groupby("User Name")["Timestamp"].max()
        .reset_index()
        .rename(columns={"Timestamp": "ULTIMO_ACESSO"})
    )

    # Merge por USER_NAME (tenta match direto)
    df_inativos = df_inativos.merge(
        ultimos_acessos, left_on="USER_NAME", right_on="User Name", how="left"
    )
    if "User Name" in df_inativos.columns:
        df_inativos.drop(columns=["User Name"], inplace=True)

    hoje = datetime.now()
    def calcular_dias(dt_str):
        if pd.isna(dt_str) or dt_str == "":
            return ""
        try:
            dt = datetime.strptime(str(dt_str).strip(), "%Y.%m.%d %H:%M:%S")
            return (hoje - dt).days
        except Exception:
            return ""

    df_inativos["DIAS SEM ACESSO"] = df_inativos["ULTIMO_ACESSO"].apply(calcular_dias)

    def formatar_ultimo_acesso(dt_str):
        if pd.isna(dt_str) or dt_str == "":
            return "NUNCA ACESSOU"
        try:
            dt = datetime.strptime(str(dt_str).strip(), "%Y.%m.%d %H:%M:%S")
            return dt.strftime("%d/%m/%Y %H:%M")
        except Exception:
            return "NUNCA ACESSOU"

    df_inativos["ULTIMO_ACESSO"] = df_inativos["ULTIMO_ACESSO"].apply(formatar_ultimo_acesso)
    df_inativos["DIAS SEM ACESSO"] = df_inativos.apply(
        lambda row: "NUNCA ACESSOU" if row["ULTIMO_ACESSO"] == "NUNCA ACESSOU" else row["DIAS SEM ACESSO"], axis=1
    )

    def empresa_from_email(email):
        if pd.isna(email):
            return ""
        dominio = email.split("@")[-1].lower()
        if "rebic" in dominio:
            return "REBIC"
        if "unialfa" in dominio:
            return "UNIALFA"
        if "vitamedic" in dominio:
            return "VITAMEDIC"
        if "nelindustria" in dominio or "nel" in dominio:
            return "N&L"
        if "grupojosealves" in dominio:
            return "HOLDING GJA"
        return dominio.split(".")[0].upper()

    df_inativos["EMPRESA"] = df_inativos["EMAIL"].apply(empresa_from_email)
    df_inativos["Licenca"] = 1
    df_saida = df_inativos[["USER_NAME", "DISPLAY_NAME", "EMAIL", "ULTIMO_ACESSO", "DIAS SEM ACESSO", "Licenca", "EMPRESA"]]
    df_saida = df_saida.rename(columns={"USER_NAME": "USUARIO", "DISPLAY_NAME": "NOME COMPLETO"})
    df_saida.to_excel(caminho_saida_xlsx, index=False)
    print(f"Arquivo Excel gerado em: {os.path.abspath(caminho_saida_xlsx)}")
