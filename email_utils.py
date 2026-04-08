import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
import os


def enviar_relatorio(smtp_host, smtp_port, email_from, destinatarios, assunto, corpo_html, anexos=None):
    """Envia email com anexos via SMTP."""
    msg = MIMEMultipart()
    msg["From"] = email_from
    msg["To"] = ", ".join(destinatarios)
    msg["Subject"] = assunto
    msg.attach(MIMEText(corpo_html, "html"))

    for caminho in (anexos or []):
        if not os.path.exists(caminho):
            continue
        with open(caminho, "rb") as f:
            parte = MIMEBase("application", "octet-stream")
            parte.set_payload(f.read())
        encoders.encode_base64(parte)
        parte.add_header("Content-Disposition", f"attachment; filename={os.path.basename(caminho)}")
        msg.attach(parte)

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.sendmail(email_from, destinatarios, msg.as_string())

    print(f"Email enviado para: {', '.join(destinatarios)}")
