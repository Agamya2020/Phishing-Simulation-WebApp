import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.core.config import settings


async def send_email(
    to_email: str,
    to_name: str,
    subject: str,
    html_body: str,
    sender: str | None = None,
):
    """Send an email via SMTP (routes to Mailpit in development)."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender or "PhishGuard Simulator <simulator@phishguard.io>"
    msg["To"] = f"{to_name} <{to_email}>"

    part = MIMEText(html_body, "html")
    msg.attach(part)

    send_options = {
        "hostname": settings.SMTP_HOST,
        "port": settings.SMTP_PORT,
        "start_tls": settings.SMTP_USE_TLS,
    }
    if settings.SMTP_USERNAME:
        send_options["username"] = settings.SMTP_USERNAME
    if settings.SMTP_PASSWORD:
        send_options["password"] = settings.SMTP_PASSWORD

    await aiosmtplib.send(msg, **send_options)
