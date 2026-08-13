import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import AvailabilityStatus
from app.models.skill import Skill
from app.models.skill_fab import SkillFab


async def get_by_id(db: AsyncSession, skill_id: uuid.UUID) -> Skill | None:
    return await db.get(Skill, skill_id)


async def list_skills(db: AsyncSession) -> list[Skill]:
    result = await db.execute(select(Skill).order_by(Skill.created_at))
    return list(result.scalars().all())


async def create_skill(
    db: AsyncSession,
    *,
    id: uuid.UUID,
    name: str,
    version: str,
    description: str | None,
    category: str | None,
    tags: list[str],
    created_by: uuid.UUID,
    bucket_path: str,
    mcp_dependency: list[uuid.UUID],
) -> Skill:
    skill = Skill(
        id=id,
        name=name,
        version=version,
        description=description,
        category=category,
        tags=tags,
        created_by=created_by,
        bucket_path=bucket_path,
        mcp_dependency=mcp_dependency,
    )
    db.add(skill)
    await db.commit()
    await db.refresh(skill)
    return skill


def mark_synced(skill: Skill, status: AvailabilityStatus) -> None:
    """Set status + last_synced_at on the in-session object. Caller commits once for the batch."""
    skill.status = status
    skill.last_synced_at = datetime.now(timezone.utc)


async def list_skill_fabs_for_skill(db: AsyncSession, skill_id: uuid.UUID) -> list[SkillFab]:
    result = await db.execute(
        select(SkillFab).where(SkillFab.skill_id == skill_id).order_by(SkillFab.created_at)
    )
    return list(result.scalars().all())


async def list_all_skill_fabs(db: AsyncSession) -> list[SkillFab]:
    result = await db.execute(select(SkillFab).order_by(SkillFab.created_at))
    return list(result.scalars().all())


async def get_skill_fab(db: AsyncSession, skill_id: uuid.UUID, fab_id: uuid.UUID) -> SkillFab | None:
    return await db.get(SkillFab, {"skill_id": skill_id, "fab_id": fab_id})


async def create_skill_fab(db: AsyncSession, *, skill_id: uuid.UUID, fab_id: uuid.UUID) -> SkillFab:
    skill_fab = SkillFab(skill_id=skill_id, fab_id=fab_id)
    db.add(skill_fab)
    await db.commit()
    await db.refresh(skill_fab)
    return skill_fab


async def remove_skill_fab(db: AsyncSession, skill_fab: SkillFab) -> None:
    await db.delete(skill_fab)
    await db.commit()
