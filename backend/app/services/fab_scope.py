"""Fab-scoping rules for agent-version dependencies.

An agent version can be deployed to more than one fab (see AgentFab), and a legacy
skill/mcp dependency (see AgentDependency.fab_id) is scoped to exactly one of those
fabs — the same skill can be added twice, once per fab, if it needs to differ per
fab (2026-08-18 design discussion: this replaced an earlier "one dependency set
must cover every deployed fab" rule that made it impossible to change what one fab
uses without touching every other fab the version also serves).

`resolve_dependency_fab_id` is the single place that decides whether a candidate
`fab_id` on a new dependency is legal, used by POST .../dependencies:

- type=model or source=registry: never fab-scoped (no `model_fabs` table, no
  per-fab registry data — see docs/superpowers/specs/2026-08-12-fab-scoped-schema-
  design.md), so fab_id must be omitted.
- legacy skill/mcp on a version with no fab deployed yet: fab_id must be omitted
  too (nothing to scope to).
- legacy skill/mcp on a version deployed to 1+ fabs: fab_id is required, must be
  one of those deployed fabs, and the referenced skill/mcp must itself be
  available in that fab (SkillFab / MCPFab, MCP additionally checked against its
  per-fab `status`).

There is deliberately no "does this version's dependency set cover all its fabs"
check anymore: deploying to a new fab now legitimately starts that fab out with no
dependencies of its own, the same way a freshly created version starts with none.
"""

import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import agent_fab as agent_fab_crud
from app.crud import fab as fab_crud
from app.crud import mcp as mcp_crud
from app.crud import skill as skill_crud
from app.models.enums import AvailabilityStatus, DependencySource, DependencyType


async def version_fab_ids(db: AsyncSession, agent_version_slug: str) -> set[uuid.UUID]:
    rows = await agent_fab_crud.list_for_version(db, agent_version_slug)
    return {r.fab_id for r in rows}


async def dependency_available_fab_ids(
    db: AsyncSession,
    *,
    type: DependencyType,
    dependency_id: str,
    source: DependencySource,
) -> set[uuid.UUID] | None:
    """The fabs this dependency is available in, or None if it isn't fab-scoped at
    all (always considered available everywhere — see module docstring)."""
    if source != DependencySource.legacy or type == DependencyType.model:
        return None
    try:
        legacy_id = uuid.UUID(dependency_id)
    except ValueError:
        return None
    if type == DependencyType.skill:
        rows = await skill_crud.list_skill_fabs_for_skill(db, legacy_id)
        return {r.fab_id for r in rows}
    rows = await mcp_crud.list_mcp_fabs_for_mcp(db, legacy_id)
    return {r.fab_id for r in rows if r.status == AvailabilityStatus.available}


async def resolve_dependency_fab_id(
    db: AsyncSession,
    *,
    agent_version_slug: str,
    type: DependencyType,
    dependency_id: str,
    source: DependencySource,
    requested_fab_id: uuid.UUID | None,
) -> uuid.UUID | None:
    """Validate `requested_fab_id` for a candidate dependency and return the fab_id
    to store (None for fab-agnostic dependencies). Raises HTTPException on any
    violation."""
    if type == DependencyType.model or source == DependencySource.registry:
        if requested_fab_id is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{type.value} dependencies have no fab dimension — omit fab_id",
            )
        return None

    deployed = await version_fab_ids(db, agent_version_slug)
    if not deployed:
        if requested_fab_id is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This version isn't deployed to any fab yet — omit fab_id",
            )
        return None

    if requested_fab_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="fab_id is required — this version is deployed to one or more fabs",
        )
    if requested_fab_id not in deployed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Fab {requested_fab_id} is not one of this version's deployed fabs",
        )

    available = await dependency_available_fab_ids(
        db, type=type, dependency_id=dependency_id, source=source
    )
    if available is not None and requested_fab_id not in available:
        fab = await fab_crud.get_by_id(db, requested_fab_id)
        fab_name = fab.fab if fab is not None else str(requested_fab_id)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{type.value} {dependency_id} is not available in fab {fab_name}",
        )
    return requested_fab_id
