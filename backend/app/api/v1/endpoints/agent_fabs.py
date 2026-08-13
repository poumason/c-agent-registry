from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.agent_access import (
    ensure_agent_visible,
    ensure_can_manage,
    ensure_version_editable,
    get_agent_by_id_or_404,
    get_version_or_404,
)
from app.core.deps import get_current_user
from app.crud import agent_fab as agent_fab_crud
from app.crud import fab as fab_crud
from app.db.base import get_db
from app.models.user import User
from app.schemas.agent_fab import AgentFabRead, AgentFabSetRequest

router = APIRouter(tags=["agent-fabs"])


@router.get("/versions/{version_slug}/fabs", response_model=list[AgentFabRead])
async def list_version_fabs(
    version_slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AgentFabRead]:
    agent_version = await get_version_or_404(db, version_slug)
    agent = await get_agent_by_id_or_404(db, agent_version.agent_id)
    await ensure_agent_visible(db, agent, current_user)
    rows = await agent_fab_crud.list_for_version(db, agent_version.slug)
    return [AgentFabRead.model_validate(r) for r in rows]


@router.put("/versions/{version_slug}/fabs", response_model=list[AgentFabRead])
async def set_version_fabs(
    version_slug: str,
    payload: AgentFabSetRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AgentFabRead]:
    agent_version = await get_version_or_404(db, version_slug)
    agent = await get_agent_by_id_or_404(db, agent_version.agent_id)
    await ensure_can_manage(db, agent, current_user)
    ensure_version_editable(agent_version)

    seen_fab_ids: set = set()
    for entry in payload.fabs:
        if entry.fab_id in seen_fab_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Fab {entry.fab_id} listed more than once",
            )
        seen_fab_ids.add(entry.fab_id)
        if await fab_crud.get_by_id(db, entry.fab_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Fab {entry.fab_id} not found"
            )

    rows = await agent_fab_crud.replace_for_version(
        db, agent_version.slug, [(e.fab_id, e.url) for e in payload.fabs]
    )
    return [AgentFabRead.model_validate(r) for r in rows]
