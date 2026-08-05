import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.agent_access import (
    ensure_agent_visible,
    ensure_can_manage,
    get_agent_by_id_or_404,
    get_version_or_404,
)
from app.core.deps import get_current_user
from app.crud import agent_dependency as dependency_crud
from app.crud import mcp as mcp_crud
from app.crud import skill as skill_crud
from app.db.base import get_db
from app.models.enums import DependencyType, VersionStatus
from app.models.user import User
from app.schemas.agent_dependency import AgentDependencyCreate, AgentDependencyRead

router = APIRouter(tags=["dependencies"])


@router.get("/versions/{version_slug}/dependencies", response_model=list[AgentDependencyRead])
async def list_dependencies(
    version_slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AgentDependencyRead]:
    agent_version = await get_version_or_404(db, version_slug)
    agent = await get_agent_by_id_or_404(db, agent_version.agent_id)
    await ensure_agent_visible(db, agent, current_user)
    deps = await dependency_crud.list_by_version(db, agent_version.slug)
    return [AgentDependencyRead.model_validate(d) for d in deps]


@router.post(
    "/versions/{version_slug}/dependencies",
    response_model=AgentDependencyRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_dependency(
    version_slug: str,
    payload: AgentDependencyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentDependencyRead:
    agent_version = await get_version_or_404(db, version_slug)
    agent = await get_agent_by_id_or_404(db, agent_version.agent_id)
    await ensure_can_manage(db, agent, current_user)
    if agent_version.status != VersionStatus.draft:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Dependencies can only be changed while the version is a draft",
        )

    if payload.type == DependencyType.skill:
        exists = await skill_crud.get_by_id(db, payload.dependency_id)
    else:
        exists = await mcp_crud.get_by_id(db, payload.dependency_id)
    if exists is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{payload.type.value} {payload.dependency_id} not found",
        )

    dependency = await dependency_crud.create_dependency(
        db,
        agent_slug=agent_version.slug,
        dependency_id=payload.dependency_id,
        type=payload.type,
    )
    return AgentDependencyRead.model_validate(dependency)


@router.delete(
    "/versions/{version_slug}/dependencies/{dependency_row_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_dependency(
    version_slug: str,
    dependency_row_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    agent_version = await get_version_or_404(db, version_slug)
    agent = await get_agent_by_id_or_404(db, agent_version.agent_id)
    await ensure_can_manage(db, agent, current_user)
    if agent_version.status != VersionStatus.draft:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Dependencies can only be changed while the version is a draft",
        )
    dependency = await dependency_crud.get_by_id(db, dependency_row_id)
    if dependency is None or dependency.agent_slug != agent_version.slug:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dependency not found")
    await dependency_crud.remove_dependency(db, dependency)
