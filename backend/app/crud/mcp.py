import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import AvailabilityStatus
from app.models.mcp import MCP
from app.models.mcp_fab import MCPFab


async def get_by_id(db: AsyncSession, mcp_id: uuid.UUID) -> MCP | None:
    return await db.get(MCP, mcp_id)


async def list_mcps(db: AsyncSession) -> list[MCP]:
    result = await db.execute(select(MCP).order_by(MCP.created_at))
    return list(result.scalars().all())


async def create_mcp(
    db: AsyncSession,
    *,
    name: str,
    version: str,
    description: str | None,
    category: str | None,
    tags: list[str],
    created_by: uuid.UUID,
) -> MCP:
    """Internal/test seeding only — there's no longer a public create endpoint for
    this (MCPs are meant to arrive via sync; see docs/registry-sync.md). Kept here so
    tests and any future admin tooling can still create a catalog row directly."""
    mcp = MCP(
        name=name,
        version=version,
        description=description,
        category=category,
        tags=tags,
        created_by=created_by,
    )
    db.add(mcp)
    await db.commit()
    await db.refresh(mcp)
    return mcp


async def list_mcp_fabs_for_mcp(db: AsyncSession, mcp_id: uuid.UUID) -> list[MCPFab]:
    result = await db.execute(
        select(MCPFab).where(MCPFab.mcp_id == mcp_id).order_by(MCPFab.created_at)
    )
    return list(result.scalars().all())


async def list_all_mcp_fabs(db: AsyncSession) -> list[MCPFab]:
    result = await db.execute(select(MCPFab).order_by(MCPFab.created_at))
    return list(result.scalars().all())


async def get_mcp_fab(db: AsyncSession, mcp_id: uuid.UUID, fab_id: uuid.UUID) -> MCPFab | None:
    return await db.get(MCPFab, {"mcp_id": mcp_id, "fab_id": fab_id})


async def create_mcp_fab(
    db: AsyncSession, *, mcp_id: uuid.UUID, fab_id: uuid.UUID, host: str
) -> MCPFab:
    mcp_fab = MCPFab(mcp_id=mcp_id, fab_id=fab_id, host=host)
    db.add(mcp_fab)
    await db.commit()
    await db.refresh(mcp_fab)
    return mcp_fab


def mark_fab_synced(mcp_fab: MCPFab, status: AvailabilityStatus) -> None:
    """Set status + last_synced_at on the in-session object. Caller commits once for the batch."""
    mcp_fab.status = status
    mcp_fab.last_synced_at = datetime.now(timezone.utc)


async def remove_mcp_fab(db: AsyncSession, mcp_fab: MCPFab) -> None:
    await db.delete(mcp_fab)
    await db.commit()
