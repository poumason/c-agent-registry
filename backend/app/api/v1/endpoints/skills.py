import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.deps import get_current_user
from app.crud import fab as fab_crud
from app.crud import skill as skill_crud
from app.db.base import get_db
from app.models.enums import AvailabilityStatus
from app.models.skill import Skill
from app.models.skill_fab import SkillFab
from app.models.user import User
from app.schemas.skill import SkillRead, SkillSyncItem, SkillSyncResult
from app.schemas.skill_fab import SkillFabCreate, SkillFabRead
from app.services.storage import object_exists

router = APIRouter(prefix="/skills", tags=["skills"])
settings = get_settings()


def _group_fabs_by_skill(fabs: list[SkillFab]) -> dict[uuid.UUID, list[SkillFab]]:
    grouped: dict[uuid.UUID, list[SkillFab]] = {}
    for f in fabs:
        grouped.setdefault(f.skill_id, []).append(f)
    return grouped


def _to_read(skill: Skill, fabs: list[SkillFab]) -> SkillRead:
    return SkillRead(
        id=skill.id,
        name=skill.name,
        version=skill.version,
        description=skill.description,
        category=skill.category,
        tags=skill.tags,
        created_by=skill.created_by,
        bucket_path=skill.bucket_path,
        mcp_dependency=skill.mcp_dependency,
        status=skill.status,
        last_synced_at=skill.last_synced_at,
        created_at=skill.created_at,
        updated_at=skill.updated_at,
        fabs=[SkillFabRead.model_validate(f) for f in fabs],
    )


@router.get("", response_model=list[SkillRead])
async def list_skills(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[SkillRead]:
    skills = await skill_crud.list_skills(db)
    fabs_by_skill = _group_fabs_by_skill(await skill_crud.list_all_skill_fabs(db))
    return [_to_read(s, fabs_by_skill.get(s.id, [])) for s in skills]


@router.post("/{skill_id}/fabs", response_model=SkillFabRead, status_code=status.HTTP_201_CREATED)
async def assign_skill_fab(
    skill_id: uuid.UUID,
    payload: SkillFabCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SkillFabRead:
    """Marks an existing skill as available in a fab. Not the removed "create a new
    skill" flow — this attaches a fab to a skill that already exists in the catalog."""
    if await skill_crud.get_by_id(db, skill_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")
    if await fab_crud.get_by_id(db, payload.fab_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fab not found")
    if await skill_crud.get_skill_fab(db, skill_id, payload.fab_id) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Skill already available in this fab"
        )
    skill_fab = await skill_crud.create_skill_fab(db, skill_id=skill_id, fab_id=payload.fab_id)
    return SkillFabRead.model_validate(skill_fab)


@router.get("/{skill_id}/fabs", response_model=list[SkillFabRead])
async def list_skill_fabs(
    skill_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[SkillFabRead]:
    fabs = await skill_crud.list_skill_fabs_for_skill(db, skill_id)
    return [SkillFabRead.model_validate(f) for f in fabs]


@router.delete("/{skill_id}/fabs/{fab_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_skill_fab(
    skill_id: uuid.UUID,
    fab_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    skill_fab = await skill_crud.get_skill_fab(db, skill_id, fab_id)
    if skill_fab is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    await skill_crud.remove_skill_fab(db, skill_fab)


@router.post("/sync", response_model=SkillSyncResult)
async def sync_skills(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SkillSyncResult:
    """Re-checks every skill's bucket_path still exists in MinIO and refreshes status.
    `changed` on each returned item is true when this run flipped its status, so the
    frontend can highlight exactly what this sync touched."""
    skills = await skill_crud.list_skills(db)
    previous_status = {s.id: s.status for s in skills}
    for skill in skills:
        available = object_exists(settings.minio_skills_bucket, skill.bucket_path)
        skill_crud.mark_synced(
            skill, AvailabilityStatus.available if available else AvailabilityStatus.unavailable
        )
    await db.commit()
    for skill in skills:
        await db.refresh(skill)

    fabs_by_skill = _group_fabs_by_skill(await skill_crud.list_all_skill_fabs(db))
    available_count = sum(1 for s in skills if s.status == AvailabilityStatus.available)
    return SkillSyncResult(
        synced_at=datetime.now(timezone.utc),
        total=len(skills),
        available=available_count,
        unavailable=len(skills) - available_count,
        items=[
            SkillSyncItem(
                **_to_read(s, fabs_by_skill.get(s.id, [])).model_dump(),
                changed=s.status != previous_status[s.id],
            )
            for s in skills
        ],
    )
