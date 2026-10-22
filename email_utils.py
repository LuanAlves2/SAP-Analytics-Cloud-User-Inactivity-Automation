import html
import mimetypes
import os
import smtplib
import socket
from email.message import EmailMessage
from email.utils import formatdate, make_msgid

import pandas as pd


# ----------------------------------------------------------------------------
# Envio
# ----------------------------------------------------------------------------

def enviar_email(smtp_host, smtp_port, email_from, destinatarios, assunto, corpo_html, anexos=None):
    """Envia um email HTML (com fallback em texto) e anexos via SMTP."""
    if not destinatarios:
        print("Nenhum destinatario configurado. Email nao enviado.")
        return

    msg = EmailMessage()
    msg["From"] = email_from
    msg["To"] = ", ".join(destinatarios)
    msg["Subject"] = assunto
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid()
    msg.set_content("Este email contem um relatorio em HTML. Abra em um cliente com suporte a HTML.")
    msg.add_alternative(corpo_html, subtype="html")

    for caminho in (anexos or []):
        if not os.path.exists(caminho):
            print(f"Anexo nao encontrado, ignorado: {caminho}")
            continue
        tipo, _ = mimetypes.guess_type(caminho)
        maintype, subtype = (tipo or "application/octet-stream").split("/", 1)
        with open(caminho, "rb") as f:
            msg.add_attachment(f.read(), maintype=maintype, subtype=subtype,
                               filename=os.path.basename(caminho))

    with smtplib.SMTP(smtp_host, smtp_port, timeout=60) as server:
        server.send_message(msg)

    print(f"Email enviado para: {', '.join(destinatarios)}")


# Compatibilidade com a assinatura antiga
enviar_relatorio = enviar_email


# ----------------------------------------------------------------------------
# Montagem do HTML
# ----------------------------------------------------------------------------

_FONTE = "font-family:'Segoe UI',Arial,Helvetica,sans-serif;"

CORES_RESULTADO = {
    "Desativado": ("#166534", "#dcfce7"),
    "Ja estava desativado": ("#374151", "#e5e7eb"),
    "Falha": ("#991b1b", "#fee2e2"),
    "Nao encontrado": ("#991b1b", "#fee2e2"),
    "Nao processado": ("#6b7280", "#f3f4f6"),
    "Nao desativado (modo relatorio)": ("#92400e", "#fef3c7"),
}


def _e(valor):
    """Escapa texto para HTML, tratando None/NaN."""
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return ""
    return html.escape(str(valor))


def _card(valor, titulo, descricao, cor_valor, cor_fundo, cor_borda):
    return f"""
    <td width="25%" valign="top" style="padding:0 4px;">
      <table width="100%" cellpadding="0" cellspacing="0" bgcolor="{cor_fundo}"
             style="background-color:{cor_fundo}; border:1px solid {cor_borda}; border-radius:8px;">
        <tr><td style="padding:14px 8px; text-align:center;">
          <p style="{_FONTE} font-size:26px; font-weight:700; color:{cor_valor}; margin:0;">{valor}</p>
          <p style="{_FONTE} font-size:11px; font-weight:600; color:#374151; margin:6px 0 0; text-transform:uppercase; letter-spacing:0.4px;">{titulo}</p>
          <p style="{_FONTE} font-size:11px; color:#6b7280; margin:4px 0 0; line-height:1.4;">{descricao}</p>
        </td></tr>
      </table>
    </td>"""


def _caixa(titulo, texto, cor_texto, cor_fundo, cor_borda):
    return f"""
    <tr><td style="padding:0 32px 20px;">
      <table width="100%" cellpadding="0" cellspacing="0" bgcolor="{cor_fundo}"
             style="background-color:{cor_fundo}; border:1px solid {cor_borda}; border-left:5px solid {cor_texto}; border-radius:6px;">
        <tr><td style="padding:12px 16px;">
          <p style="{_FONTE} font-size:14px; font-weight:700; color:{cor_texto}; margin:0 0 4px;">{titulo}</p>
          <p style="{_FONTE} font-size:13px; color:#374151; margin:0; line-height:1.5;">{texto}</p>
        </td></tr>
      </table>
    </td></tr>"""


def _badge(texto):
    cor, fundo = CORES_RESULTADO.get(texto, ("#374151", "#e5e7eb"))
    return (f'<span style="{_FONTE} display:inline-block; font-size:11px; font-weight:600; color:{cor}; '
            f'background-color:{fundo}; padding:2px 8px; border-radius:10px; white-space:nowrap;">{_e(texto)}</span>')


