"""Fab-availability coverage checks for agent-version dependencies.

An agent version can be deployed to more than one fab (see AgentFab). A skill/mcp
dependency is only usable in the fabs where it's itself available (see SkillFab /
MCPFab). The confirmed rule (2026-08-17 design discussion): a version's dependency
set must cover *every* fab the version is deployed to, not just some of them — if a
version is deployed to fab A and fab B, every skill/mcp it depends on must be
available in both, or the write is rejected. This module is the single place both
directions of that check live:

- adding a dependency must not violate coverage for fabs the version is already in
  (see `uncovered_fabs_for_new_dependency`, used by POST .../dependencies)
- changing a version's fab deployment must not drop coverage for a fab an existing
  dependency doesn't reach (see `dependencies_uncovered_by`, used by PUT .../fabs)

AI Model dependencies and registry-sourced (SkillHub Registry) skills have no fab
dimension in this schema at all (see docs/superpowers/specs/2026-08-12-fab-scoped-
schema-design.md — Model deliberately has no `model_fabs` table, and Registry items
aren't rows in `skills`/`skill_fabs`), so they're always treated as covering every
fab: there's nothing meaningful to restrict.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import agent_dependency as dependency_crud
from app.crud import agent_fab as agent_fab_crud
from app.crud import mcp as mcp_crud
from app.crud import skill as skill_crud
from app.models.agent_dependency import AgentDependency
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


async def uncovered_fabs_for_new_dependency(
    db: AsyncSession,
    *,
    agent_version_slug: str,
    type: DependencyType,
    dependency_id: str,
    source: DependencySource,
) -> set[uuid.UUID]:
    """Fabs the version is already deployed to that this candidate dependency is NOT
    available in. Empty means the dependency may be added; a version with no fab
    deployment yet has nothing to violate."""
    required = await version_fab_ids(db, agent_version_slug)
    if not required:
        return set()
    available = await dependency_available_fab_ids(
        db, type=type, dependency_id=dependency_id, source=source
    )
    if available is None:
        return set()
    return required - available


async def dependencies_uncovered_by(
    db: AsyncSession, *, agent_version_slug: str, fab_ids: set[uuid.UUID]
) -> list[tuple[AgentDependency, set[uuid.UUID]]]:
    """Existing dependencies of this version that would NOT all be satisfied if the
    version were deployed to exactly `fab_ids` — paired with the specific fabs each
    one is missing. Empty `fab_ids` (undeploying entirely) trivially satisfies
    everything."""
    if not fab_ids:
        return []
    deps = await dependency_crud.list_by_version(db, agent_version_slug)
    result: list[tuple[AgentDependency, set[uuid.UUID]]] = []
    for dep in deps:
        available = await dependency_available_fab_ids(
            db, type=dep.type, dependency_id=dep.dependency_id, source=dep.source
        )
        if available is None:
            continue
        missing = fab_ids - available
        if missing:
            result.append((dep, missing))
    return result
