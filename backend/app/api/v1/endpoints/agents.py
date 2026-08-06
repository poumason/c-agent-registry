import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.agent_access import (
    ensure_agent_visible,
    ensure_can_administer,
    ensure_can_manage,
    get_agent_or_404,
)
from app.core.deps import get_current_user
from app.crud import agent as agent_crud
from app.crud import user_agent_rel as membership_crud
from app.db.base import get_db
from app.models.agent import Agent
from app.models.enums import AssetRole
from app.models.user import User
from app.schemas.agent import AgentCreate, AgentRead, AgentUpdate
from app.schemas.user_agent_rel import MemberRead, MemberUpsert

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("", response_model=AgentRead, status_code=status.HTTP_201_CREATED)
async def create_agent(
    payload: AgentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentRead:
    if await agent_crud.get_by_slug(db, payload.slug) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug already in use")
    agent = await agent_crud.create_agent(
        db,
        slug=payload.slug,
        name=payload.name,
        description=payload.description,
        provider=payload.provider,
        visibility=payload.visibility,
        created_by=current_user.id,
    )
    # Creator becomes this agent's owner.
    await membership_crud.upsert_membership(
        db, user_id=current_user.id, agent_id=agent.id, role=AssetRole.owner
    )
    return AgentRead.model_validate(agent)


@router.get("", response_model=list[AgentRead])
async def list_agents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AgentRead]:
    agents = await agent_crud.list_agents(db)
    visible: list[Agent] = []
    for agent in agents:
        try:
            await ensure_agent_visible(db, agent, current_user)
        except HTTPException:
            continue
        visible.append(agent)
    return [AgentRead.model_validate(a) for a in visible]


@router.get("/{slug}", response_model=AgentRead)
async def get_agent(
    slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentRead:
    agent = await get_agent_or_404(db, slug)
    await ensure_agent_visible(db, agent, current_user)
    return AgentRead.model_validate(agent)


@router.patch("/{slug}", response_model=AgentRead)
async def update_agent(
    slug: str,
    payload: AgentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentRead:
    agent = await get_agent_or_404(db, slug)
    await ensure_can_manage(db, agent, current_user)
    agent = await agent_crud.update_agent(
        db,
        agent,
        name=payload.name,
        description=payload.description,
        provider=payload.provider,
        visibility=payload.visibility,
    )
    return AgentRead.model_validate(agent)


@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    agent = await get_agent_or_404(db, slug)
    await ensure_can_administer(db, agent, current_user)
    await agent_crud.soft_delete(db, agent)


@router.get("/{slug}/members", response_model=list[MemberRead])
async def list_members(
    slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[MemberRead]:
    agent = await get_agent_or_404(db, slug)
    await ensure_agent_visible(db, agent, current_user)
    members = await membership_crud.list_members(db, agent.id)
    return [MemberRead.model_validate(m) for m in members]


@router.post("/{slug}/members", response_model=MemberRead)
async def upsert_member(
    slug: str,
    payload: MemberUpsert,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MemberRead:
    agent = await get_agent_or_404(db, slug)
    await ensure_can_administer(db, agent, current_user)
    updated = await membership_crud.upsert_membership(
        db, user_id=payload.user_id, agent_id=agent.id, role=AssetRole.editor
    )
    return MemberRead.model_validate(updated)


@router.delete("/{slug}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    slug: str,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    agent = await get_agent_or_404(db, slug)
    await ensure_can_administer(db, agent, current_user)
    target = await membership_crud.get_membership(db, user_id, agent.id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    if target.role == AssetRole.owner:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Cannot remove the agent's owner"
        )
    await membership_crud.remove_membership(db, target)
