from datetime import datetime, timedelta, timezone
from secrets import compare_digest

from fastapi import Depends, HTTPException, Request, status
from jose import JWTError, jwt

from app.core.config import settings


ACCESS_COOKIE_NAME = "phishguard_session"
CSRF_COOKIE_NAME = "phishguard_csrf"


def create_access_token(username: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": username,
        "exp": now + timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
        "iat": now,
        "type": "admin",
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def verify_access_token(token: str) -> str:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        username = payload.get("sub")
        token_type = payload.get("type")

        if (
            not username
            or token_type != "admin"
            or username != settings.ADMIN_USERNAME
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
            )

        return username
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        ) from exc


def get_session_token(request: Request) -> str | None:
    return request.cookies.get(ACCESS_COOKIE_NAME)


async def require_admin(request: Request) -> str:
    token = get_session_token(request)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    return verify_access_token(token)


async def require_admin_page(request: Request) -> str:
    token = get_session_token(request)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/admin/login"},
        )

    try:
        return verify_access_token(token)
    except HTTPException as exc:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/admin/login"},
        ) from exc


async def require_csrf(
    request: Request,
    _: str = Depends(require_admin),
) -> None:
    csrf_cookie = request.cookies.get(CSRF_COOKIE_NAME)
    csrf_header = request.headers.get("X-CSRF-Token")

    if not csrf_cookie or not csrf_header:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF validation failed",
        )

    if not compare_digest(csrf_cookie, csrf_header):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF validation failed",
        )
