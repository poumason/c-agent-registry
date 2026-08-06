import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import can_administer_agent, can_manage_agent
from app.crud import agent as agent_crud
from app.crud import agent_version as version_crud
from app.crud import review as review_crud
from app.crud import user_agent_rel as membership_crud
from app.models.agent import Agent
from app.models.agent_version import AgentVersion
from app.models.enums import AgentVisibility, UserRole, VersionStatus
from app.models.user import User

# A rejected version is fixed in place and resubmitted rather than forced into a brand
# new version - that's what lets review history accumulate on a single version slug.
EDITABLE_VERSION_STATUSES = (VersionStatus.draft, VersionStatus.rejected)


async def get_agent_or_404(db: AsyncSession, slug: str) -> Agent:
    agent = await agent_crud.get_by_slug(db, slug)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return agent


async def get_agent_by_id_or_404(db: AsyncSession, agent_id: uuid.UUID) -> Agent:
    agent = await agent_crud.get_by_id(db, agent_id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return agent


async def get_version_or_404(db: AsyncSession, slug: str) -> AgentVersion:
    version = await version_crud.get_by_slug(db, slug)
    if version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")
    return version


async def ensure_agent_visible(db: AsyncSession, agent: Agent, user: User) -> None:
    if agent.visibility in (AgentVisibility.public, AgentVisibility.internal):
        return
    if user.role == UserRole.admin or agent.created_by == user.id:
        return
    membership = await membership_crud.get_membership(db, user.id, agent.id)
    if membership is not None:
        return
    # A reviewer assigned to this agent (even a private one) must be able to open it to
    # actually review it, without being a member.
    if await review_crud.has_review_for_agent(db, user.id, agent.id):
        return
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")


def ensure_version_editable(agent_version: AgentVersion) -> None:
    if agent_version.status not in EDITABLE_VERSION_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only draft or rejected versions can be edited",
        )


async def ensure_can_manage(db: AsyncSession, agent: Agent, user: User) -> None:
    membership = await membership_crud.get_membership(db, user.id, agent.id)
    if not can_manage_agent(user, membership):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")


async def ensure_can_administer(db: AsyncSession, agent: Agent, user: User) -> None:
    membership = await membership_crud.get_membership(db, user.id, agent.id)
    if not can_administer_agent(user, membership):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
