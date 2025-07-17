import pandas as pd
from datetime import datetime
import os

def exportar_inativos_para_xlsx(caminho_csv_inativos, caminho_atividade_csv, caminho_saida_xlsx):
    df_inativos = pd.read_csv(caminho_csv_inativos)
    df_atividade = pd.read_csv(caminho_atividade_csv, skiprows=1)
    df_atividade.columns = [col.strip() for col in df_atividade.columns]

    ultimos_acessos = (
        df_atividade[df_atividade["Object Type"] == "User"]
        .groupby("User Name")["Timestamp"].max()
        .reset_index()
        .rename(columns={"User Name": "USUARIO", "Timestamp": "ULTIMO_ACESSO"})
    )
    df_inativos['USUARIO'] = df_inativos['USER_NAME']
    df_inativos = df_inativos.merge(ultimos_acessos, on='USUARIO', how='left')
    hoje = datetime.now()
    def calcular_dias(dt_str):
        if pd.isna(dt_str):
            return ''
        try:
            dt = datetime.strptime(dt_str, "%Y.%m.%d %H:%M:%S")
            return (hoje - dt).days
        except Exception:
            return ''

    df_inativos['DIAS SEM ACESSO'] = df_inativos['ULTIMO_ACESSO'].apply(calcular_dias)
    def empresa_from_email(email):
        if pd.isna(email):
            return ''
        dominio = email.split('@')[-1].lower()
        if 'rebic' in dominio:
            return 'REBIC'
        if 'unialfa' in dominio:
            return 'UNIALFA'
        if 'vitamedic' in dominio:
            return 'VITAMEDIC'
        if 'nelindustria' in dominio or 'nel' in dominio:
            return 'N&L'
        if 'grupojosealves' in dominio:
            return 'HOLDING GJA'
        return dominio.split('.')[0].upper()

    df_inativos['EMPRESA'] = df_inativos['EMAIL'].apply(empresa_from_email)
    df_inativos['Licença'] = 1
    df_saida = df_inativos[['USUARIO', 'DISPLAY_NAME', 'EMAIL', 'DIAS SEM ACESSO', 'Licença', 'EMPRESA']]
    df_saida = df_saida.rename(columns={'DISPLAY_NAME': 'NOME COMPLETO'})
    df_saida.to_excel(caminho_saida_xlsx, index=False)
    print(f"Arquivo Excel gerado em: {os.path.abspath(caminho_saida_xlsx)}")
