import pandas as pd
import os


def exportar_inativos_para_xlsx(df_inativos, caminho_saida_xlsx):
    """Gera Excel a partir do DataFrame de inativos ja processado."""
    df = df_inativos.copy()

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

    df["EMPRESA"] = df["EMAIL"].apply(empresa_from_email)
    df["Licenca"] = 1

    colunas = ["USER_NAME", "DISPLAY_NAME", "EMAIL", "ULTIMO_ACESSO", "DIAS_SEM_ACESSO", "Licenca", "EMPRESA"]
    df_saida = df[colunas].rename(columns={
        "USER_NAME": "USUARIO",
        "DISPLAY_NAME": "NOME COMPLETO",
        "DIAS_SEM_ACESSO": "DIAS SEM ACESSO",
    })
    df_saida.to_excel(caminho_saida_xlsx, index=False)
    print(f"Arquivo Excel gerado em: {os.path.abspath(caminho_saida_xlsx)}")
