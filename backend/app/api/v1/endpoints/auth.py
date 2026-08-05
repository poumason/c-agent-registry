from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.deps import get_current_user
from app.core.security import create_access_token, decode_sso_state_token, verify_password
from app.crud import user as user_crud
from app.db.base import get_db
from app.models.enums import UserStatus
from app.models.user import User
from app.schemas.user import Token, UserRead
from app.services import sso

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Token:
    user = await user_crud.get_by_email(db, form_data.username)
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.status != UserStatus.active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is disabled")
    return Token(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserRead)
async def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.get("/sso/login")
async def sso_login() -> RedirectResponse:
    """Redirects to the configured OIDC provider. Password login (above) is unaffected
    and always stays available regardless of SSO configuration."""
    try:
        url = await sso.build_authorization_url()
    except sso.SsoNotConfigured as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    return RedirectResponse(url)


@router.get("/sso/callback", response_model=None)
async def sso_callback(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
) -> Token | RedirectResponse:
    state_payload = decode_sso_state_token(state)
    if state_payload is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired SSO state"
        )

    try:
        claims = await sso.exchange_code(
            code=code,
            code_verifier=state_payload["code_verifier"],
            nonce=state_payload["nonce"],
        )
    except sso.SsoNotConfigured as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    except sso.SsoError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    user = await user_crud.get_or_create_by_sso(db, email=claims.email, name=claims.name)
    if user.status != UserStatus.active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is disabled")

    access_token = create_access_token(user.id)
    if settings.frontend_sso_redirect_url:
        target = (
            f"{settings.frontend_sso_redirect_url}#access_token={access_token}&token_type=bearer"
        )
        return RedirectResponse(target)
    return Token(access_token=access_token)
