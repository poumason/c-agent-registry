import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_version import AgentVersion
from app.models.enums import VersionStatus


async def get_by_slug(db: AsyncSession, slug: str) -> AgentVersion | None:
    return await db.get(AgentVersion, slug)


async def list_by_agent(db: AsyncSession, agent_id: uuid.UUID) -> list[AgentVersion]:
    result = await db.execute(
        select(AgentVersion)
        .where(AgentVersion.agent_id == agent_id)
        .order_by(AgentVersion.version)
    )
    return list(result.scalars().all())


async def next_version_number(db: AsyncSession, agent_id: uuid.UUID) -> int:
    result = await db.execute(
        select(func.max(AgentVersion.version)).where(AgentVersion.agent_id == agent_id)
    )
    current_max = result.scalar_one_or_none()
    return (current_max or 0) + 1


async def count_active(db: AsyncSession, agent_id: uuid.UUID) -> int:
    result = await db.execute(
        select(func.count())
        .select_from(AgentVersion)
        .where(
            AgentVersion.agent_id == agent_id, AgentVersion.status == VersionStatus.active
        )
    )
    return int(result.scalar_one())


async def create_version(
    db: AsyncSession,
    *,
    slug: str,
    agent_id: uuid.UUID,
    version: int,
    url: str | None,
    streaming: bool,
    default_input_modes: list[str],
    default_output_modes: list[str],
    created_by: uuid.UUID,
) -> AgentVersion:
    agent_version = AgentVersion(
        slug=slug,
        agent_id=agent_id,
        version=version,
        url=url,
        streaming=streaming,
        default_input_modes=default_input_modes,
        default_output_modes=default_output_modes,
        status=VersionStatus.draft,
        created_by=created_by,
        updated_by=created_by,
    )
    db.add(agent_version)
    await db.commit()
    await db.refresh(agent_version)
    return agent_version


async def save(db: AsyncSession, agent_version: AgentVersion) -> AgentVersion:
    await db.commit()
    await db.refresh(agent_version)
    return agent_version
