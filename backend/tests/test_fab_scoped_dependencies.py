"""A version's dependency set must cover every fab the version is deployed to (see
app/services/fab_scope.py). These tests exercise both directions of that rule:
adding a dependency that doesn't cover the version's current fabs, and deploying to
a new fab that an existing dependency doesn't reach — plus the type=model lookup
bug fixed alongside this (it used to resolve against mcp_crud instead of
ai_model_crud, so every model dependency 404'd)."""

import uuid

from app.core.config import get_settings
from app.crud import ai_model as ai_model_crud
from app.crud import mcp as mcp_crud
from app.crud import skill as skill_crud
from app.models.enums import AvailabilityStatus, UserRole
from app.services.storage import put_bytes
from tests.conftest import auth_headers, login, make_user

settings = get_settings()


async def _create_agent_and_draft_version(client, token, slug):
    resp = await client.post(
        "/api/v1/agents",
        headers=auth_headers(token),
        json={"slug": slug, "name": slug, "visibility": "internal"},
    )
    assert resp.status_code == 201, resp.text
    resp = await client.post(
        f"/api/v1/agents/{slug}/versions", headers=auth_headers(token), json={}
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["slug"]


async def _create_fab(client, token, fab="F01"):
    resp = await client.post("/api/v1/fabs", headers=auth_headers(token), json={"fab": fab})
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _seed_skill(db_session, user, name="skill-x"):
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
    return skill


async def _assign_skill_fab(client, token, skill_id, fab_id):
    resp = await client.post(
        f"/api/v1/skills/{skill_id}/fabs", headers=auth_headers(token), json={"fab_id": fab_id}
    )
    assert resp.status_code == 201, resp.text


async def _set_version_fabs(client, token, version_slug, fab_ids):
    resp = await client.put(
        f"/api/v1/versions/{version_slug}/fabs",
        headers=auth_headers(token),
        json={"fabs": [{"fab_id": fid, "url": "https://agents.example.com/a"} for fid in fab_ids]},
    )
    return resp


async def test_add_dependency_unrestricted_when_no_fabs_deployed(client, db_session):
    user = await make_user(db_session, email="fs1@example.com", role=UserRole.member)
    token = await login(client, "fs1@example.com")
    version_slug = await _create_agent_and_draft_version(client, token, "fs-agent-1")
    skill = await _seed_skill(db_session, user, "fs-skill-1")

    resp = await client.post(
        f"/api/v1/versions/{version_slug}/dependencies",
        headers=auth_headers(token),
        json={"dependency_id": str(skill.id), "type": "skill"},
    )
    assert resp.status_code == 201, resp.text


async def test_add_dependency_rejected_when_missing_in_deployed_fab(client, db_session):
    user = await make_user(db_session, email="fs2@example.com", role=UserRole.member)
    token = await login(client, "fs2@example.com")
    version_slug = await _create_agent_and_draft_version(client, token, "fs-agent-2")

    fab_a = await _create_fab(client, token, "F01")
    fab_b = await _create_fab(client, token, "F02")
    resp = await _set_version_fabs(client, token, version_slug, [fab_a, fab_b])
    assert resp.status_code == 200, resp.text

    skill = await _seed_skill(db_session, user, "fs-skill-2")
    await _assign_skill_fab(client, token, str(skill.id), fab_a)
    # Not assigned to fab_b — the version is deployed to both, so this should be
    # rejected rather than silently leaving fab_b's deployment without the skill.

    resp = await client.post(
        f"/api/v1/versions/{version_slug}/dependencies",
        headers=auth_headers(token),
        json={"dependency_id": str(skill.id), "type": "skill"},
    )
    assert resp.status_code == 409, resp.text
    assert "F02" in resp.json()["detail"]


async def test_add_dependency_allowed_when_covers_all_deployed_fabs(client, db_session):
    user = await make_user(db_session, email="fs3@example.com", role=UserRole.member)
    token = await login(client, "fs3@example.com")
    version_slug = await _create_agent_and_draft_version(client, token, "fs-agent-3")

    fab_a = await _create_fab(client, token, "F03")
    fab_b = await _create_fab(client, token, "F04")
    await _set_version_fabs(client, token, version_slug, [fab_a, fab_b])

    skill = await _seed_skill(db_session, user, "fs-skill-3")
    await _assign_skill_fab(client, token, str(skill.id), fab_a)
    await _assign_skill_fab(client, token, str(skill.id), fab_b)

    resp = await client.post(
        f"/api/v1/versions/{version_slug}/dependencies",
        headers=auth_headers(token),
        json={"dependency_id": str(skill.id), "type": "skill"},
    )
    assert resp.status_code == 201, resp.text


async def test_add_mcp_dependency_requires_available_status_per_fab(client, db_session):
    user = await make_user(db_session, email="fs4@example.com", role=UserRole.member)
    token = await login(client, "fs4@example.com")
    version_slug = await _create_agent_and_draft_version(client, token, "fs-agent-4")

    fab_a = await _create_fab(client, token, "F05")
    await _set_version_fabs(client, token, version_slug, [fab_a])

    mcp = await mcp_crud.create_mcp(
        db_session,
        name="fs-mcp-4",
        version="1.0.0",
        description=None,
        category=None,
        tags=[],
        created_by=user.id,
    )
    mcp_fab = await mcp_crud.create_mcp_fab(
        db_session, mcp_id=mcp.id, fab_id=uuid.UUID(fab_a), host="http://127.0.0.1:1"
    )
    # Deployed to fab_a, but flip its status to unavailable — e.g. a failed sync —
    # to prove the coverage check looks at per-fab status, not just membership.
    mcp_crud.mark_fab_synced(mcp_fab, AvailabilityStatus.unavailable)
    await db_session.commit()

    resp = await client.post(
        f"/api/v1/versions/{version_slug}/dependencies",
        headers=auth_headers(token),
        json={"dependency_id": str(mcp.id), "type": "mcp"},
    )
    assert resp.status_code == 409, resp.text
    assert "F05" in resp.json()["detail"]


async def test_add_model_dependency_resolves_against_ai_models_not_mcps(client, db_session):
    # Regression test for the pre-existing bug where type=model looked itself up in
    # mcp_crud instead of ai_model_crud and therefore always 404'd.
    user = await make_user(db_session, email="fs5@example.com", role=UserRole.member)
    token = await login(client, "fs5@example.com")
    version_slug = await _create_agent_and_draft_version(client, token, "fs-agent-5")

    fab_a = await _create_fab(client, token, "F06")
    await _set_version_fabs(client, token, version_slug, [fab_a])

    model = await ai_model_crud.create_model(
        db_session,
        name="claude-sonnet-5",
        provider="anthropic",
        model_id="claude-sonnet-5",
        description=None,
        category=None,
        tags=[],
        created_by=user.id,
    )

    resp = await client.post(
        f"/api/v1/versions/{version_slug}/dependencies",
        headers=auth_headers(token),
        json={"dependency_id": str(model.id), "type": "model"},
    )
    # Model dependencies have no fab dimension (see fab_scope module docstring), so
    # this must succeed even though the version is deployed to fab_a.
    assert resp.status_code == 201, resp.text
    assert resp.json()["type"] == "model"


async def test_set_version_fabs_rejected_when_dependency_missing_in_new_fab(client, db_session):
    user = await make_user(db_session, email="fs6@example.com", role=UserRole.member)
    token = await login(client, "fs6@example.com")
    version_slug = await _create_agent_and_draft_version(client, token, "fs-agent-6")

    fab_a = await _create_fab(client, token, "F07")
    fab_b = await _create_fab(client, token, "F08")
    await _set_version_fabs(client, token, version_slug, [fab_a])

    skill = await _seed_skill(db_session, user, "fs-skill-6")
    await _assign_skill_fab(client, token, str(skill.id), fab_a)
    resp = await client.post(
        f"/api/v1/versions/{version_slug}/dependencies",
        headers=auth_headers(token),
        json={"dependency_id": str(skill.id), "type": "skill"},
    )
    assert resp.status_code == 201, resp.text

    # Now try to also deploy to fab_b, where the skill isn't assigned.
    resp = await _set_version_fabs(client, token, version_slug, [fab_a, fab_b])
    assert resp.status_code == 409, resp.text
    assert "F08" in resp.json()["detail"]


async def test_set_version_fabs_allowed_when_dependency_covers_new_fab(client, db_session):
    user = await make_user(db_session, email="fs7@example.com", role=UserRole.member)
    token = await login(client, "fs7@example.com")
    version_slug = await _create_agent_and_draft_version(client, token, "fs-agent-7")

    fab_a = await _create_fab(client, token, "F09")
    fab_b = await _create_fab(client, token, "F10")
    await _set_version_fabs(client, token, version_slug, [fab_a])

    skill = await _seed_skill(db_session, user, "fs-skill-7")
    await _assign_skill_fab(client, token, str(skill.id), fab_a)
    await _assign_skill_fab(client, token, str(skill.id), fab_b)
    resp = await client.post(
        f"/api/v1/versions/{version_slug}/dependencies",
        headers=auth_headers(token),
        json={"dependency_id": str(skill.id), "type": "skill"},
    )
    assert resp.status_code == 201, resp.text

    resp = await _set_version_fabs(client, token, version_slug, [fab_a, fab_b])
    assert resp.status_code == 200, resp.text
