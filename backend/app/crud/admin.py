from datetime import datetime, timedelta, timezone

from sqlalchemy import Integer, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.crud import registry as registry_crud
from app.models.agent import Agent
from app.models.agent_version import AgentVersion
from app.models.ai_model import AIModel
from app.models.enums import AssetRole, AvailabilityStatus, ReviewResult, UserRole, UserStatus, VersionStatus
from app.models.mcp_fab import MCPFab
from app.models.review import Review
from app.models.user import User
from app.models.user_agent_rel import UserAgentRel
from app.services.storage import total_bucket_bytes

_AGENT_SORT_CLAUSES = {
    "newest": Agent.created_at.desc(),
    "oldest": Agent.created_at.asc(),
    "name": Agent.name.asc(),
}


async def list_agents_with_owner(
    db: AsyncSession, *, q: str | None, sort: str, limit: int, offset: int
) -> tuple[list[tuple[Agent, User]], int]:
    """Every non-deleted agent (visibility ignored — this is the admin governance
    view, not the visibility-scoped public one) joined with its current owner."""
    stmt = (
        select(Agent, User)
        .join(UserAgentRel, UserAgentRel.agent_id == Agent.id)
        .join(User, User.id == UserAgentRel.user_id)
        .where(Agent.deleted_at.is_(None), UserAgentRel.role == AssetRole.owner)
    )
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(or_(Agent.name.ilike(pattern), Agent.description.ilike(pattern)))

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.order_by(_AGENT_SORT_CLAUSES.get(sort, _AGENT_SORT_CLAUSES["newest"])).limit(limit).offset(offset)
    rows = (await db.execute(stmt)).all()
    return [(row[0], row[1]) for row in rows], total


TREND_WINDOW_DAYS = 30


def _day_range(days: int) -> list[str]:
    today = datetime.now(timezone.utc).date()
    return [(today - timedelta(days=offset)).isoformat() for offset in range(days - 1, -1, -1)]


async def _counts_by_day(db: AsyncSession, *, result: ReviewResult, since: datetime) -> dict[str, int]:
    stmt = (
        select(func.date(Review.updated_at).label("day"), func.count().label("count"))
        .where(Review.result == result, Review.updated_at >= since)
        .group_by("day")
    )
    rows = (await db.execute(stmt)).all()
    return {row.day.isoformat(): row.count for row in rows}


async def get_review_summary(db: AsyncSession) -> dict:
    since = datetime.now(timezone.utc) - timedelta(days=TREND_WINDOW_DAYS)

    pending_count = (
        await db.execute(select(func.count()).where(Review.result == ReviewResult.pending))
    ).scalar_one()
    total_approved = (
        await db.execute(select(func.count()).where(Review.result == ReviewResult.approved))
    ).scalar_one()
    total_rejected = (
        await db.execute(select(func.count()).where(Review.result == ReviewResult.rejected))
    ).scalar_one()

    last_30_approved = (
        await db.execute(
            select(func.count()).where(Review.result == ReviewResult.approved, Review.updated_at >= since)
        )
    ).scalar_one()
    last_30_rejected = (
        await db.execute(
            select(func.count()).where(Review.result == ReviewResult.rejected, Review.updated_at >= since)
        )
    ).scalar_one()

    avg_seconds = (
        await db.execute(
            select(func.avg(func.extract("epoch", Review.updated_at - Review.created_at))).where(
                Review.result != ReviewResult.pending, Review.updated_at >= since
            )
        )
    ).scalar_one()
    average_review_time_hours = round(avg_seconds / 3600, 1) if avg_seconds is not None else None

    approved_by_day = await _counts_by_day(db, result=ReviewResult.approved, since=since)
    rejected_by_day = await _counts_by_day(db, result=ReviewResult.rejected, since=since)
    days = _day_range(TREND_WINDOW_DAYS)

    top_reviewers_stmt = (
        select(
            Review.signoff_by,
            User.name,
            func.count().label("total"),
            func.sum(func.cast(Review.result == ReviewResult.approved, Integer)).label(
                "approved"
            ),
            func.sum(func.cast(Review.result == ReviewResult.rejected, Integer)).label(
                "rejected"
            ),
        )
        .join(User, Review.signoff_by == User.id)
        .where(Review.result != ReviewResult.pending)
        .group_by(Review.signoff_by, User.name)
        .order_by(func.count().desc())
        .limit(5)
    )
    top_reviewers_rows = (await db.execute(top_reviewers_stmt)).all()

    return {
        "pendingCount": pending_count,
        "totalApproved": total_approved,
        "totalRejected": total_rejected,
        "last30Days": {"approved": last_30_approved, "rejected": last_30_rejected},
        "averageReviewTimeHours": average_review_time_hours,
        "trends": {
            "approvedByDay": [{"date": d, "count": approved_by_day.get(d, 0)} for d in days],
            "rejectedByDay": [{"date": d, "count": rejected_by_day.get(d, 0)} for d in days],
        },
        "topReviewers": [
            {
                "reviewerId": row.signoff_by,
                "reviewerName": row.name,
                "total": row.total,
                "approved": row.approved,
                "rejected": row.rejected,
            }
            for row in top_reviewers_rows
        ],
    }


