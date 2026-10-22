import os
import pandas as pd

from config import COL_USER_ID_USERS, COL_USER_NAME, COL_USER_EMAIL

# Trecho do dominio de email -> nome da empresa (ordem importa: o primeiro que casar vence)
EMPRESAS_POR_DOMINIO = [
    ("rebic", "REBIC"),
    ("unialfa", "UNIALFA"),
    ("vitamedic", "VITAMEDIC"),
    ("nelindustria", "N&L"),
    ("nel", "N&L"),
    ("grupojosealves", "HOLDING GJA"),
]

# Coluna interna -> nome exibido no CSV/Excel/email
COLUNAS_SAIDA = {
    COL_USER_ID_USERS: "USUARIO",
    COL_USER_NAME: "NOME COMPLETO",
    COL_USER_EMAIL: "EMAIL",
    "EMPRESA": "EMPRESA",
    "ULTIMO_ACESSO": "ULTIMO ACESSO",
    "DIAS_SEM_ACESSO": "DIAS SEM ACESSO",
    "LICENCA": "LICENCA",
}


def empresa_from_email(email):
    if pd.isna(email) or "@" not in str(email):
        return ""
    dominio = str(email).split("@")[-1].lower()
    for trecho, empresa in EMPRESAS_POR_DOMINIO:
        if trecho in dominio:
            return empresa
    return dominio.split(".")[0].upper()


def preparar_df_saida(df_inativos):
    """Monta o DataFrame final com as mesmas colunas para CSV, Excel e email."""
    df = df_inativos.copy()
    df["EMPRESA"] = df[COL_USER_EMAIL].apply(empresa_from_email)
    df["LICENCA"] = 1
    colunas = dict(COLUNAS_SAIDA)
    if "RESULTADO" in df.columns:
        colunas["RESULTADO"] = "RESULTADO DESATIVACAO"
    df_saida = df[list(colunas.keys())].rename(columns=colunas)
    # Ordena por empresa (sem empresa por ultimo) e usuario
    df_saida["_ord"] = df_saida["EMPRESA"].eq("")
    return (df_saida.sort_values(["_ord", "EMPRESA", "USUARIO"])
            .drop(columns="_ord").reset_index(drop=True))


def _ajustar_largura_colunas(ws):
    for col_cells in ws.columns:
        largura = max((len(str(c.value)) for c in col_cells if c.value is not None), default=0)
        ws.column_dimensions[col_cells[0].column_letter].width = min(max(12, largura + 2), 60)


def exportar_relatorios(df_saida, caminho_csv, caminho_xlsx, df_protegidos=None):
    """Grava o CSV e o Excel (aba Inativos + aba Protegidos) a partir do DataFrame final."""
    df_saida.to_csv(caminho_csv, index=False, encoding="utf-8-sig")
    print(f"Arquivo CSV gerado em: {os.path.abspath(caminho_csv)}")

    with pd.ExcelWriter(caminho_xlsx, engine="openpyxl") as writer:
        df_saida.to_excel(writer, index=False, sheet_name="Inativos")
        ws = writer.sheets["Inativos"]
        ws.freeze_panes = "A2"
        if len(df_saida) > 0:
            ws.auto_filter.ref = ws.dimensions
        _ajustar_largura_colunas(ws)

        if df_protegidos is not None and len(df_protegidos) > 0:
            df_protegidos.to_excel(writer, index=False, sheet_name="Protegidos")
            ws2 = writer.sheets["Protegidos"]
            ws2.freeze_panes = "A2"
            _ajustar_largura_colunas(ws2)
    print(f"Arquivo Excel gerado em: {os.path.abspath(caminho_xlsx)}")
