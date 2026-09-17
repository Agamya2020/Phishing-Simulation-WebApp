import asyncio
import base64

from email.message import EmailMessage
from email.utils import formataddr

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.core.config import settings
from app.core.token_crypto import decrypt_token
from app.models.models import GmailSender


GMAIL_SEND_SCOPE = (
    "https://www.googleapis.com/auth/gmail.send"
)

GOOGLE_TOKEN_URI = (
    "https://oauth2.googleapis.com/token"
)


def _send_gmail_sync(
    gmail_sender: GmailSender,
    to_email: str,
    to_name: str,
    subject: str,
    html_body: str,
):
    if (
        not settings.GOOGLE_CLIENT_ID
        or not settings.GOOGLE_CLIENT_SECRET
    ):
        raise RuntimeError(
            "Google OAuth credentials are not configured"
        )

    refresh_token = decrypt_token(
        gmail_sender.encrypted_refresh_token
    )

    credentials = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri=GOOGLE_TOKEN_URI,
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=[GMAIL_SEND_SCOPE],
    )

    credentials.refresh(Request())

    message = EmailMessage()

    if to_name:
        message["To"] = formataddr(
            (to_name, to_email)
        )
    else:
        message["To"] = to_email

    sender_name = (
        gmail_sender.display_name
        or gmail_sender.email
    )

    message["From"] = formataddr(
        (
            sender_name,
            gmail_sender.email,
        )
    )

    message["Subject"] = subject

    message.set_content(
        "This message contains HTML content."
    )

    message.add_alternative(
        html_body,
        subtype="html",
    )

    encoded_message = (
        base64.urlsafe_b64encode(
            message.as_bytes()
        )
        .decode()
    )

    service = build(
        "gmail",
        "v1",
        credentials=credentials,
        cache_discovery=False,
    )

    result = (
        service.users()
        .messages()
        .send(
            userId="me",
            body={
                "raw": encoded_message
            },
        )
        .execute()
    )

    return result


async def send_gmail_email(
    gmail_sender: GmailSender,
    to_email: str,
    to_name: str,
    subject: str,
    html_body: str,
):
    """
    Send mail using the Gmail account that explicitly
    authorized PhishGuard through Google OAuth.
    """

    return await asyncio.to_thread(
        _send_gmail_sync,
        gmail_sender,
        to_email,
        to_name,
        subject,
        html_body,
    )
