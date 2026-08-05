import uuid

from app.models.enums import UserRole
from tests.conftest import auth_headers, login, make_user


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


async def _upload_skill(client, token, name="skill-x"):
    resp = await client.post(
        "/api/v1/skills",
        headers=auth_headers(token),
        files={"file": ("main.py", b"print('hi')", "text/plain")},
        data={"name": name, "version": "1.0.0"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_create_mcp_and_list(client, db_session):
    await make_user(db_session, email="m@example.com", role=UserRole.member)
    token = await login(client, "m@example.com")
    resp = await client.post(
        "/api/v1/mcps",
        headers=auth_headers(token),
        json={"name": "mcp-1", "version": "1.0.0", "host": "https://mcp.example.com"},
    )
    assert resp.status_code == 201, resp.text

    resp = await client.get("/api/v1/mcps", headers=auth_headers(token))
    assert any(m["name"] == "mcp-1" for m in resp.json())


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
    await make_user(db_session, email="dm2@example.com", role=UserRole.member)
    token = await login(client, "dm2@example.com")
    version_slug = await _create_agent_and_draft_version(client, token, "agent-d2")

    skill = await _upload_skill(client, token, "skill-a")
    mcp_resp = await client.post(
        "/api/v1/mcps",
        headers=auth_headers(token),
        json={"name": "mcp-a", "version": "1.0.0", "host": "https://mcp.example.com"},
    )
    mcp = mcp_resp.json()

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
    await make_user(db_session, email="dm3@example.com", role=UserRole.member)
    reviewer = await make_user(
        db_session, email="revd3@example.com", role=UserRole.reviewer
    )
    token = await login(client, "dm3@example.com")
    version_slug = await _create_agent_and_draft_version(client, token, "agent-d3")

    skill = await _upload_skill(client, token, "skill-locked")
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