def _tabela_usuarios(df, mostrar_resultado, max_linhas):
    """Tabela HTML dos usuarios inativos. df ja esta no formato de saida (preparar_df_saida)."""
    if len(df) == 0:
        return (f'<p style="{_FONTE} font-size:13px; color:#6b7280; margin:0;">'
                f'Nenhum usuario passivel de desativacao nesta execucao.</p>')

    colunas = ["USUARIO", "NOME COMPLETO", "EMPRESA", "ULTIMO ACESSO", "DIAS SEM ACESSO"]
    if mostrar_resultado:
        colunas.append("RESULTADO DESATIVACAO")

    th = "".join(
        f'<th align="left" style="{_FONTE} font-size:11px; color:#4b5563; text-transform:uppercase; '
        f'letter-spacing:0.4px; padding:8px 10px; border-bottom:2px solid #e5e7eb; background-color:#f9fafb;">{_e(c)}</th>'
        for c in colunas
    )

    linhas = []
    for i, (_, row) in enumerate(df.head(max_linhas).iterrows()):
        fundo = "#ffffff" if i % 2 == 0 else "#f9fafb"
        tds = []
        for c in colunas:
            valor = row.get(c, "")
            if c == "RESULTADO DESATIVACAO":
                conteudo = _badge(valor)
            elif c == "DIAS SEM ACESSO":
                conteudo = f'<span style="font-weight:600;">{_e(valor)}</span>'
            else:
                conteudo = _e(valor)
            tds.append(f'<td style="{_FONTE} font-size:12px; color:#1f2937; padding:8px 10px; '
                       f'border-bottom:1px solid #f3f4f6; vertical-align:top;">{conteudo}</td>')
        linhas.append(f'<tr bgcolor="{fundo}">{"".join(tds)}</tr>')

    restante = len(df) - max_linhas
    rodape = ""
    if restante > 0:
        rodape = (f'<p style="{_FONTE} font-size:12px; color:#6b7280; margin:8px 0 0;">'
                  f'Exibindo os primeiros {max_linhas} de {len(df)} usuarios. A lista completa esta nos anexos.</p>')

    return (f'<table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">'
            f'<tr>{th}</tr>{"".join(linhas)}</table>{rodape}')


