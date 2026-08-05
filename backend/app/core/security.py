import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: uuid.UUID) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {"sub": str(subject), "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> uuid.UUID | None:
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
    except JWTError:
        return None
    sub = payload.get("sub")
    if sub is None:
        return None
    try:
        return uuid.UUID(sub)
    except ValueError:
        return None


SSO_STATE_PURPOSE = "sso_state"
SSO_STATE_EXPIRE_MINUTES = 5


def create_sso_state_token(*, nonce: str, code_verifier: str, redirect_after: str = "") -> str:
    """Encodes the OIDC `state` param so we don't need server-side session storage.

    Carries a distinct `purpose` claim so a real access token can never be replayed here
    (or vice versa).
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=SSO_STATE_EXPIRE_MINUTES)
    payload = {
        "purpose": SSO_STATE_PURPOSE,
        "nonce": nonce,
        "code_verifier": code_verifier,
        "redirect_after": redirect_after,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_sso_state_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
    except JWTError:
        return None
    if payload.get("purpose") != SSO_STATE_PURPOSE:
        return None
    if "nonce" not in payload or "code_verifier" not in payload:
        return None
    return payload
