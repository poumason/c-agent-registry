from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.agent_access import (
    ensure_agent_visible,
    ensure_can_manage,
    ensure_version_editable,
    get_agent_by_id_or_404,
    get_agent_or_404,
    get_version_or_404,
)
from app.core.config import get_settings
from app.core.deps import get_current_user
from app.crud import agent_fab as agent_fab_crud
from app.crud import agent_version as version_crud
from app.db.base import get_db
from app.models.enums import VersionStatus
from app.models.user import User
from app.schemas.agent_card import AgentCard
from app.schemas.agent_version import AgentVersionCreate, AgentVersionRead, AgentVersionUpdate
from app.services.agent_card import build_agent_card
from app.services.storage import presigned_download_url

router = APIRouter(tags=["agent-versions"])
settings = get_settings()


@router.post(
    "/agents/{slug}/versions",
    response_model=AgentVersionRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_version(
    slug: str,
    payload: AgentVersionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentVersionRead:
    agent = await get_agent_or_404(db, slug)
    await ensure_can_manage(db, agent, current_user)
    version_number = await version_crud.next_version_number(db, agent.id)
    version_slug = f"{agent.slug}-v{version_number}"
    agent_version = await version_crud.create_version(
        db,
        slug=version_slug,
        agent_id=agent.id,
        version=version_number,
        streaming=payload.streaming,
        default_input_modes=payload.default_input_modes,
        default_output_modes=payload.default_output_modes,
        created_by=current_user.id,
    )
    return AgentVersionRead.model_validate(agent_version)


@router.get("/agents/{slug}/versions", response_model=list[AgentVersionRead])
async def list_versions(
    slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AgentVersionRead]:
    agent = await get_agent_or_404(db, slug)
    await ensure_agent_visible(db, agent, current_user)
    versions = await version_crud.list_by_agent(db, agent.id)
    return [AgentVersionRead.model_validate(v) for v in versions]


@router.get("/versions/{version_slug}", response_model=AgentVersionRead)
async def get_version(
    version_slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentVersionRead:
    agent_version = await get_version_or_404(db, version_slug)
    agent = await get_agent_by_id_or_404(db, agent_version.agent_id)
    await ensure_agent_visible(db, agent, current_user)
    return AgentVersionRead.model_validate(agent_version)


@router.patch("/versions/{version_slug}", response_model=AgentVersionRead)
async def update_version(
    version_slug: str,
    payload: AgentVersionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentVersionRead:
    agent_version = await get_version_or_404(db, version_slug)
    agent = await get_agent_by_id_or_404(db, agent_version.agent_id)
    await ensure_can_manage(db, agent, current_user)
    ensure_version_editable(agent_version)
    if payload.streaming is not None:
        agent_version.streaming = payload.streaming
    if payload.default_input_modes is not None:
        agent_version.default_input_modes = payload.default_input_modes
    if payload.default_output_modes is not None:
        agent_version.default_output_modes = payload.default_output_modes
    if payload.skills is not None:
        agent_version.skills = payload.skills
    agent_version.updated_by = current_user.id
    agent_version = await version_crud.save(db, agent_version)
    return AgentVersionRead.model_validate(agent_version)


@router.post("/versions/{version_slug}/activate", response_model=AgentVersionRead)
async def activate_version(
    version_slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentVersionRead:
    agent_version = await get_version_or_404(db, version_slug)
    agent = await get_agent_by_id_or_404(db, agent_version.agent_id)
    await ensure_can_manage(db, agent, current_user)
    if agent_version.status != VersionStatus.approved:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only approved versions can be activated",
        )
    # No cap on how many versions of an agent can be active at once (2026-08-19
    # rule change) — a fab may be served by more than one active version.
    agent_version.status = VersionStatus.active
    agent_version.updated_by = current_user.id
    agent_version = await version_crud.save(db, agent_version)
    return AgentVersionRead.model_validate(agent_version)


@router.post("/versions/{version_slug}/deactivate", response_model=AgentVersionRead)
async def deactivate_version(
    version_slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentVersionRead:
    agent_version = await get_version_or_404(db, version_slug)
    agent = await get_agent_by_id_or_404(db, agent_version.agent_id)
    await ensure_can_manage(db, agent, current_user)
    if agent_version.status != VersionStatus.active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Version is not active"
        )
    agent_version.status = VersionStatus.approved
    agent_version.updated_by = current_user.id
    agent_version = await version_crud.save(db, agent_version)
    return AgentVersionRead.model_validate(agent_version)


@router.get("/versions/{version_slug}/agent-card", response_model=AgentCard)
async def get_agent_card(
    version_slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentCard:
    """Assembles the A2A 1.0 agent card fresh on every request from Agent +
    AgentVersion + AgentFab — see app/services/agent_card.py. Nothing here is
    persisted; this is a read/projection endpoint only."""
    agent_version = await get_version_or_404(db, version_slug)
    agent = await get_agent_by_id_or_404(db, agent_version.agent_id)
    await ensure_agent_visible(db, agent, current_user)
    fabs = await agent_fab_crud.list_for_version(db, agent_version.slug)
    return build_agent_card(agent, agent_version, fabs)


@router.get("/versions/{version_slug}/download")
async def download_version(
    version_slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    agent_version = await get_version_or_404(db, version_slug)
    agent = await get_agent_by_id_or_404(db, agent_version.agent_id)
    await ensure_agent_visible(db, agent, current_user)
    if agent_version.package_path is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This version has not been approved/packaged yet",
        )
    url = presigned_download_url(settings.minio_packages_bucket, agent_version.package_path)
    return {"url": url}
