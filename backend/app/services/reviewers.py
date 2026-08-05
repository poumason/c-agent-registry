import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import user as user_crud
from app.crud import user_agent_rel as membership_crud
from app.models.agent import Agent
from app.models.enums import UserRole


async def eligible_reviewer_ids(
    db: AsyncSession, agent: Agent, *, exclude_user_id: uuid.UUID
) -> set[uuid.UUID]:
    """Users who may review a submitted version of this agent.

    Per Claude.md: system owners/admins can review any agent, plus anyone granted
    an admin/reviewer Asset_Role on this specific agent (User_Agent_Rel).
    """
    global_reviewers = await user_crud.list_by_roles(db, [UserRole.owner, UserRole.admin])
    ids = {u.id for u in global_reviewers}

    agent_reviewers = await membership_crud.list_reviewer_eligible_members(db, agent.id)
    ids |= {m.user_id for m in agent_reviewers}

    ids.discard(exclude_user_id)
    return ids
