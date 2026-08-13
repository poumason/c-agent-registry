from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.crud import fab as fab_crud
from app.db.base import get_db
from app.models.user import User
from app.schemas.fab import FabCreate, FabRead

router = APIRouter(prefix="/fabs", tags=["fabs"])


@router.post("", response_model=FabRead, status_code=status.HTTP_201_CREATED)
async def create_fab(
    payload: FabCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FabRead:
    if await fab_crud.get_by_value(db, payload.fab) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Fab already exists")
    fab = await fab_crud.create_fab(db, fab=payload.fab)
    return FabRead.model_validate(fab)


@router.get("", response_model=list[FabRead])
async def list_fabs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[FabRead]:
    fabs = await fab_crud.list_fabs(db)
    return [FabRead.model_validate(f) for f in fabs]
