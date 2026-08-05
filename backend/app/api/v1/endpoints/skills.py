import uuid

from fastapi import APIRouter, Depends, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.deps import get_current_user
from app.crud import skill as skill_crud
from app.db.base import get_db
from app.models.user import User
from app.schemas.skill import SkillRead
from app.services.storage import ensure_buckets, put_bytes

router = APIRouter(prefix="/skills", tags=["skills"])
settings = get_settings()


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


@router.post("", response_model=SkillRead, status_code=201)
async def create_skill(
    file: UploadFile,
    name: str = Form(...),
    version: str = Form(...),
    description: str | None = Form(None),
    category: str | None = Form(None),
    tags: str | None = Form(None),
    mcp_dependency: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SkillRead:
    ensure_buckets()
    skill_id = uuid.uuid4()
    object_name = f"{skill_id}/{file.filename}"
    content = await file.read()
    put_bytes(
        settings.minio_skills_bucket,
        object_name,
        content,
        file.content_type or "application/octet-stream",
    )
    skill = await skill_crud.create_skill(
        db,
        id=skill_id,
        name=name,
        version=version,
        description=description,
        category=category,
        tags=_split_csv(tags),
        created_by=current_user.id,
        bucket_path=object_name,
        mcp_dependency=[uuid.UUID(v) for v in _split_csv(mcp_dependency)],
    )
    return SkillRead.model_validate(skill)


@router.get("", response_model=list[SkillRead])
async def list_skills(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[SkillRead]:
    skills = await skill_crud.list_skills(db)
    return [SkillRead.model_validate(s) for s in skills]
