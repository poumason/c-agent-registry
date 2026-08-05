import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import AssetRole
from app.models.user_agent_rel import UserAgentRel


async def get_membership(
    db: AsyncSession, user_id: uuid.UUID, agent_id: uuid.UUID
) -> UserAgentRel | None:
    result = await db.execute(
        select(UserAgentRel).where(
            UserAgentRel.user_id == user_id, UserAgentRel.agent_id == agent_id
        )
    )
    return result.scalar_one_or_none()


async def list_members(db: AsyncSession, agent_id: uuid.UUID) -> list[UserAgentRel]:
    result = await db.execute(
        select(UserAgentRel).where(UserAgentRel.agent_id == agent_id)
    )
    return list(result.scalars().all())


async def upsert_membership(
    db: AsyncSession, *, user_id: uuid.UUID, agent_id: uuid.UUID, role: AssetRole
) -> UserAgentRel:
    membership = await get_membership(db, user_id, agent_id)
    if membership is None:
        membership = UserAgentRel(user_id=user_id, agent_id=agent_id, role=role)
        db.add(membership)
    else:
        membership.role = role
    await db.commit()
    await db.refresh(membership)
    return membership


async def remove_membership(db: AsyncSession, membership: UserAgentRel) -> None:
    await db.delete(membership)
    await db.commit()