async def _user_counts_by_day(db: AsyncSession, *, column, since: datetime, extra_where=None) -> dict[str, int]:
    stmt = select(func.date(column).label("day"), func.count().label("count")).where(column >= since)
    if extra_where is not None:
        stmt = stmt.where(extra_where)
    stmt = stmt.group_by("day")
    rows = (await db.execute(stmt)).all()
    return {row.day.isoformat(): row.count for row in rows}


async def get_user_summary(db: AsyncSession) -> dict:
    since = datetime.now(timezone.utc) - timedelta(days=TREND_WINDOW_DAYS)

    total_users = (
        await db.execute(select(func.count()).where(User.deleted_at.is_(None)))
    ).scalar_one()
    active_count = (
        await db.execute(
            select(func.count()).where(User.deleted_at.is_(None), User.status == UserStatus.active)
        )
    ).scalar_one()
    disabled_count = (
        await db.execute(
            select(func.count()).where(User.deleted_at.is_(None), User.status == UserStatus.disabled)
        )
    ).scalar_one()

    by_role = {}
    for role in UserRole:
        by_role[role.value] = (
            await db.execute(
                select(func.count()).where(User.deleted_at.is_(None), User.role == role)
            )
        ).scalar_one()

    # "Owns at least one live (non-deleted) agent" — a LEFT JOIN to the owner
    # membership of non-deleted agents, then filter to the NULL side.
    owned_agent_subq = (
        select(UserAgentRel.user_id)
        .join(Agent, Agent.id == UserAgentRel.agent_id)
        .where(UserAgentRel.role == AssetRole.owner, Agent.deleted_at.is_(None))
        .distinct()
        .subquery()
    )
    without_agents = (
        await db.execute(
            select(func.count()).where(
                User.deleted_at.is_(None),
                User.status == UserStatus.active,
                User.id.notin_(select(owned_agent_subq.c.user_id)),
            )
        )
    ).scalar_one()

    created_by_day = await _user_counts_by_day(db, column=User.created_at, since=since)
    deleted_by_day = await _user_counts_by_day(
        db, column=User.deleted_at, since=since, extra_where=User.deleted_at.is_not(None)
    )
    days = _day_range(TREND_WINDOW_DAYS)

    top_owners_stmt = (
        select(User.id, User.name, func.count().label("agent_count"))
        .join(UserAgentRel, UserAgentRel.user_id == User.id)
        .join(Agent, Agent.id == UserAgentRel.agent_id)
        .where(UserAgentRel.role == AssetRole.owner, Agent.deleted_at.is_(None))
        .group_by(User.id, User.name)
        .order_by(func.count().desc())
        .limit(5)
    )
    top_owners_rows = (await db.execute(top_owners_stmt)).all()

    top_reviewers_stmt = (
        select(Review.signoff_by, User.name, func.count().label("review_count"))
        .join(User, Review.signoff_by == User.id)
        .where(Review.result != ReviewResult.pending)
        .group_by(Review.signoff_by, User.name)
        .order_by(func.count().desc())
        .limit(5)
    )
    top_reviewers_rows = (await db.execute(top_reviewers_stmt)).all()

    return {
        "totalUsers": total_users,
        "activeCount": active_count,
        "disabledCount": disabled_count,
        "usersWithoutAgents": without_agents,
        "byRole": by_role,
        "trends": {
            "createdByDay": [{"date": d, "count": created_by_day.get(d, 0)} for d in days],
            "deletedByDay": [{"date": d, "count": deleted_by_day.get(d, 0)} for d in days],
        },
        "topAgentOwners": [
            {"userId": row.id, "userName": row.name, "agentCount": row.agent_count} for row in top_owners_rows
        ],
        "topReviewers": [
            {"userId": row.signoff_by, "userName": row.name, "reviewCount": row.review_count}
            for row in top_reviewers_rows
        ],
    }


