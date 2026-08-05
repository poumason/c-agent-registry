from collections.abc import Callable, Sequence

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.crud import user as user_crud
from app.db.base import get_db
from app.models.enums import UserRole, UserStatus
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    user_id = decode_access_token(token)
    if user_id is None:
        raise credentials_error
    user = await user_crud.get_by_id(db, user_id)
    if user is None:
        raise credentials_error
    if user.status != UserStatus.active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is disabled")
    return user


def require_role(*roles: UserRole) -> Callable:
    async def _checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {[r.value for r in roles]}",
            )
        return current_user

    return _checker


def require_any_role(roles: Sequence[UserRole]) -> Callable:
    return require_role(*roles)
