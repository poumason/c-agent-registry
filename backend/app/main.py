from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.crud import user as user_crud
from app.db.base import async_session_factory
from app.models.enums import UserRole
from app.services.storage import ensure_buckets

settings = get_settings()


async def _bootstrap_admin() -> None:
    async with async_session_factory() as db:
        if await user_crud.count_admins(db) > 0:
            return
        await user_crud.create_user(
            db,
            email=settings.bootstrap_admin_email,
            password=settings.bootstrap_admin_password,
            name=settings.bootstrap_admin_name,
            role=UserRole.admin,
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_buckets()
    await _bootstrap_admin()
    yield


app = FastAPI(title="Agent Registry API", version="0.1.0", lifespan=lifespan)
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
