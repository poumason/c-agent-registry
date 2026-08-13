import uuid

from app.core.config import get_settings
from app.crud import mcp as mcp_crud
from app.crud import registry as registry_crud
from app.crud import skill as skill_crud
from app.models.enums import UserRole
from app.schemas.registry import RegistryItem
from app.services.storage import put_bytes
from tests.conftest import auth_headers, login, make_user

settings = get_settings()


async def _create_agent_and_draft_version(client, token, slug):
    resp = await client.post(
        "/api/v1/agents",
        headers=auth_headers(token),
        json={"slug": slug, "name": slug, "visibility": "internal"},
    )
    assert resp.status_code == 201
    resp = await client.post(
        f"/api/v1/agents/{slug}/versions",
        headers=auth_headers(token),
        json={"url": "https://example.com", "streaming": False},
    )
    assert resp.status_code == 201
    return resp.json()["slug"]


async def _seed_skill(db_session, user, name="skill-x"):
    """Direct crud + MinIO seeding — there's no POST /skills anymore (skills arrive
    via sync now, see docs/registry-sync.md)."""
    object_name = f"seed/{name}/main.py"
    put_bytes(settings.minio_skills_bucket, object_name, b"print('hi')", "text/plain")
    skill = await skill_crud.create_skill(
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
    return {"id": str(skill.id), "name": skill.name}


async def _seed_mcp(db_session, user, name="mcp-a"):
    """Direct crud seeding — there's no POST /mcps anymore either (see MCPFab)."""
    mcp = await mcp_crud.create_mcp(
        db_session,
        name=name,
        version="1.0.0",
        description=None,
        category=None,
        tags=[],
        created_by=user.id,
    )
    return {"id": str(mcp.id), "name": mcp.name}


async def test_dependency_rejects_unknown_id(client, db_session):
    await make_user(db_session, email="dm@example.com", role=UserRole.member)
    token = await login(client, "dm@example.com")
    version_slug = await _create_agent_and_draft_version(client, token, "agent-d1")

    resp = await client.post(
        f"/api/v1/versions/{version_slug}/dependencies",
        headers=auth_headers(token),
        json={"dependency_id": str(uuid.uuid4()), "type": "skill"},
    )
    assert resp.status_code == 404


async def test_dependency_polymorphic_skill_and_mcp(client, db_session):
    user = await make_user(db_session, email="dm2@example.com", role=UserRole.member)
    token = await login(client, "dm2@example.com")
    version_slug = await _create_agent_and_draft_version(client, token, "agent-d2")

    skill = await _seed_skill(db_session, user, "skill-a")
    mcp = await _seed_mcp(db_session, user, "mcp-a")

    resp = await client.post(
        f"/api/v1/versions/{version_slug}/dependencies",
        headers=auth_headers(token),
        json={"dependency_id": skill["id"], "type": "skill"},
    )
    assert resp.status_code == 201

    resp = await client.post(
        f"/api/v1/versions/{version_slug}/dependencies",
        headers=auth_headers(token),
        json={"dependency_id": mcp["id"], "type": "mcp"},
    )
    assert resp.status_code == 201

    resp = await client.get(
        f"/api/v1/versions/{version_slug}/dependencies", headers=auth_headers(token)
    )
    deps = resp.json()
    assert {d["type"] for d in deps} == {"skill", "mcp"}


async def test_dependencies_locked_after_submit(client, db_session):
    user = await make_user(db_session, email="dm3@example.com", role=UserRole.member)
    reviewer = await make_user(
        db_session, email="revd3@example.com", role=UserRole.reviewer
    )
    token = await login(client, "dm3@example.com")
    version_slug = await _create_agent_and_draft_version(client, token, "agent-d3")

    skill = await _seed_skill(db_session, user, "skill-locked")
    await client.post(
        f"/api/v1/versions/{version_slug}/submit",
        headers=auth_headers(token),
        json={"reviewer_ids": [str(reviewer.id)]},
    )

    resp = await client.post(
        f"/api/v1/versions/{version_slug}/dependencies",
        headers=auth_headers(token),
        json={"dependency_id": skill["id"], "type": "skill"},
    )
    assert resp.status_code == 409


async def test_dependency_omitted_source_defaults_to_legacy(client, db_session):
    # Backward compatibility: existing clients that never send `source` (like the
    # requests above) keep working against the first-party skills/mcps tables.
    user = await make_user(db_session, email="dm4@example.com", role=UserRole.member)
    token = await login(client, "dm4@example.com")
    version_slug = await _create_agent_and_draft_version(client, token, "agent-d4")
    skill = await _seed_skill(db_session, user, "skill-legacy")

    resp = await client.post(
        f"/api/v1/versions/{version_slug}/dependencies",
        headers=auth_headers(token),
        json={"dependency_id": skill["id"], "type": "skill"},
    )
    assert resp.status_code == 201
    assert resp.json()["source"] == "legacy"


async def test_dependency_registry_source_rejects_when_not_synced(client, db_session):
    await make_user(db_session, email="dm5@example.com", role=UserRole.member)
    token = await login(client, "dm5@example.com")
    version_slug = await _create_agent_and_draft_version(client, token, "agent-d5")

    resp = await client.post(
        f"/api/v1/versions/{version_slug}/dependencies",
        headers=auth_headers(token),
        json={"dependency_id": "not-mirrored-yet", "type": "skill", "source": "registry"},
    )
    assert resp.status_code == 404


async def test_dependency_registry_source_accepts_mirrored_item(client, db_session, monkeypatch):
    # Simulates a real sync having populated the skillhub-registry stub with one
    # skill — the actual population logic is what the real sync integration
    # replaces (see app/crud/registry.py's PLACEHOLDER note); this proves the
    # dependency endpoint correctly recognizes whatever ends up in that store.
    item = RegistryItem(id="pdf-parser-skill", name="PDF Parser", version="2.1.0", category=None, deprecated=False, last_seen_at=None)
    monkeypatch.setitem(registry_crud._state["skillhub-registry"], "items", [item])

    await make_user(db_session, email="dm6@example.com", role=UserRole.member)
    token = await login(client, "dm6@example.com")
    version_slug = await _create_agent_and_draft_version(client, token, "agent-d6")

    resp = await client.post(
        f"/api/v1/versions/{version_slug}/dependencies",
        headers=auth_headers(token),
        json={"dependency_id": "pdf-parser-skill", "type": "skill", "source": "registry"},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["source"] == "registry"


async def test_dependency_mcp_has_no_registry_source(client, db_session):
    # MCP dependencies resolve against the real, availability-synced mcps table
    # directly (see app/api/v1/endpoints/mcps.py) — there's no separate "MCP
    # registry" mirror to source=registry from, unlike skill's SkillHub Registry.
    await make_user(db_session, email="dm7@example.com", role=UserRole.member)
    token = await login(client, "dm7@example.com")
    version_slug = await _create_agent_and_draft_version(client, token, "agent-d7")

    resp = await client.post(
        f"/api/v1/versions/{version_slug}/dependencies",
        headers=auth_headers(token),
        json={"dependency_id": "whatever", "type": "mcp", "source": "registry"},
    )
    assert resp.status_code == 400
