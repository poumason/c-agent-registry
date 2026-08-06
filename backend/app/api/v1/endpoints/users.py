import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_role
from app.crud import user as user_crud
from app.db.base import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.user import UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])

admin_only = require_role(UserRole.admin)


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
    _: object = Depends(admin_only),
) -> UserRead:
    existing = await user_crud.get_by_email(db, payload.email)
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")
    user = await user_crud.create_user(
        db,
        email=payload.email,
        password=payload.password,
        name=payload.name,
        role=payload.role,
        status=payload.status,
    )
    return UserRead.model_validate(user)


@router.get("", response_model=list[UserRead])
async def list_users(
    db: AsyncSession = Depends(get_db),
    _: object = Depends(admin_only),
) -> list[UserRead]:
    users = await user_crud.list_users(db)
    return [UserRead.model_validate(u) for u in users]


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
    _: object = Depends(admin_only),
) -> UserRead:
    user = await user_crud.get_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user = await user_crud.update_user(
        db,
        user,
        name=payload.name,
        role=payload.role,
        status=payload.status,
        password=payload.password,
    )
    return UserRead.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(admin_only),
) -> None:
    if user_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Cannot delete your own account"
        )
    user = await user_crud.get_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    await user_crud.soft_delete(db, user)
