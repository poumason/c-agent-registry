import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.crud import user as user_crud
from app.db.base import Base, async_session_factory, engine, get_db
from app.main import app
from app.models.enums import UserRole
from app.services.storage import ensure_buckets


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _prepare_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    ensure_buckets()
    yield
    await engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def _clean_tables():
    yield
    async with engine.begin() as conn:
        table_names = ", ".join(f'"{t.name}"' for t in Base.metadata.sorted_tables)
        await conn.execute(text(f"TRUNCATE TABLE {table_names} RESTART IDENTITY CASCADE"))


@pytest_asyncio.fixture
async def db_session():
    async with async_session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client():
    async def _get_db_override():
        async with async_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = _get_db_override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


async def make_user(
    db_session, *, email: str, password: str = "password123", role: UserRole = UserRole.member
):
    return await user_crud.create_user(
        db_session, email=email, password=password, name=email.split("@")[0], role=role
    )


async def login(client: AsyncClient, email: str, password: str = "password123") -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
