import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_fab import AgentFab


async def list_for_version(db: AsyncSession, agent_version_slug: str) -> list[AgentFab]:
    result = await db.execute(
        select(AgentFab)
        .where(AgentFab.agent_version_slug == agent_version_slug)
        .order_by(AgentFab.created_at)
    )
    return list(result.scalars().all())


async def replace_for_version(
    db: AsyncSession, agent_version_slug: str, entries: list[tuple[uuid.UUID, str]]
) -> list[AgentFab]:
    """Replace-all: deletes every existing row for this version, then inserts the
    given (fab_id, url) set. Matches the deploy-to-fabs panel's single-save-button
    UX — the panel always submits its full current state, not a diff."""
    await db.execute(delete(AgentFab).where(AgentFab.agent_version_slug == agent_version_slug))
    rows = [
        AgentFab(fab_id=fab_id, agent_version_slug=agent_version_slug, url=url)
        for fab_id, url in entries
    ]
    db.add_all(rows)
    await db.commit()
    return await list_for_version(db, agent_version_slug)
