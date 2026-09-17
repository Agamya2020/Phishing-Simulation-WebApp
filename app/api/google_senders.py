import logging
import secrets

import httpx

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
)
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.core.security import require_admin
from app.core.token_crypto import encrypt_token
from app.models.models import GmailSender
from app.schemas.schemas import (
    GmailSenderOut,
    GmailSenderUpdate,
)


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/google",
    tags=["google-senders"],
    dependencies=[Depends(require_admin)],
)


SCOPES = [
    "openid",
    "email",
    "https://www.googleapis.com/auth/gmail.send",
]


def create_google_flow(
    state: str | None = None,
    code_verifier: str | None = None,
) -> Flow:

    if (
        not settings.GOOGLE_CLIENT_ID
        or not settings.GOOGLE_CLIENT_SECRET
        or not settings.GOOGLE_REDIRECT_URI
    ):
        raise HTTPException(
            status_code=500,
            detail="Google OAuth is not configured.",
        )

    client_config = {
        "web": {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "auth_uri":
                "https://accounts.google.com/o/oauth2/auth",
            "token_uri":
                "https://oauth2.googleapis.com/token",
            "redirect_uris": [
                settings.GOOGLE_REDIRECT_URI
            ],
        }
    }

    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        state=state,
        code_verifier=code_verifier,
        autogenerate_code_verifier=False,
    )

    flow.redirect_uri = (
        settings.GOOGLE_REDIRECT_URI
    )

    return flow


@router.get("/connect")
async def connect_google():

    # Generate our own PKCE verifier.
    # token_urlsafe(64) produces a valid PKCE-safe value.
    code_verifier = secrets.token_urlsafe(64)

    flow = create_google_flow(
        code_verifier=code_verifier,
    )

    authorization_url, state = (
        flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )
    )

    response = RedirectResponse(
        url=authorization_url,
        status_code=302,
    )

    response.set_cookie(
        key="google_oauth_state",
        value=state,
        max_age=600,
        httponly=True,
        secure=True,
        samesite="lax",
    )

    response.set_cookie(
        key="google_oauth_code_verifier",
        value=code_verifier,
        max_age=600,
        httponly=True,
        secure=True,
        samesite="lax",
    )

    return response


@router.get("/callback")
async def google_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    if error:
        raise HTTPException(
            status_code=400,
            detail=f"Google authorization failed: {error}",
        )

    if not code or not state:
        raise HTTPException(
            status_code=400,
            detail="Missing Google authorization response.",
        )

    saved_state = request.cookies.get(
        "google_oauth_state"
    )

    saved_code_verifier = request.cookies.get(
        "google_oauth_code_verifier"
    )

    if (
        not saved_state
        or not secrets.compare_digest(
            saved_state,
            state,
        )
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid Google OAuth state.",
        )

    if not saved_code_verifier:
        raise HTTPException(
            status_code=400,
            detail="Missing Google OAuth code verifier.",
        )

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "code": code,
                    "code_verifier": saved_code_verifier,
                    "grant_type": "authorization_code",
                    "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                },
            )

        if token_response.status_code != 200:
            logger.error(
                "Google OAuth token exchange failed: status=%s body=%s",
                token_response.status_code,
                token_response.text,
            )

            raise HTTPException(
                status_code=400,
                detail="Unable to exchange Google authorization code.",
            )

        token_data = token_response.json()

        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")

        if not access_token:
            raise HTTPException(
                status_code=400,
                detail="Google did not return an access token.",
            )

    except HTTPException:
        raise

    except Exception as exc:
        logger.exception(
            "Google OAuth token exchange failed: %s",
            exc,
        )

        raise HTTPException(
            status_code=400,
            detail="Unable to exchange Google authorization code.",
        ) from exc

    # Obtain the identity of the Google account
    # that actually granted permission.
    try:
        async with httpx.AsyncClient(
            timeout=20.0
        ) as client:

            profile_response = await client.get(
                (
                    "https://openidconnect."
                    "googleapis.com/v1/userinfo"
                ),
                headers={
                    "Authorization":
                        f"Bearer {access_token}"
                },
            )

            profile_response.raise_for_status()

            profile = profile_response.json()

    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                "Unable to retrieve the connected "
                "Google account."
            ),
        ) from exc

    email = str(
        profile.get("email") or ""
    ).lower().strip()

    google_subject_id = str(
        profile.get("sub") or ""
    ).strip()

    email_verified = bool(
        profile.get("email_verified")
    )

    if (
        not email
        or not google_subject_id
        or not email_verified
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Google did not return a verified "
                "email identity."
            ),
        )

    result = await db.execute(
        select(GmailSender).where(
            or_(
                GmailSender.email == email,
                GmailSender.google_subject_id
                == google_subject_id,
            )
        )
    )

    sender = result.scalar_one_or_none()

    if sender:
        # Reconnecting an existing account.
        sender.email = email
        sender.google_subject_id = (
            google_subject_id
        )
        sender.is_active = True

        if refresh_token:
            sender.encrypted_refresh_token = (
                encrypt_token(refresh_token)
            )

    else:
        if not refresh_token:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Google did not return a refresh "
                    "token. Reconnect the account "
                    "and grant consent."
                ),
            )

        sender = GmailSender(
            email=email,
            display_name=email,
            google_subject_id=google_subject_id,
            encrypted_refresh_token=(
                encrypt_token(refresh_token)
            ),
            is_active=True,
        )

        db.add(sender)

    await db.commit()
    await db.refresh(sender)

    response = RedirectResponse(
        url="/admin/senders?gmail=connected",
        status_code=302,
    )

    response.delete_cookie(
        "google_oauth_state"
    )

    response.delete_cookie(
        "google_oauth_code_verifier"
    )

    return response


@router.get(
    "/senders",
    response_model=list[GmailSenderOut],
)
async def list_gmail_senders(
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(GmailSender)
        .order_by(GmailSender.created_at.desc())
    )

    return result.scalars().all()


@router.patch(
    "/senders/{sender_id}",
    response_model=GmailSenderOut,
)
async def update_gmail_sender(
    sender_id: int,
    payload: GmailSenderUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(GmailSender)
        .where(GmailSender.id == sender_id)
    )

    sender = result.scalar_one_or_none()

    if not sender:
        raise HTTPException(
            status_code=404,
            detail="Gmail sender not found.",
        )

    values = payload.model_dump(
        exclude_none=True
    )

    for field, value in values.items():
        setattr(sender, field, value)

    await db.commit()
    await db.refresh(sender)

    return sender


@router.delete("/senders/{sender_id}")
async def disconnect_gmail_sender(
    sender_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(GmailSender)
        .where(GmailSender.id == sender_id)
    )

    sender = result.scalar_one_or_none()

    if not sender:
        raise HTTPException(
            status_code=404,
            detail="Gmail sender not found.",
        )

    sender.is_active = False

    # Remove access to the stored Google authorization
    # while preserving the sender row for historical campaigns.
    sender.encrypted_refresh_token = ""

    await db.commit()

    return {
        "ok": True,
        "message": "Gmail sender disconnected.",
    }
