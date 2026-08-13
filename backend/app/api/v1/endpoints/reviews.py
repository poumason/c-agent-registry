import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.agent_access import (
    EDITABLE_VERSION_STATUSES,
    ensure_agent_visible,
    ensure_can_manage,
    get_agent_by_id_or_404,
    get_version_or_404,
)
from app.core.deps import get_current_user, require_role
from app.crud import agent_version as version_crud
from app.crud import review as review_crud
from app.crud import user as user_crud
from app.db.base import get_db
from app.models.enums import ReviewResult, UserRole, UserStatus, VersionStatus
from app.models.user import User
from app.schemas.agent_version import AgentVersionRead
from app.schemas.review import (
    ReviewDecision,
    ReviewerCandidate,
    ReviewQueueItem,
    ReviewQueueResponse,
    ReviewRead,
    SubmitForReview,
)
from app.services.packaging import generate_package_for_version
from app.services.reviewers import list_reviewer_candidates

router = APIRouter(tags=["reviews"])


@router.get("/reviewers", response_model=list[ReviewerCandidate])
async def list_reviewers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ReviewerCandidate]:
    candidates = await list_reviewer_candidates(db)
    return [ReviewerCandidate.model_validate(u) for u in candidates]


@router.post("/versions/{version_slug}/submit", response_model=AgentVersionRead)
async def submit_version(
    version_slug: str,
    payload: SubmitForReview,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentVersionRead:
    agent_version = await get_version_or_404(db, version_slug)
    agent = await get_agent_by_id_or_404(db, agent_version.agent_id)
    await ensure_can_manage(db, agent, current_user)
    if agent_version.status not in EDITABLE_VERSION_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only draft or rejected versions can be submitted",
        )

    reviewer_ids = set(payload.reviewer_ids)
    if reviewer_ids:
        if current_user.id in reviewer_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot assign yourself as reviewer",
            )
        for reviewer_id in reviewer_ids:
            reviewer = await user_crud.get_by_id(db, reviewer_id)
            if (
                reviewer is None
                or reviewer.status != UserStatus.active
                or reviewer.role not in (UserRole.reviewer, UserRole.admin)
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{reviewer_id} is not an eligible reviewer",
                )
    else:
        # No reviewers named: fall back to every eligible reviewer (system role
        # reviewer/admin), excluding the submitter.
        candidates = await list_reviewer_candidates(db)
        reviewer_ids = {c.id for c in candidates} - {current_user.id}

    if not reviewer_ids:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No eligible reviewers available for this version",
        )

    for reviewer_id in reviewer_ids:
        await review_crud.create_review(
            db, agent_slug=agent_version.slug, reviewer_id=reviewer_id
        )

    agent_version.status = VersionStatus.in_review
    agent_version.updated_by = current_user.id
    agent_version = await version_crud.save(db, agent_version)
    return AgentVersionRead.model_validate(agent_version)


@router.get("/versions/{version_slug}/reviews", response_model=list[ReviewRead])
async def list_version_reviews(
    version_slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ReviewRead]:
    agent_version = await get_version_or_404(db, version_slug)
    agent = await get_agent_by_id_or_404(db, agent_version.agent_id)
    await ensure_agent_visible(db, agent, current_user)
    reviews = await review_crud.list_by_version(db, agent_version.slug)
    return [ReviewRead.model_validate(r) for r in reviews]


@router.get("/reviews", response_model=ReviewQueueResponse)
async def review_queue(
    status: ReviewResult = ReviewResult.pending,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.reviewer, UserRole.admin)),
) -> ReviewQueueResponse:
    # Admin sees every reviewer's rows (a genuine oversight queue); a reviewer sees
    # only their own assignments — matches the same scope `decide_review` already
    # enforces for who's allowed to act on a row.
    scope_reviewer_id = None if current_user.role == UserRole.admin else current_user.id
    rows, total = await review_crud.list_queue(
        db, reviewer_id=scope_reviewer_id, status=status, limit=limit, offset=offset
    )
    items = [
        ReviewQueueItem(
            id=review.id,
            result=review.result,
            priority=review.priority,
            comment=review.comment,
            created_at=review.created_at,
            updated_at=review.updated_at,
            agent_slug=agent.slug,
            agent_name=agent.name,
            version_slug=version.slug,
            version_number=version.version,
            reviewer_id=reviewer.id,
            reviewer_name=reviewer.name,
            submitted_by_id=submitter.id,
            submitted_by_name=submitter.name,
            signoff_by_id=signoff.id if signoff else None,
            signoff_by_name=signoff.name if signoff else None,
        )
        for review, version, agent, reviewer, submitter, signoff in rows
    ]
    return ReviewQueueResponse(items=items, total=total, limit=limit, offset=offset)


@router.post("/reviews/{review_id}/decision", response_model=ReviewRead)
async def decide_review(
    review_id: uuid.UUID,
    payload: ReviewDecision,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReviewRead:
    review = await review_crud.get_by_id(db, review_id)
    if review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    if review.reviewer_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your review")
    if review.result != ReviewResult.pending:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Review already decided"
        )

    agent_version = await get_version_or_404(db, review.agent_slug)
    if agent_version.status != VersionStatus.in_review:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Version is no longer awaiting review",
        )

    review.result = payload.result
    review.signoff_by = current_user.id
    review.comment = payload.comment
    review = await review_crud.save(db, review)

    agent = await get_agent_by_id_or_404(db, agent_version.agent_id)
    if payload.result == ReviewResult.approved:
        agent_version.status = VersionStatus.approved
        agent_version.updated_by = current_user.id
        await version_crud.save(db, agent_version)
        await generate_package_for_version(db, agent=agent, agent_version=agent_version)
    else:
        agent_version.status = VersionStatus.rejected
        agent_version.updated_by = current_user.id
        await version_crud.save(db, agent_version)

    return ReviewRead.model_validate(review)
