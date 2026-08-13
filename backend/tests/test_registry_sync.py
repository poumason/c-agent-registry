import uuid

from app.core.config import get_settings
from app.crud import fab as fab_crud
from app.crud import mcp as mcp_crud
from app.crud import skill as skill_crud
from app.models.enums import UserRole
from app.services.storage import get_minio_client, put_bytes
from tests.conftest import auth_headers, login, make_user

settings = get_settings()


async def _seed_skill(db_session, user, name="sync-skill", content=b"print('hi')"):
    """Direct crud + MinIO seeding — there's no POST /skills anymore (skills arrive
    via sync now, see docs/registry-sync.md), so tests build rows the same way a real
    sync integration eventually would."""
    object_name = f"seed/{name}/main.py"
    put_bytes(settings.minio_skills_bucket, object_name, content, "text/plain")
    return await skill_crud.create_skill(
        db_session,
        id=uuid.uuid4(),
        name=name,
        version="1.0.0",
        description=None,
        category=None,
        tags=[],
        created_by=user.id,
        bucket_path=object_name,
        mcp_dependency=[],
    )


async def _seed_mcp_with_fab(db_session, user, *, host: str, name="sync-mcp", fab_value="F01"):
    mcp = await mcp_crud.create_mcp(
        db_session,
        name=name,
        version="1.0.0",
        description=None,
        category=None,
        tags=[],
        created_by=user.id,
    )
    fab = await fab_crud.create_fab(db_session, fab=fab_value)
    mcp_fab = await mcp_crud.create_mcp_fab(db_session, mcp_id=mcp.id, fab_id=fab.id, host=host)
    return mcp, fab, mcp_fab


async def test_skill_defaults_to_available_and_unsynced(client, db_session):
    user = await make_user(db_session, email="sk1@example.com", role=UserRole.member)
    skill = await _seed_skill(db_session, user)
    assert skill.status.value == "available"
    assert skill.last_synced_at is None


async def test_skill_sync_marks_missing_object_unavailable_and_flags_changed(client, db_session):
    user = await make_user(db_session, email="sk2@example.com", role=UserRole.member)
    token = await login(client, "sk2@example.com")
    skill = await _seed_skill(db_session, user, "sync-skill-2")

    resp = await client.post("/api/v1/skills/sync", headers=auth_headers(token))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] >= 1
    synced = next(s for s in body["items"] if s["id"] == str(skill.id))
    assert synced["status"] == "available"
    assert synced["last_synced_at"] is not None
    # available -> available on a never-synced row is not a change.
    assert synced["changed"] is False

    get_minio_client().remove_object(settings.minio_skills_bucket, skill.bucket_path)

    resp = await client.post("/api/v1/skills/sync", headers=auth_headers(token))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    synced = next(s for s in body["items"] if s["id"] == str(skill.id))
    assert synced["status"] == "unavailable"
    assert synced["changed"] is True
    assert body["unavailable"] >= 1


async def test_mcp_sync_marks_unreachable_host_unavailable_and_flags_changed(client, db_session):
    user = await make_user(db_session, email="mc1@example.com", role=UserRole.member)
    token = await login(client, "mc1@example.com")

    mcp, fab, _ = await _seed_mcp_with_fab(
        db_session, user, host="http://127.0.0.1:1", name="unreachable-mcp", fab_value="F02"
    )
    stdio_mcp, stdio_fab, _ = await _seed_mcp_with_fab(
        db_session, user, host="npx some-mcp-server", name="stdio-mcp", fab_value="F03"
    )

    resp = await client.post("/api/v1/mcps/sync", headers=auth_headers(token))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    by_id = {m["id"]: m for m in body["items"]}

    unreachable_fab_row = next(
        f for f in by_id[str(mcp.id)]["fabs"] if f["fab_id"] == str(fab.id)
    )
    assert unreachable_fab_row["status"] == "unavailable"
    assert unreachable_fab_row["changed"] is True  # was "available" by default before sync

    stdio_fab_row = next(
        f for f in by_id[str(stdio_mcp.id)]["fabs"] if f["fab_id"] == str(stdio_fab.id)
    )
    assert stdio_fab_row["status"] == "available"
    assert stdio_fab_row["changed"] is False


