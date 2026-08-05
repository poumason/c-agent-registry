import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_dependency import AgentDependency
from app.models.enums import DependencyType


async def list_by_version(db: AsyncSession, agent_slug: str) -> list[AgentDependency]:
    result = await db.execute(
        select(AgentDependency).where(AgentDependency.agent_slug == agent_slug)
    )
    return list(result.scalars().all())


async def get_by_id(db: AsyncSession, dependency_row_id: uuid.UUID) -> AgentDependency | None:
    return await db.get(AgentDependency, dependency_row_id)


async def create_dependency(
    db: AsyncSession, *, agent_slug: str, dependency_id: uuid.UUID, type: DependencyType
) -> AgentDependency:
    dependency = AgentDependency(agent_slug=agent_slug, dependency_id=dependency_id, type=type)
    db.add(dependency)
    await db.commit()
    await db.refresh(dependency)
    return dependency


async def remove_dependency(db: AsyncSession, dependency: AgentDependency) -> None:
    await db.delete(dependency)
    await db.commit()
