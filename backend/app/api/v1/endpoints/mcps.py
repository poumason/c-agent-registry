from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.crud import mcp as mcp_crud
from app.db.base import get_db
from app.models.user import User
from app.schemas.mcp import MCPCreate, MCPRead

router = APIRouter(prefix="/mcps", tags=["mcps"])


@router.post("", response_model=MCPRead, status_code=201)
async def create_mcp(
    payload: MCPCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MCPRead:
    mcp = await mcp_crud.create_mcp(
        db,
        name=payload.name,
        version=payload.version,
        description=payload.description,
        category=payload.category,
        tags=payload.tags,
        created_by=current_user.id,
        host=payload.host,
    )
    return MCPRead.model_validate(mcp)


@router.get("", response_model=list[MCPRead])
async def list_mcps(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[MCPRead]:
    mcps = await mcp_crud.list_mcps(db)
    return [MCPRead.model_validate(m) for m in mcps]
