import uuid
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.crud import mcp as mcp_crud
from app.db.base import get_db
from app.models.enums import AvailabilityStatus
from app.models.mcp import MCP
from app.models.mcp_fab import MCPFab
from app.models.user import User
from app.schemas.mcp import (
    MCPFabCreate,
    MCPFabRead,
    MCPFabSyncItem,
    MCPRead,
    MCPSyncMcpItem,
    MCPSyncResult,
)

router = APIRouter(prefix="/mcps", tags=["mcps"])


async def _check_reachable(host: str) -> bool:
    """Best-effort heuristic: probe http(s) hosts with a short-timeout HEAD request. Any
    response (even 4xx/5xx) counts as reachable. Non-http(s) hosts (e.g. stdio commands)
    can't be verified over the network, so they're assumed available rather than flagged.
    """
    if not host.startswith("http://") and not host.startswith("https://"):
        return True
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            await client.head(host)
        return True
    except httpx.RequestError:
        return False


def _group_fabs_by_mcp(fabs: list[MCPFab]) -> dict[uuid.UUID, list[MCPFab]]:
    grouped: dict[uuid.UUID, list[MCPFab]] = {}
    for f in fabs:
        grouped.setdefault(f.mcp_id, []).append(f)
    return grouped


def _to_read(mcp: MCP, fabs: list[MCPFab]) -> MCPRead:
    return MCPRead(
        id=mcp.id,
        name=mcp.name,
        version=mcp.version,
        description=mcp.description,
        category=mcp.category,
        tags=mcp.tags,
        created_by=mcp.created_by,
        created_at=mcp.created_at,
        updated_at=mcp.updated_at,
        fabs=[MCPFabRead.model_validate(f) for f in fabs],
    )


@router.get("", response_model=list[MCPRead])
async def list_mcps(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[MCPRead]:
    mcps = await mcp_crud.list_mcps(db)
    fabs_by_mcp = _group_fabs_by_mcp(await mcp_crud.list_all_mcp_fabs(db))
    return [_to_read(m, fabs_by_mcp.get(m.id, [])) for m in mcps]


@router.post("/{mcp_id}/fabs", response_model=MCPFabRead, status_code=status.HTTP_201_CREATED)
async def assign_mcp_fab(
    mcp_id: uuid.UUID,
    payload: MCPFabCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MCPFabRead:
    """Deploy an existing MCP into a fab, at the given host. This is not the removed
    "create a new MCP" flow — it attaches a per-fab deployment to an MCP that already
    exists in the catalog (see docs/registry-sync.md for how catalog rows arrive)."""
    if await mcp_crud.get_by_id(db, mcp_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MCP not found")
    if await mcp_crud.get_mcp_fab(db, mcp_id, payload.fab_id) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="MCP already deployed to this fab"
        )
    mcp_fab = await mcp_crud.create_mcp_fab(
        db, mcp_id=mcp_id, fab_id=payload.fab_id, host=payload.host
    )
    return MCPFabRead.model_validate(mcp_fab)


@router.get("/{mcp_id}/fabs", response_model=list[MCPFabRead])
async def list_mcp_fabs(
    mcp_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[MCPFabRead]:
    fabs = await mcp_crud.list_mcp_fabs_for_mcp(db, mcp_id)
    return [MCPFabRead.model_validate(f) for f in fabs]


@router.delete("/{mcp_id}/fabs/{fab_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_mcp_fab(
    mcp_id: uuid.UUID,
    fab_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    mcp_fab = await mcp_crud.get_mcp_fab(db, mcp_id, fab_id)
    if mcp_fab is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    await mcp_crud.remove_mcp_fab(db, mcp_fab)


@router.post("/sync", response_model=MCPSyncResult)
async def sync_mcps(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MCPSyncResult:
    """Re-probes every (mcp, fab) deployment's own host and refreshes its status —
    availability is per-fab now, not per-MCP (see MCPFab). `changed` on each returned
    fab row is true when this run flipped its status, so the frontend can highlight
    exactly what this sync touched rather than the whole (mostly unchanged) list.
    """
    mcp_fabs = await mcp_crud.list_all_mcp_fabs(db)
    changed_keys: set[tuple[uuid.UUID, uuid.UUID]] = set()
    for mcp_fab in mcp_fabs:
        previous_status = mcp_fab.status
        reachable = await _check_reachable(mcp_fab.host)
        new_status = AvailabilityStatus.available if reachable else AvailabilityStatus.unavailable
        mcp_crud.mark_fab_synced(mcp_fab, new_status)
        if new_status != previous_status:
            changed_keys.add((mcp_fab.mcp_id, mcp_fab.fab_id))
    await db.commit()
    for mcp_fab in mcp_fabs:
        await db.refresh(mcp_fab)

    mcps = await mcp_crud.list_mcps(db)
    fabs_by_mcp = _group_fabs_by_mcp(mcp_fabs)

    items = [
        MCPSyncMcpItem(
            id=m.id,
            name=m.name,
            version=m.version,
            description=m.description,
            category=m.category,
            tags=m.tags,
            created_by=m.created_by,
            created_at=m.created_at,
            updated_at=m.updated_at,
            fabs=[
                MCPFabSyncItem(
                    **MCPFabRead.model_validate(f).model_dump(),
                    changed=(f.mcp_id, f.fab_id) in changed_keys,
                )
                for f in fabs_by_mcp.get(m.id, [])
            ],
        )
        for m in mcps
    ]

    available_count = sum(1 for f in mcp_fabs if f.status == AvailabilityStatus.available)
    return MCPSyncResult(
        synced_at=datetime.now(timezone.utc),
        total=len(mcp_fabs),
        available=available_count,
        unavailable=len(mcp_fabs) - available_count,
        items=items,
    )
