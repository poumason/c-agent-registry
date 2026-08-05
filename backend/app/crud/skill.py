import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.skill import Skill


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
