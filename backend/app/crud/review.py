import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_version import AgentVersion
from app.models.enums import ReviewResult
from app.models.review import Review


async def get_by_id(db: AsyncSession, review_id: uuid.UUID) -> Review | None:
    return await db.get(Review, review_id)


async def list_by_version(db: AsyncSession, agent_slug: str) -> list[Review]:
    result = await db.execute(
        select(Review).where(Review.agent_slug == agent_slug).order_by(Review.created_at)
    )
    return list(result.scalars().all())


async def list_mine(
    db: AsyncSession, reviewer_id: uuid.UUID, *, pending_only: bool = False
) -> list[Review]:
    stmt = select(Review).where(Review.reviewer_id == reviewer_id)
    if pending_only:
        stmt = stmt.where(Review.result == ReviewResult.pending)
    stmt = stmt.order_by(Review.created_at)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def has_review_for_agent(db: AsyncSession, reviewer_id: uuid.UUID, agent_id: uuid.UUID) -> bool:
    """Whether this user has ever been assigned a review on any version of this agent.

    Used to let an assigned reviewer view an otherwise-private agent they're reviewing.
    """
    result = await db.execute(
        select(Review.id)
        .join(AgentVersion, Review.agent_slug == AgentVersion.slug)
        .where(AgentVersion.agent_id == agent_id, Review.reviewer_id == reviewer_id)
        .limit(1)
    )
    return result.scalar_one_or_none() is not None


async def create_review(
    db: AsyncSession, *, agent_slug: str, reviewer_id: uuid.UUID, priority: int = 0
) -> Review:
    review = Review(agent_slug=agent_slug, reviewer_id=reviewer_id, priority=priority)
    db.add(review)
    return review


async def save(db: AsyncSession, review: Review) -> Review:
    await db.commit()
    await db.refresh(review)
    return review
