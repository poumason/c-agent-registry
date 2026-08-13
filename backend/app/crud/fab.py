import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fab import Fab


async def get_by_id(db: AsyncSession, fab_id: uuid.UUID) -> Fab | None:
    return await db.get(Fab, fab_id)


async def list_fabs(db: AsyncSession) -> list[Fab]:
    result = await db.execute(select(Fab).order_by(Fab.fab))
    return list(result.scalars().all())


async def get_by_value(db: AsyncSession, fab: str) -> Fab | None:
    result = await db.execute(select(Fab).where(Fab.fab == fab))
    return result.scalar_one_or_none()


async def create_fab(db: AsyncSession, *, fab: str) -> Fab:
    row = Fab(fab=fab)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row
