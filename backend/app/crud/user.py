import secrets
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.enums import UserRole, UserStatus
from app.models.user import User


async def get_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    return await db.get(User, user_id)


async def get_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def list_users(db: AsyncSession) -> list[User]:
    result = await db.execute(select(User).order_by(User.created_at))
    return list(result.scalars().all())


async def count_admins(db: AsyncSession) -> int:
    result = await db.execute(select(User).where(User.role == UserRole.admin))
    return len(result.scalars().all())


async def list_by_roles(db: AsyncSession, roles: list[UserRole]) -> list[User]:
    result = await db.execute(
        select(User).where(User.role.in_(roles), User.status == UserStatus.active)
    )
    return list(result.scalars().all())


async def create_user(
    db: AsyncSession,
    *,
    email: str,
    password: str,
    name: str,
    role: UserRole = UserRole.member,
    status: UserStatus = UserStatus.active,
) -> User:
    user = User(
        email=email,
        hashed_password=hash_password(password),
        name=name,
        role=role,
        status=status,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_or_create_by_sso(db: AsyncSession, *, email: str, name: str) -> User:
    """Looks up a user by email for SSO login; auto-provisions with role=member if new.

    Never touches role/status of an existing user - SSO only authenticates, it doesn't
    grant permissions.
    """
    existing = await get_by_email(db, email)
    if existing is not None:
        return existing
    return await create_user(
        db,
        email=email,
        password=secrets.token_urlsafe(32),
        name=name,
        role=UserRole.member,
        status=UserStatus.active,
    )


async def update_user(
    db: AsyncSession,
    user: User,
    *,
    name: str | None = None,
    role: UserRole | None = None,
    status: UserStatus | None = None,
    password: str | None = None,
) -> User:
    if name is not None:
        user.name = name
    if role is not None:
        user.role = role
    if status is not None:
        user.status = status
    if password is not None:
        user.hashed_password = hash_password(password)
    await db.commit()
    await db.refresh(user)
    return user
