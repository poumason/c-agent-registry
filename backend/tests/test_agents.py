from app.models.enums import UserRole
from tests.conftest import auth_headers, login, make_user


async def test_member_can_create_agent_and_becomes_admin_member(client, db_session):
    await make_user(db_session, email="m1@example.com", role=UserRole.member)
    token = await login(client, "m1@example.com")

    resp = await client.post(
        "/api/v1/agents",
        headers=auth_headers(token),
        json={"slug": "agent-a", "name": "Agent A", "visibility": "private"},
    )
    assert resp.status_code == 201, resp.text
    agent = resp.json()

    resp = await client.get(
        f"/api/v1/agents/{agent['slug']}/members", headers=auth_headers(token)
    )
    assert resp.status_code == 200
    members = resp.json()
    assert len(members) == 1
    assert members[0]["role"] == "admin"


async def test_private_agent_hidden_from_unrelated_member(client, db_session):
    await make_user(db_session, email="owner@example.com", role=UserRole.member)
    await make_user(db_session, email="stranger@example.com", role=UserRole.member)
    owner_token = await login(client, "owner@example.com")
    stranger_token = await login(client, "stranger@example.com")

    resp = await client.post(
        "/api/v1/agents",
        headers=auth_headers(owner_token),
        json={"slug": "private-agent", "name": "Private", "visibility": "private"},
    )
    assert resp.status_code == 201

    resp = await client.get(
        "/api/v1/agents/private-agent", headers=auth_headers(stranger_token)
    )
    assert resp.status_code == 404

    resp = await client.get("/api/v1/agents", headers=auth_headers(stranger_token))
    slugs = {a["slug"] for a in resp.json()}
    assert "private-agent" not in slugs


async def test_system_owner_can_manage_any_agent(client, db_session):
    await make_user(db_session, email="creator@example.com", role=UserRole.member)
    await make_user(db_session, email="sysowner@example.com", role=UserRole.owner)
    creator_token = await login(client, "creator@example.com")
    owner_token = await login(client, "sysowner@example.com")

    resp = await client.post(
        "/api/v1/agents",
        headers=auth_headers(creator_token),
        json={"slug": "agent-b", "name": "Agent B", "visibility": "private"},
    )
    assert resp.status_code == 201

    # system owner (not a member) can still create a version - "調整 agent 的所有參數"
    resp = await client.post(
        "/api/v1/agents/agent-b/versions",
        headers=auth_headers(owner_token),
        json={"url": "https://example.com", "streaming": False},
    )
    assert resp.status_code == 201, resp.text


async def test_max_two_active_versions_per_agent(client, db_session):
    # Two system owners: one submits, the other is the eligible reviewer
    # (a submitter is never eligible to review their own submission).
    await make_user(db_session, email="owner2@example.com", role=UserRole.owner)
    await make_user(db_session, email="reviewer2@example.com", role=UserRole.owner)
    token = await login(client, "owner2@example.com")
    reviewer_token = await login(client, "reviewer2@example.com")

    resp = await client.post(
        "/api/v1/agents",
        headers=auth_headers(token),
        json={"slug": "agent-c", "name": "Agent C", "visibility": "internal"},
    )
    assert resp.status_code == 201

    slugs = []
    for _ in range(3):
        resp = await client.post(
            "/api/v1/agents/agent-c/versions",
            headers=auth_headers(token),
            json={"url": "https://example.com", "streaming": False},
        )
        assert resp.status_code == 201
        version_slug = resp.json()["slug"]
        slugs.append(version_slug)

        resp = await client.post(
            f"/api/v1/versions/{version_slug}/submit", headers=auth_headers(token)
        )
        assert resp.status_code == 200, resp.text

        resp = await client.get(
            f"/api/v1/versions/{version_slug}/reviews", headers=auth_headers(token)
        )
        review_id = resp.json()[0]["id"]
        resp = await client.post(
            f"/api/v1/reviews/{review_id}/decision",
            headers=auth_headers(reviewer_token),
            json={"result": "approved"},
        )
        assert resp.status_code == 200, resp.text

    # activate first two - should succeed
    for version_slug in slugs[:2]:
        resp = await client.post(
            f"/api/v1/versions/{version_slug}/activate", headers=auth_headers(token)
        )
        assert resp.status_code == 200, resp.text

    # third activation should be rejected (max 2 active)
    resp = await client.post(
        f"/api/v1/versions/{slugs[2]}/activate", headers=auth_headers(token)
    )
    assert resp.status_code == 409
