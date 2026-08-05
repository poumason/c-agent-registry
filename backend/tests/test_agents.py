from app.models.enums import UserRole
from tests.conftest import auth_headers, login, make_user


async def test_member_can_create_agent_and_becomes_owner_member(client, db_session):
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
    assert members[0]["role"] == "owner"


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


async def test_system_admin_can_manage_any_agent(client, db_session):
    await make_user(db_session, email="creator@example.com", role=UserRole.member)
    await make_user(db_session, email="sysadmin@example.com", role=UserRole.admin)
    creator_token = await login(client, "creator@example.com")
    admin_token = await login(client, "sysadmin@example.com")

    resp = await client.post(
        "/api/v1/agents",
        headers=auth_headers(creator_token),
        json={"slug": "agent-b", "name": "Agent B", "visibility": "private"},
    )
    assert resp.status_code == 201

    # system admin (not a member of this agent) can still manage it
    resp = await client.post(
        "/api/v1/agents/agent-b/versions",
        headers=auth_headers(admin_token),
        json={"url": "https://example.com", "streaming": False},
    )
    assert resp.status_code == 201, resp.text


async def test_reviewer_without_membership_cannot_manage_agent(client, db_session):
    # Being a system 'reviewer' only makes you assignable as a reviewer - it does not
    # grant edit access to agents you're not a member of.
    await make_user(db_session, email="creator2@example.com", role=UserRole.member)
    await make_user(db_session, email="rev@example.com", role=UserRole.reviewer)
    creator_token = await login(client, "creator2@example.com")
    reviewer_token = await login(client, "rev@example.com")

    resp = await client.post(
        "/api/v1/agents",
        headers=auth_headers(creator_token),
        json={"slug": "agent-b2", "name": "Agent B2", "visibility": "internal"},
    )
    assert resp.status_code == 201

    resp = await client.post(
        "/api/v1/agents/agent-b2/versions",
        headers=auth_headers(reviewer_token),
        json={"url": "https://example.com", "streaming": False},
    )
    assert resp.status_code == 403


async def test_owner_can_invite_editor_but_cannot_remove_owner(client, db_session):
    owner_user = await make_user(db_session, email="owner3@example.com", role=UserRole.member)
    editor_user = await make_user(db_session, email="editor3@example.com", role=UserRole.member)
    owner_token = await login(client, "owner3@example.com")
    editor_token = await login(client, "editor3@example.com")

    resp = await client.post(
        "/api/v1/agents",
        headers=auth_headers(owner_token),
        json={"slug": "agent-inv", "name": "Agent Inv", "visibility": "internal"},
    )
    assert resp.status_code == 201

    # invite editor3 - always granted editor rights (no role field to choose)
    resp = await client.post(
        "/api/v1/agents/agent-inv/members",
        headers=auth_headers(owner_token),
        json={"user_id": str(editor_user.id)},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["role"] == "editor"

    # editor has equal content permissions - can create a version
    resp = await client.post(
        "/api/v1/agents/agent-inv/versions",
        headers=auth_headers(editor_token),
        json={"url": "https://example.com", "streaming": False},
    )
    assert resp.status_code == 201

    # editor cannot manage membership (only owner/admin can)
    resp = await client.delete(
        f"/api/v1/agents/agent-inv/members/{owner_user.id}",
        headers=auth_headers(editor_token),
    )
    assert resp.status_code == 403

    # owner cannot remove themself (the owner row) via this endpoint
    resp = await client.delete(
        f"/api/v1/agents/agent-inv/members/{owner_user.id}",
        headers=auth_headers(owner_token),
    )
    assert resp.status_code == 409

    # owner can remove the editor
    resp = await client.delete(
        f"/api/v1/agents/agent-inv/members/{editor_user.id}",
        headers=auth_headers(owner_token),
    )
    assert resp.status_code == 204


async def test_max_two_active_versions_per_agent(client, db_session):
    await make_user(db_session, email="owner2@example.com", role=UserRole.member)
    await make_user(db_session, email="reviewer2@example.com", role=UserRole.reviewer)
    token = await login(client, "owner2@example.com")
    reviewer_token = await login(client, "reviewer2@example.com")

    resp = await client.get("/api/v1/reviewers", headers=auth_headers(token))
    reviewer_id = next(
        c["id"] for c in resp.json() if c["email"] == "reviewer2@example.com"
    )

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
            f"/api/v1/versions/{version_slug}/submit",
            headers=auth_headers(token),
            json={"reviewer_ids": [reviewer_id]},
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