def montar_email_relatorio(ctx):
    """Monta assunto e HTML do relatorio.

    ctx (dict) deve conter:
      data_hoje, hora, data_corte, dias_inatividade, dias_carencia,
      total_users, total_ativos, total_inativos, total_protegidos, total_novos, pct_inativos,
      modo ("desativacao" | "relatorio"), apenas_um (bool),
      qtd_desativados, qtd_ja_desativados, qtd_falhas, erro_desativacao (str|None),
      df_saida (DataFrame formato de saida), protegidos (lista de dict USUARIO/NOME/EMAIL),
      anexos (lista de nomes), max_linhas_tabela, host
    """
    c = ctx
    modo_desativacao = c["modo"] == "desativacao"

    # ---- Assunto ----
    if modo_desativacao:
        if c.get("erro_desativacao"):
            resumo_assunto = f"ERRO na desativacao ({c['total_inativos']} inativos, {c['qtd_desativados']} desativados)"
        elif c["qtd_falhas"] > 0:
            resumo_assunto = f"{c['qtd_desativados']} desativados, {c['qtd_falhas']} falhas"
        else:
            resumo_assunto = f"{c['qtd_desativados']} usuarios desativados"
    else:
        resumo_assunto = f"{c['total_inativos']} inativos identificados (sem desativacao)"
    assunto = f"[SAC] Usuarios inativos: {resumo_assunto} - {c['data_hoje']}"

    # ---- Frase de resumo ----
    if modo_desativacao:
        if c["total_inativos"] == 0:
            frase = "Nenhum usuario ficou sem acesso por mais de {d} dias. Nenhuma desativacao foi necessaria."
        elif c["apenas_um"]:
            frase = ("Foram identificados <strong>{n}</strong> usuarios sem acesso ha mais de {d} dias. "
                     "Por estar em <strong>modo de teste</strong>, apenas o primeiro da lista foi processado.")
        else:
            frase = ("Foram identificados <strong>{n}</strong> usuarios sem acesso ha mais de {d} dias e a "
                     "desativacao automatica foi executada. O resultado de cada usuario esta na tabela abaixo.")
    else:
        frase = ("Foram identificados <strong>{n}</strong> usuarios sem acesso ha mais de {d} dias. "
                 "<strong>Nenhum usuario foi desativado</strong>: a automacao esta em modo relatorio.")
    frase = frase.format(n=c["total_inativos"], d=c["dias_inatividade"])

    # ---- Caixa de status ----
    if c.get("erro_desativacao"):
        status_html = _caixa(
            "Desativacao interrompida por erro",
            f"A etapa de desativacao falhou antes de processar todos os usuarios: <code>{_e(c['erro_desativacao'])}</code>. "
            f"Os relatorios em anexo foram gerados normalmente. Verifique o log do servico.",
            "#991b1b", "#fef2f2", "#fecaca")
    elif not modo_desativacao:
        status_html = _caixa(
            "Modo relatorio: nenhuma alteracao feita no SAC",
            "A automacao esta configurada apenas para gerar o relatorio (DESATIVAR = False). "
            "Revise a lista em anexo; para desativar automaticamente, altere a configuracao no servidor.",
            "#92400e", "#fffbeb", "#fde68a")
    elif c["qtd_falhas"] > 0:
        ja = f", {c['qtd_ja_desativados']} ja estava(m) desativado(s)" if c["qtd_ja_desativados"] else ""
        status_html = _caixa(
            f"Desativacao concluida com {c['qtd_falhas']} falha(s)",
            f"{c['qtd_desativados']} usuario(s) desativado(s) com sucesso{ja} e {c['qtd_falhas']} falhou(aram). "
            f"Veja a coluna <em>Resultado</em> na tabela e trate manualmente os que falharam.",
            "#991b1b", "#fef2f2", "#fecaca")
    elif c["total_inativos"] == 0:
        status_html = _caixa(
            "Tudo em ordem",
            "Nao havia usuarios a desativar nesta execucao.",
            "#166534", "#f0fdf4", "#bbf7d0")
    else:
        extra = " Modo de teste: apenas o primeiro usuario foi processado." if c["apenas_um"] else ""
        status_html = _caixa(
            "Desativacao executada com sucesso",
            f"{c['qtd_desativados']} usuario(s) desativado(s) no SAP Analytics Cloud."
            f"{' ' + str(c['qtd_ja_desativados']) + ' ja estava(m) desativado(s).' if c['qtd_ja_desativados'] else ''}{extra} "
            f"As licencas desses usuarios foram liberadas.",
            "#166534", "#f0fdf4", "#bbf7d0")

    # ---- Cards ----
    cards = "".join([
        _card(c["total_users"], "Usuarios ativos no SAC", "Contas habilitadas hoje", "#1f2937", "#f9fafb", "#e5e7eb"),
        _card(c["total_ativos"], f"Com acesso ({c['dias_inatividade']}d)", f"Usaram o SAC desde {c['data_corte']}", "#1d4ed8", "#eff6ff", "#bfdbfe"),
        _card(c["total_inativos"], "Inativos", f"Sem acesso ha mais de {c['dias_inatividade']} dias", "#dc2626", "#fef2f2", "#fecaca"),
        _card(c["qtd_desativados"] if modo_desativacao else 0, "Desativados hoje", "Nesta execucao", "#166534", "#f0fdf4", "#bbf7d0"),
    ])

    # ---- Protegidos / novos ----
    obs = []
    if c["total_protegidos"] > 0:
        nomes = ", ".join(_e(p["USUARIO"]) for p in c["protegidos"][:15])
        if len(c["protegidos"]) > 15:
            nomes += f" e mais {len(c['protegidos']) - 15}"
        obs.append(f"<strong>{c['total_protegidos']} usuario(s) inativo(s) estao na lista de protecao</strong> e nunca sao "
                   f"desativados pela automacao: {nomes}. Eles aparecem na aba <em>Protegidos</em> do Excel.")
    if c["total_novos"] > 0:
        obs.append(f"<strong>{c['total_novos']} usuario(s) criado(s) ha menos de {c['dias_carencia']} dias</strong> ainda nao "
                   f"acessaram o SAC e foram ignorados (periodo de carencia para contas novas).")
    obs_html = ""
    if obs:
        itens = "".join(f'<li style="margin-bottom:6px;">{o}</li>' for o in obs)
        obs_html = f"""
        <tr><td style="padding:0 32px 20px;">
          <p style="{_FONTE} font-size:14px; font-weight:700; color:#111827; margin:0 0 8px;">Observacoes</p>
          <ul style="{_FONTE} font-size:13px; color:#374151; margin:0; padding-left:18px; line-height:1.5;">{itens}</ul>
        </td></tr>"""

    # ---- Tabela ----
    tabela_html = _tabela_usuarios(c["df_saida"], modo_desativacao, c["max_linhas_tabela"])

    # ---- Anexos ----
    anexos_html = "<br>".join(f"&#128206; {_e(a)}" for a in c["anexos"])

    pct = c["pct_inativos"]
    largura_barra = max(0, min(100, int(round(pct))))

    corpo = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>{_e(assunto)}</title></head>
