from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


def _fernet() -> Fernet:
    if not settings.TOKEN_ENCRYPTION_KEY:
        raise RuntimeError(
            "TOKEN_ENCRYPTION_KEY is not configured"
        )

    return Fernet(
        settings.TOKEN_ENCRYPTION_KEY.encode()
    )


def encrypt_token(token: str) -> str:
    return (
        _fernet()
        .encrypt(token.encode())
        .decode()
    )


def decrypt_token(token: str) -> str:
    try:
        return (
            _fernet()
            .decrypt(token.encode())
            .decode()
        )

    except InvalidToken as exc:
        raise RuntimeError(
            "Unable to decrypt stored Google token"
        ) from exc
