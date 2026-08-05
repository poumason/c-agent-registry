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


async def test_submit_rejects_ineligible_reviewer(client, db_session):
    await make_user(db_session, email="member@example.com", role=UserRole.member)
    plain = await make_user(db_session, email="plain@example.com", role=UserRole.member)
    member_token = await login(client, "member@example.com")
    version_slug = await _create_agent_and_draft_version(client, member_token, "agent-r0")

    # a plain member (not reviewer/admin) can't be named as reviewer
    resp = await client.post(
        f"/api/v1/versions/{version_slug}/submit",
        headers=auth_headers(member_token),
        json={"reviewer_ids": [str(plain.id)]},
    )
    assert resp.status_code == 400


async def test_submit_rejects_self_assignment(client, db_session):
    member = await make_user(db_session, email="member0b@example.com", role=UserRole.reviewer)
    member_token = await login(client, "member0b@example.com")
    version_slug = await _create_agent_and_draft_version(client, member_token, "agent-r0b")

    resp = await client.post(
        f"/api/v1/versions/{version_slug}/submit",
        headers=auth_headers(member_token),
        json={"reviewer_ids": [str(member.id)]},
    )
    assert resp.status_code == 400


async def test_submit_creates_review_for_named_reviewer(client, db_session):
    await make_user(db_session, email="member1@example.com", role=UserRole.member)
    reviewer = await make_user(db_session, email="reviewer1@example.com", role=UserRole.reviewer)
    member_token = await login(client, "member1@example.com")

    version_slug = await _create_agent_and_draft_version(client, member_token, "agent-r1")

    resp = await client.post(
        f"/api/v1/versions/{version_slug}/submit",
        headers=auth_headers(member_token),
        json={"reviewer_ids": [str(reviewer.id)]},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "in_review"

    resp = await client.get(
        f"/api/v1/versions/{version_slug}/reviews", headers=auth_headers(member_token)
    )
    reviews = resp.json()
    assert len(reviews) == 1
    assert reviews[0]["result"] == "pending"
    assert reviews[0]["reviewer_id"] == str(reviewer.id)


async def test_only_the_assigned_reviewer_can_decide(client, db_session):
    await make_user(db_session, email="member2@example.com", role=UserRole.member)
    await make_user(db_session, email="assigned@example.com", role=UserRole.reviewer)
    # eligible in general (system role reviewer) but never actually assigned
    await make_user(db_session, email="unassigned@example.com", role=UserRole.reviewer)
    member_token = await login(client, "member2@example.com")
    unassigned_token = await login(client, "unassigned@example.com")

    version_slug = await _create_agent_and_draft_version(client, member_token, "agent-r2")
    resp = await client.get(
        "/api/v1/reviewers", headers=auth_headers(member_token)
    )
    assigned_id = next(c["id"] for c in resp.json() if c["email"] == "assigned@example.com")
    await client.post(
        f"/api/v1/versions/{version_slug}/submit",
        headers=auth_headers(member_token),
        json={"reviewer_ids": [assigned_id]},
    )

    resp = await client.get(
        f"/api/v1/versions/{version_slug}/reviews", headers=auth_headers(member_token)
    )
    review_id = resp.json()[0]["id"]

    resp = await client.post(
        f"/api/v1/reviews/{review_id}/decision",
        headers=auth_headers(unassigned_token),
        json={"result": "approved"},
    )
    assert resp.status_code == 403


async def test_rejection_sets_version_rejected_and_no_package(client, db_session):
    await make_user(db_session, email="member3@example.com", role=UserRole.member)
    reviewer = await make_user(db_session, email="reviewer3@example.com", role=UserRole.reviewer)
    member_token = await login(client, "member3@example.com")
    reviewer_token = await login(client, "reviewer3@example.com")

    version_slug = await _create_agent_and_draft_version(client, member_token, "agent-r3")
    await client.post(
        f"/api/v1/versions/{version_slug}/submit",
        headers=auth_headers(member_token),
        json={"reviewer_ids": [str(reviewer.id)]},
    )

    resp = await client.get(
        f"/api/v1/versions/{version_slug}/reviews", headers=auth_headers(member_token)
    )
    review_id = resp.json()[0]["id"]

    resp = await client.post(
        f"/api/v1/reviews/{review_id}/decision",
        headers=auth_headers(reviewer_token),
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