<body style="margin:0; padding:0; background-color:#f4f6f9;" bgcolor="#f4f6f9">
<table width="100%" cellpadding="0" cellspacing="0" bgcolor="#f4f6f9" style="background-color:#f4f6f9; padding:24px 0;">
<tr><td align="center">
<table width="680" cellpadding="0" cellspacing="0" bgcolor="#ffffff" style="background-color:#ffffff; border-radius:8px; border:1px solid #e5e7eb;">

  <!-- Cabecalho -->
  <tr><td bgcolor="#0a1628" style="background-color:#0a1628; padding:24px 32px;">
    <p style="{_FONTE} color:#ffffff; margin:0; font-size:20px; font-weight:600;">SAP Analytics Cloud</p>
    <p style="{_FONTE} color:#7eb8e0; margin:4px 0 0; font-size:14px;">Relatorio semanal de usuarios inativos</p>
    <p style="{_FONTE} color:#9ca3af; margin:10px 0 0; font-size:12px;">Executado em {c['data_hoje']} as {c['hora']}</p>
  </td></tr>

  <!-- Resumo -->
  <tr><td style="padding:24px 32px 16px;">
    <p style="{_FONTE} font-size:15px; color:#111827; margin:0; line-height:1.6;">{frase}</p>
  </td></tr>

  {status_html}

  <!-- Cards -->
  <tr><td style="padding:0 28px 20px;">
    <table width="100%" cellpadding="0" cellspacing="0"><tr>{cards}</tr></table>
  </td></tr>

  <!-- Barra -->
  <tr><td style="padding:0 32px 20px;">
    <table width="100%" cellpadding="0" cellspacing="0" bgcolor="#f9fafb" style="background-color:#f9fafb; border:1px solid #e5e7eb; border-radius:8px;">
      <tr><td style="padding:12px 16px;">
        <p style="{_FONTE} font-size:12px; color:#6b7280; margin:0 0 8px;">
          <strong style="color:#374151;">Taxa de inatividade:</strong> {pct}% dos usuarios ativos no SAC nao acessam ha mais de {c['dias_inatividade']} dias
        </p>
        <table width="100%" cellpadding="0" cellspacing="0"><tr>
          <td bgcolor="#e5e7eb" style="background-color:#e5e7eb; border-radius:4px; height:8px; font-size:0; line-height:0;">
            <table width="{largura_barra}%" cellpadding="0" cellspacing="0"><tr>
              <td bgcolor="#dc2626" style="background-color:#dc2626; border-radius:4px; height:8px; font-size:0; line-height:0;">&nbsp;</td>
            </tr></table>
          </td>
        </tr></table>
      </td></tr>
    </table>
  </td></tr>

  <!-- Tabela -->
  <tr><td style="padding:0 32px 20px;">
    <p style="{_FONTE} font-size:14px; font-weight:700; color:#111827; margin:0 0 10px;">
      Usuarios inativos{" e resultado da desativacao" if modo_desativacao else ""}
    </p>
    {tabela_html}
  </td></tr>

  {obs_html}

  <!-- Criterio -->
  <tr><td style="padding:0 32px 20px;">
    <p style="{_FONTE} font-size:14px; font-weight:700; color:#111827; margin:0 0 8px;">Como a lista e calculada</p>
    <ul style="{_FONTE} font-size:12px; color:#4b5563; margin:0; padding-left:18px; line-height:1.6;">
      <li>Sao considerados apenas usuarios <strong>habilitados</strong> no SAC (contas ja desativadas nao entram).</li>
      <li>Um usuario e <strong>inativo</strong> quando nao ha nenhuma atividade registrada no log do SAC desde <strong>{c['data_corte']}</strong> ({c['dias_inatividade']} dias).</li>
      <li>"NUNCA ACESSOU" indica que nao ha nenhum registro de atividade para o usuario.</li>
      <li>Usuarios da lista de protecao e contas criadas ha menos de {c['dias_carencia']} dias nunca sao desativados.</li>
      <li>Cada usuario desativado libera 1 licenca. Para reativar, basta habilitar o usuario novamente no SAC.</li>
    </ul>
  </td></tr>

  <!-- Anexos -->
  <tr><td style="padding:0 32px 24px;">
    <p style="{_FONTE} font-size:14px; font-weight:700; color:#111827; margin:0 0 6px;">Anexos</p>
    <p style="{_FONTE} font-size:13px; color:#4b5563; margin:0; line-height:1.8;">{anexos_html}</p>
  </td></tr>

  <!-- Rodape -->
  <tr><td bgcolor="#f9fafb" style="background-color:#f9fafb; padding:14px 32px; border-top:1px solid #e5e7eb; text-align:center;">
    <p style="{_FONTE} font-size:11px; color:#9ca3af; margin:0;">
      Email automatico do SAC User Automation (servidor {_e(c['host'])}). Nao responda a esta mensagem.
    </p>
  </td></tr>

