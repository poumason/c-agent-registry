import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent
from app.models.enums import AgentVisibility


async def get_by_id(db: AsyncSession, agent_id: uuid.UUID) -> Agent | None:
    return await db.get(Agent, agent_id)


async def get_by_slug(db: AsyncSession, slug: str) -> Agent | None:
    result = await db.execute(select(Agent).where(Agent.slug == slug))
    return result.scalar_one_or_none()


async def list_agents(db: AsyncSession) -> list[Agent]:
    result = await db.execute(select(Agent).order_by(Agent.created_at))
    return list(result.scalars().all())


async def create_agent(
    db: AsyncSession,
    *,
    slug: str,
    name: str,
    description: str | None,
    provider: str | None,
    visibility: AgentVisibility,
    created_by: uuid.UUID,
) -> Agent:
    agent = Agent(
        slug=slug,
        name=name,
        description=description,
        provider=provider,
        visibility=visibility,
        created_by=created_by,
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return agent
