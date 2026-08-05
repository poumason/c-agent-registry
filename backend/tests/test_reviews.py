from app.models.enums import UserRole
from tests.conftest import auth_headers, login, make_user


async def _create_agent_and_draft_version(client, token, slug="agent-r"):
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


async def test_submit_creates_review_for_eligible_reviewers(client, db_session):
    await make_user(db_session, email="member@example.com", role=UserRole.member)
    await make_user(db_session, email="owner@example.com", role=UserRole.owner)
    member_token = await login(client, "member@example.com")

    version_slug = await _create_agent_and_draft_version(client, member_token, "agent-r1")

    resp = await client.post(
        f"/api/v1/versions/{version_slug}/submit", headers=auth_headers(member_token)
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "in_review"

    resp = await client.get(
        f"/api/v1/versions/{version_slug}/reviews", headers=auth_headers(member_token)
    )
    reviews = resp.json()
    assert len(reviews) == 1
    assert reviews[0]["result"] == "pending"


async def test_only_assigned_reviewer_can_decide(client, db_session):
    # "unrelated" is a plain member with no relationship to this agent, so they are
    # not an eligible reviewer (unlike a system owner/admin, who would be).
    await make_user(db_session, email="member2@example.com", role=UserRole.member)
    await make_user(db_session, email="owner3@example.com", role=UserRole.owner)
    await make_user(db_session, email="unrelated@example.com", role=UserRole.member)
    member_token = await login(client, "member2@example.com")
    unrelated_token = await login(client, "unrelated@example.com")

    version_slug = await _create_agent_and_draft_version(client, member_token, "agent-r2")
    await client.post(f"/api/v1/versions/{version_slug}/submit", headers=auth_headers(member_token))

    resp = await client.get(
        f"/api/v1/versions/{version_slug}/reviews", headers=auth_headers(member_token)
    )
    review_id = resp.json()[0]["id"]

    resp = await client.post(
        f"/api/v1/reviews/{review_id}/decision",
        headers=auth_headers(unrelated_token),
        json={"result": "approved"},
    )
    assert resp.status_code == 403


async def test_rejection_sets_version_rejected_and_no_package(client, db_session):
    await make_user(db_session, email="member3@example.com", role=UserRole.member)
    await make_user(db_session, email="owner4@example.com", role=UserRole.owner)
    member_token = await login(client, "member3@example.com")
    owner_token = await login(client, "owner4@example.com")

    version_slug = await _create_agent_and_draft_version(client, member_token, "agent-r3")
    await client.post(f"/api/v1/versions/{version_slug}/submit", headers=auth_headers(member_token))

    resp = await client.get(
        f"/api/v1/versions/{version_slug}/reviews", headers=auth_headers(member_token)
    )
    review_id = resp.json()[0]["id"]

    resp = await client.post(
        f"/api/v1/reviews/{review_id}/decision",
        headers=auth_headers(owner_token),
        json={"result": "rejected"},
    )
    assert resp.status_code == 200

    resp = await client.get(
        f"/api/v1/versions/{version_slug}", headers=auth_headers(member_token)
    )
    body = resp.json()
    assert body["status"] == "rejected"
    assert body["package_path"] is None

    resp = await client.get(
        f"/api/v1/versions/{version_slug}/download", headers=auth_headers(member_token)
    )
    assert resp.status_code == 409
