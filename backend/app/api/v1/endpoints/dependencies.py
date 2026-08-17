import uuid

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
from app.crud import agent_dependency as dependency_crud
from app.crud import ai_model as ai_model_crud
from app.crud import fab as fab_crud
from app.crud import mcp as mcp_crud
from app.crud import registry as registry_crud
from app.crud import skill as skill_crud
from app.db.base import get_db
from app.models.enums import DependencySource, DependencyType
from app.models.user import User
from app.schemas.agent_dependency import AgentDependencyCreate, AgentDependencyRead
from app.services import fab_scope

router = APIRouter(tags=["dependencies"])

# Which Registry source (see app/crud/registry.py) backs a dependency `type` when
# source=registry. Skill-only now — SkillHub Registry mirrors `skill` dependencies;
# `mcp` has no registry source anymore (it resolves against the real, availability-
# synced mcps table directly, same as source=legacy — see app/api/v1/endpoints/
# mcps.py). Model and Agent Templates aren't dependency types at all here.
_REGISTRY_SOURCE_BY_TYPE = {
    DependencyType.skill: "skillhub-registry",
}


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
    ensure_version_editable(agent_version)

    if payload.source == DependencySource.legacy:
        try:
            legacy_id = uuid.UUID(payload.dependency_id)
        except ValueError:
            exists = None
        else:
            if payload.type == DependencyType.skill:
                exists = await skill_crud.get_by_id(db, legacy_id)
            elif payload.type == DependencyType.mcp:
                exists = await mcp_crud.get_by_id(db, legacy_id)
            else:
                exists = await ai_model_crud.get_by_id(db, legacy_id)
    else:
        registry_source = _REGISTRY_SOURCE_BY_TYPE.get(payload.type)
        if registry_source is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{payload.type.value} has no registry source — use source=legacy",
            )
        exists = registry_crud.get_item(registry_source, payload.dependency_id)
    if exists is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{payload.source.value} {payload.type.value} {payload.dependency_id} not found",
        )

    # A version's dependency set must cover every fab the version is deployed to
    # (see app/services/fab_scope.py) — reject a candidate that isn't available in
    # one of them rather than silently letting a fab's deployment go unfulfilled.
    missing_fab_ids = await fab_scope.uncovered_fabs_for_new_dependency(
        db,
        agent_version_slug=agent_version.slug,
        type=payload.type,
        dependency_id=payload.dependency_id,
        source=payload.source,
    )
    if missing_fab_ids:
        fabs_by_id = {f.id: f.fab for f in await fab_crud.list_fabs(db)}
        names = ", ".join(sorted(fabs_by_id.get(fid, str(fid)) for fid in missing_fab_ids))
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"{payload.type.value} {payload.dependency_id} is not available in "
                f"fab(s) this version is deployed to: {names}"
            ),
        )

    dependency = await dependency_crud.create_dependency(
        db,
        agent_slug=agent_version.slug,
        dependency_id=payload.dependency_id,
        type=payload.type,
        source=payload.source,
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
    ensure_version_editable(agent_version)
    dependency = await dependency_crud.get_by_id(db, dependency_row_id)
    if dependency is None or dependency.agent_slug != agent_version.slug:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dependency not found")
    await dependency_crud.remove_dependency(db, dependency)
