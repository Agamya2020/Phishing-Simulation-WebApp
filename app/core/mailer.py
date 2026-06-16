import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.core.config import settings


async def send_email(to_email: str, to_name: str, subject: str, html_body: str):
    """Send an email via SMTP (routes to Mailpit in development)."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"PhishGuard Simulator <simulator@phishguard.io>"
    msg["To"] = f"{to_name} <{to_email}>"

    part = MIMEText(html_body, "html")
    msg.attach(part)

    await aiosmtplib.send(
        msg,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        start_tls=False,
    )