async def test_mcp_fab_assignment_rejects_duplicate_and_unknown_mcp(client, db_session):
    user = await make_user(db_session, email="mc2@example.com", role=UserRole.member)
    token = await login(client, "mc2@example.com")
    mcp, fab, _ = await _seed_mcp_with_fab(db_session, user, host="https://a.example.com")

    # duplicate (mcp, fab) assignment
    resp = await client.post(
        f"/api/v1/mcps/{mcp.id}/fabs",
        headers=auth_headers(token),
        json={"fab_id": str(fab.id), "host": "https://b.example.com"},
    )
    assert resp.status_code == 409

    # unknown mcp id
    resp = await client.post(
        f"/api/v1/mcps/{uuid.uuid4()}/fabs",
        headers=auth_headers(token),
        json={"fab_id": str(fab.id), "host": "https://c.example.com"},
    )
    assert resp.status_code == 404


async def test_mcp_fab_remove(client, db_session):
    user = await make_user(db_session, email="mc3@example.com", role=UserRole.member)
    token = await login(client, "mc3@example.com")
    mcp, fab, _ = await _seed_mcp_with_fab(db_session, user, host="https://a.example.com")

    resp = await client.delete(f"/api/v1/mcps/{mcp.id}/fabs/{fab.id}", headers=auth_headers(token))
    assert resp.status_code == 204

    resp = await client.get(f"/api/v1/mcps/{mcp.id}/fabs", headers=auth_headers(token))
    assert resp.json() == []

    resp = await client.delete(f"/api/v1/mcps/{mcp.id}/fabs/{fab.id}", headers=auth_headers(token))
    assert resp.status_code == 404


async def test_skill_fab_assign_list_and_reject_duplicate(client, db_session):
    user = await make_user(db_session, email="sf1@example.com", role=UserRole.member)
    token = await login(client, "sf1@example.com")
    skill = await _seed_skill(db_session, user, "fab-skill")
    fab = await fab_crud.create_fab(db_session, fab="F41")

    resp = await client.post(
        f"/api/v1/skills/{skill.id}/fabs",
        headers=auth_headers(token),
        json={"fab_id": str(fab.id)},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["skill_id"] == str(skill.id)
    assert body["fab_id"] == str(fab.id)
    assert body["created_at"]

    resp = await client.get(f"/api/v1/skills/{skill.id}/fabs", headers=auth_headers(token))
    assert resp.status_code == 200
    assert [f["fab_id"] for f in resp.json()] == [str(fab.id)]

    # GET /skills reflects the assignment too.
    resp = await client.get("/api/v1/skills", headers=auth_headers(token))
    listed = next(s for s in resp.json() if s["id"] == str(skill.id))
    assert [f["fab_id"] for f in listed["fabs"]] == [str(fab.id)]

    # duplicate assignment rejected
    resp = await client.post(
        f"/api/v1/skills/{skill.id}/fabs",
        headers=auth_headers(token),
        json={"fab_id": str(fab.id)},
    )
    assert resp.status_code == 409

    # unknown skill
    resp = await client.post(
        f"/api/v1/skills/{uuid.uuid4()}/fabs",
        headers=auth_headers(token),
        json={"fab_id": str(fab.id)},
    )
    assert resp.status_code == 404


async def test_skill_fab_remove(client, db_session):
    user = await make_user(db_session, email="sf2@example.com", role=UserRole.member)
    token = await login(client, "sf2@example.com")
    skill = await _seed_skill(db_session, user, "fab-skill-2")
    fab = await fab_crud.create_fab(db_session, fab="F42")
    await client.post(
        f"/api/v1/skills/{skill.id}/fabs", headers=auth_headers(token), json={"fab_id": str(fab.id)}
    )

    resp = await client.delete(
        f"/api/v1/skills/{skill.id}/fabs/{fab.id}", headers=auth_headers(token)
    )
    assert resp.status_code == 204

    resp = await client.get(f"/api/v1/skills/{skill.id}/fabs", headers=auth_headers(token))
    assert resp.json() == []


async def test_ai_model_create_list_sync(client, db_session):
    await make_user(db_session, email="ai1@example.com", role=UserRole.member)
    token = await login(client, "ai1@example.com")

    resp = await client.post(
        "/api/v1/models",
        headers=auth_headers(token),
        json={"name": "Claude Sonnet 5", "provider": "anthropic", "model_id": "claude-sonnet-5"},
    )
    assert resp.status_code == 201, resp.text
    model = resp.json()
    assert model["status"] == "available"
    assert model["last_synced_at"] is None

    resp = await client.get("/api/v1/models", headers=auth_headers(token))
    assert resp.status_code == 200
    assert any(m["id"] == model["id"] for m in resp.json())

    resp = await client.post("/api/v1/models/sync", headers=auth_headers(token))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    synced = next(m for m in body["items"] if m["id"] == model["id"])
    assert synced["status"] == "available"
    assert synced["last_synced_at"] is not None
