import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_dependency import AgentDependency
from app.models.enums import DependencySource, DependencyType


async def list_by_version(db: AsyncSession, agent_slug: str) -> list[AgentDependency]:
    result = await db.execute(
        select(AgentDependency).where(AgentDependency.agent_slug == agent_slug)
    )
    return list(result.scalars().all())


async def get_by_id(db: AsyncSession, dependency_row_id: uuid.UUID) -> AgentDependency | None:
    return await db.get(AgentDependency, dependency_row_id)


async def get_existing(
    db: AsyncSession,
    *,
    agent_slug: str,
    dependency_id: str,
    type: DependencyType,
    source: DependencySource,
    fab_id: uuid.UUID | None,
) -> AgentDependency | None:
    """Look up a row matching the full uq_agent_dependency key, including a NULL
    fab_id — the DB's UNIQUE constraint treats NULLs as distinct from each other,
    so it won't catch a duplicate fab-agnostic row on its own; callers must check
    this before create_dependency."""
    result = await db.execute(
        select(AgentDependency).where(
            AgentDependency.agent_slug == agent_slug,
            AgentDependency.dependency_id == dependency_id,
            AgentDependency.type == type,
            AgentDependency.source == source,
            AgentDependency.fab_id == fab_id,
        )
    )
    return result.scalar_one_or_none()


async def create_dependency(
    db: AsyncSession,
    *,
    agent_slug: str,
    dependency_id: str,
    type: DependencyType,
    source: DependencySource = DependencySource.legacy,
    fab_id: uuid.UUID | None = None,
) -> AgentDependency:
    dependency = AgentDependency(
        agent_slug=agent_slug,
        dependency_id=dependency_id,
        type=type,
        source=source,
        fab_id=fab_id,
    )
    db.add(dependency)
    await db.commit()
    await db.refresh(dependency)
    return dependency


async def remove_dependency(db: AsyncSession, dependency: AgentDependency) -> None:
    await db.delete(dependency)
    await db.commit()
