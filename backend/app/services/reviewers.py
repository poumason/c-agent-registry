from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import user as user_crud
from app.models.enums import UserRole
from app.models.user import User


async def list_reviewer_candidates(db: AsyncSession) -> list[User]:
    """Active users eligible to be assigned as a reviewer at submit time."""
    return await user_crud.list_by_roles(db, [UserRole.reviewer, UserRole.admin])