async def get_agent_summary(db: AsyncSession) -> dict:
    total = (await db.execute(select(func.count()).where(Agent.deleted_at.is_(None)))).scalar_one()

    with_production = (
        await db.execute(
            select(func.count(func.distinct(Agent.id)))
            .join(AgentVersion, AgentVersion.agent_id == Agent.id)
            .where(Agent.deleted_at.is_(None), AgentVersion.status == VersionStatus.active)
        )
    ).scalar_one()

    without_any_version = (
        await db.execute(
            select(func.count()).where(
                Agent.deleted_at.is_(None),
                Agent.id.notin_(select(AgentVersion.agent_id).distinct()),
            )
        )
    ).scalar_one()

    by_visibility_rows = (
        await db.execute(
            select(Agent.visibility, func.count())
            .where(Agent.deleted_at.is_(None))
            .group_by(Agent.visibility)
        )
    ).all()

    return {
        "total": total,
        "withProduction": with_production,
        "withoutProduction": total - with_production,
        "withoutAnyVersion": without_any_version,
        "byVisibility": [{"visibility": row[0], "count": row[1]} for row in by_visibility_rows],
    }


async def _availability_status(db: AsyncSession, model) -> dict:
    total = (await db.execute(select(func.count()).select_from(model))).scalar_one()
    unavailable = (
        await db.execute(
            select(func.count()).select_from(model).where(model.status == AvailabilityStatus.unavailable)
        )
    ).scalar_one()
    last_synced_at = (await db.execute(select(func.max(model.last_synced_at)))).scalar_one()
    return {
        "total_count": total,
        "last_synced_at": last_synced_at,
        "consecutive_failures": 0,
        "stale_count": unavailable,
    }


async def _mcp_fab_availability_status(db: AsyncSession) -> dict:
    """MCP's own status/last_synced_at moved to MCPFab (availability is per-fab now,
    see docs/registry-sync.md) — counts over (mcp, fab) deployment rows rather than
    distinct MCPs, same convention as MCPSyncResult.total."""
    total = (await db.execute(select(func.count()).select_from(MCPFab))).scalar_one()
    unavailable = (
        await db.execute(
            select(func.count())
            .select_from(MCPFab)
            .where(MCPFab.status == AvailabilityStatus.unavailable)
        )
    ).scalar_one()
    last_synced_at = (await db.execute(select(func.max(MCPFab.last_synced_at)))).scalar_one()
    return {
        "total_count": total,
        "last_synced_at": last_synced_at,
        "consecutive_failures": 0,
        "stale_count": unavailable,
    }


async def get_stats(db: AsyncSession) -> dict:
    since = datetime.now(timezone.utc) - timedelta(days=TREND_WINDOW_DAYS)
    days = _day_range(TREND_WINDOW_DAYS)

    agent_summary = await get_agent_summary(db)
    user_summary = await get_user_summary(db)
    review_summary = await get_review_summary(db)

    versions_by_status_rows = (
        await db.execute(select(AgentVersion.status, func.count()).group_by(AgentVersion.status))
    ).all()
    versions_by_status = {row[0].value: row[1] for row in versions_by_status_rows}

    agents_created_by_day = await _user_counts_by_day(db, column=Agent.created_at, since=since)

    # "mcp"/"model" are real now (see app/api/v1/endpoints/mcps.py, ai_models.py) —
    # shoehorned into the same RegistryStatus shape the placeholder sources use
    # (total_count/last_synced_at/stale_count) since there's no real
    # "consecutive_failures" concept for a probe that runs on demand rather than a
    # background job; it's always 0 here, not fabricated data, just an unused field
    # for these two sources.
    registry_status = {
        "skillhub-registry": registry_crud.get_overview("skillhub-registry").status,
        "mcp": await _mcp_fab_availability_status(db),
        "model": await _availability_status(db, AIModel),
    }

    settings = get_settings()
    artifact_storage_bytes = total_bucket_bytes(settings.minio_packages_bucket)

    return {
        "agentsTotal": agent_summary["total"],
        "agentsByVisibility": agent_summary["byVisibility"],
        "agentsWithoutProductionCount": agent_summary["withoutProduction"],
        "versionsByStatus": versions_by_status,
        "usersTotal": user_summary["totalUsers"],
        "usersByRole": user_summary["byRole"],
        "disabledUsersCount": user_summary["disabledCount"],
        "pendingReviewCount": review_summary["pendingCount"],
        "registryStatus": registry_status,
        "trends": {
            "agentsCreatedByDay": [{"date": d, "count": agents_created_by_day.get(d, 0)} for d in days],
            "reviewsApprovedByDay": review_summary["trends"]["approvedByDay"],
            "reviewsRejectedByDay": review_summary["trends"]["rejectedByDay"],
        },
        "reviewGovernance": {
            "approvedLast30Days": review_summary["last30Days"]["approved"],
            "rejectedLast30Days": review_summary["last30Days"]["rejected"],
            "averageReviewTimeHours": review_summary["averageReviewTimeHours"],
        },
        "artifactStorageBytes": artifact_storage_bytes,
    }
