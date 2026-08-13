import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models.agent import Agent
from app.models.agent_version import AgentVersion
from app.models.enums import ReviewResult
from app.models.review import Review
from app.models.user import User


async def get_by_id(db: AsyncSession, review_id: uuid.UUID) -> Review | None:
    return await db.get(Review, review_id)


async def list_by_version(db: AsyncSession, agent_slug: str) -> list[Review]:
    result = await db.execute(
        select(Review).where(Review.agent_slug == agent_slug).order_by(Review.created_at)
    )
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


_ReviewerUser = aliased(User)
_SubmitterUser = aliased(User)
_SignoffUser = aliased(User)


def _queue_row_select():
    # Joined once here and reused by both the page query and the count query below,
    # so the two can never disagree about which rows qualify.
    return (
        select(Review, AgentVersion, Agent, _ReviewerUser, _SubmitterUser, _SignoffUser)
        .join(AgentVersion, Review.agent_slug == AgentVersion.slug)
        .join(Agent, AgentVersion.agent_id == Agent.id)
        .join(_ReviewerUser, Review.reviewer_id == _ReviewerUser.id)
        .join(_SubmitterUser, AgentVersion.created_by == _SubmitterUser.id)
        .outerjoin(_SignoffUser, Review.signoff_by == _SignoffUser.id)
    )


async def list_queue(
    db: AsyncSession,
    *,
    reviewer_id: uuid.UUID | None,
    status: ReviewResult,
    limit: int,
    offset: int,
) -> tuple[list[tuple], int]:
    """Review Queue rows, joined with display info. `reviewer_id=None` means "every
    reviewer's rows" (admin scope); a UUID scopes to just that reviewer's own
    assignments — the same visibility split `decide_review` already enforces for who's
    allowed to act on a row, applied here to who's allowed to see it in the queue."""
    stmt = _queue_row_select().where(Review.result == status)
    if reviewer_id is not None:
        stmt = stmt.where(Review.reviewer_id == reviewer_id)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.order_by(Review.created_at.desc()).limit(limit).offset(offset)
    rows = (await db.execute(stmt)).all()
    return list(rows), total


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
