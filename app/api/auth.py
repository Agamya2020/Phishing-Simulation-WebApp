import secrets
import time
from collections import defaultdict, deque

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel

from app.core.config import settings
from app.core.security import (
    ACCESS_COOKIE_NAME,
    CSRF_COOKIE_NAME,
    create_access_token,
    require_admin,
)


router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)

LOGIN_WINDOW_SECONDS = 15 * 60
LOGIN_MAX_ATTEMPTS = 5

login_attempts: dict[str, deque[float]] = defaultdict(deque)


class LoginRequest(BaseModel):
    username: str
    password: str


def client_identifier(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()

    if request.client:
        return request.client.host

    return "unknown"


def check_login_limit(identifier: str) -> None:
    now = time.time()
    attempts = login_attempts[identifier]

    while attempts and attempts[0] < now - LOGIN_WINDOW_SECONDS:
        attempts.popleft()

    if len(attempts) >= LOGIN_MAX_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Try again later.",
        )


def record_failed_login(identifier: str) -> None:
    login_attempts[identifier].append(time.time())


def clear_login_attempts(identifier: str) -> None:
    login_attempts.pop(identifier, None)


@router.post("/login")
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
):
    identifier = client_identifier(request)
    check_login_limit(identifier)

    username_valid = secrets.compare_digest(
        payload.username,
        settings.ADMIN_USERNAME,
    )
    password_valid = secrets.compare_digest(
        payload.password,
        settings.ADMIN_PASSWORD,
    )

    if not (username_valid and password_valid):
        record_failed_login(identifier)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    clear_login_attempts(identifier)

    access_token = create_access_token(payload.username)
    csrf_token = secrets.token_urlsafe(32)
    production = settings.APP_ENV.lower() == "production"
    max_age = settings.JWT_EXPIRE_MINUTES * 60

    response.set_cookie(
        key=ACCESS_COOKIE_NAME,
        value=access_token,
        httponly=True,
        secure=production,
        samesite="lax",
        max_age=max_age,
        path="/",
    )
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf_token,
        httponly=False,
        secure=production,
        samesite="lax",
        max_age=max_age,
        path="/",
    )

    return {
        "authenticated": True,
        "username": payload.username,
    }


@router.get("/me")
async def current_admin(username: str = Depends(require_admin)):
    return {
        "authenticated": True,
        "username": username,
    }


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(ACCESS_COOKIE_NAME, path="/")
    response.delete_cookie(CSRF_COOKIE_NAME, path="/")

    return {"message": "Logged out successfully"}