</table>
</td></tr>
</table>
</body>
</html>"""
    return assunto, corpo


def montar_email_erro(etapa, erro, traceback_txt, data_hoje, hora, host=None):
    """Monta assunto e HTML do email de falha da automacao."""
    host = host or socket.gethostname()
    assunto = f"[SAC] ERRO na automacao de usuarios inativos - {data_hoje}"
    corpo = f"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8"></head>
<body style="margin:0; padding:0; background-color:#f4f6f9;" bgcolor="#f4f6f9">
<table width="100%" cellpadding="0" cellspacing="0" style="padding:24px 0;"><tr><td align="center">
<table width="680" cellpadding="0" cellspacing="0" bgcolor="#ffffff" style="background-color:#ffffff; border-radius:8px; border:1px solid #e5e7eb;">
  <tr><td bgcolor="#7f1d1d" style="background-color:#7f1d1d; padding:24px 32px;">
    <p style="{_FONTE} color:#ffffff; margin:0; font-size:20px; font-weight:600;">SAP Analytics Cloud</p>
    <p style="{_FONTE} color:#fecaca; margin:4px 0 0; font-size:14px;">A automacao de usuarios inativos falhou</p>
    <p style="{_FONTE} color:#d1d5db; margin:10px 0 0; font-size:12px;">Executado em {data_hoje} as {hora} no servidor {_e(host)}</p>
  </td></tr>
  <tr><td style="padding:24px 32px 12px;">
    <p style="{_FONTE} font-size:14px; color:#111827; margin:0 0 12px; line-height:1.6;">
      A execucao foi interrompida na etapa <strong>{_e(etapa)}</strong>. Nenhum relatorio foi gerado e nenhum usuario foi
      desativado nesta execucao. Verifique o problema abaixo e execute novamente.
    </p>
    <p style="{_FONTE} font-size:13px; color:#991b1b; margin:0 0 12px;"><strong>Erro:</strong> {_e(erro)}</p>
    <pre style="font-family:Consolas,monospace; font-size:11px; color:#374151; background-color:#f3f4f6; border:1px solid #e5e7eb; border-radius:6px; padding:12px; overflow:auto; white-space:pre-wrap; margin:0;">{_e(traceback_txt)}</pre>
  </td></tr>
  <tr><td style="padding:0 32px 24px;">
    <p style="{_FONTE} font-size:12px; color:#6b7280; margin:0;">
      Causas comuns: credenciais OAuth expiradas ou invalidas (.env), tenant indisponivel, ou mudanca no formato do log de atividades.
    </p>
  </td></tr>
  <tr><td bgcolor="#f9fafb" style="background-color:#f9fafb; padding:14px 32px; border-top:1px solid #e5e7eb; text-align:center;">
    <p style="{_FONTE} font-size:11px; color:#9ca3af; margin:0;">Email automatico do SAC User Automation. Nao responda a esta mensagem.</p>
  </td></tr>
</table>
</td></tr></table>
</body></html>"""
    return assunto, corpo
