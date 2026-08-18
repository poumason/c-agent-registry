"""A legacy skill/mcp dependency is scoped to one specific fab once its version is
deployed to any fab at all (see app/services/fab_scope.py). These tests exercise:
the no-fab-deployed-yet path (fab_id must stay unset), the fab_id-required path
once fabs are deployed (must be one of the deployed fabs, and the dependency must
itself be available there), duplicate rejection, the type=model exemption (also a
regression test for the pre-existing bug where it resolved against mcp_crud instead
of ai_model_crud), and that deploying to a new fab no longer requires existing
dependencies to already cover it.
"""

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


async def test_add_dependency_no_fab_id_when_version_has_no_fabs_deployed(client, db_session):
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
    assert resp.json()["fab_id"] is None


async def test_add_dependency_rejects_fab_id_when_version_has_no_fabs_deployed(client, db_session):
    user = await make_user(db_session, email="fs2@example.com", role=UserRole.member)
    token = await login(client, "fs2@example.com")
    version_slug = await _create_agent_and_draft_version(client, token, "fs-agent-2")
    skill = await _seed_skill(db_session, user, "fs-skill-2")
    fab = await _create_fab(client, token, "F02")

    resp = await client.post(
        f"/api/v1/versions/{version_slug}/dependencies",
        headers=auth_headers(token),
        json={"dependency_id": str(skill.id), "type": "skill", "fab_id": fab},
    )
    assert resp.status_code == 400, resp.text


async def test_add_dependency_requires_fab_id_once_version_has_fabs_deployed(client, db_session):
    user = await make_user(db_session, email="fs3@example.com", role=UserRole.member)
    token = await login(client, "fs3@example.com")
    version_slug = await _create_agent_and_draft_version(client, token, "fs-agent-3")
    fab_a = await _create_fab(client, token, "F03")
    await _set_version_fabs(client, token, version_slug, [fab_a])
    skill = await _seed_skill(db_session, user, "fs-skill-3")
    await _assign_skill_fab(client, token, str(skill.id), fab_a)

    resp = await client.post(
        f"/api/v1/versions/{version_slug}/dependencies",
        headers=auth_headers(token),
        json={"dependency_id": str(skill.id), "type": "skill"},
    )
    assert resp.status_code == 400, resp.text


async def test_add_dependency_rejects_fab_id_not_deployed_by_version(client, db_session):
    user = await make_user(db_session, email="fs4@example.com", role=UserRole.member)
    token = await login(client, "fs4@example.com")
    version_slug = await _create_agent_and_draft_version(client, token, "fs-agent-4")
    fab_a = await _create_fab(client, token, "F04a")
    fab_b = await _create_fab(client, token, "F04b")
    await _set_version_fabs(client, token, version_slug, [fab_a])
    skill = await _seed_skill(db_session, user, "fs-skill-4")
    await _assign_skill_fab(client, token, str(skill.id), fab_a)
    await _assign_skill_fab(client, token, str(skill.id), fab_b)

    resp = await client.post(
        f"/api/v1/versions/{version_slug}/dependencies",
        headers=auth_headers(token),
        json={"dependency_id": str(skill.id), "type": "skill", "fab_id": fab_b},
    )
    assert resp.status_code == 400, resp.text


async def test_add_dependency_rejects_fab_where_dependency_unavailable(client, db_session):
    user = await make_user(db_session, email="fs5@example.com", role=UserRole.member)
    token = await login(client, "fs5@example.com")
    version_slug = await _create_agent_and_draft_version(client, token, "fs-agent-5")
    fab_a = await _create_fab(client, token, "F05")
    await _set_version_fabs(client, token, version_slug, [fab_a])
    skill = await _seed_skill(db_session, user, "fs-skill-5")
    # Deliberately not assigned to fab_a.

    resp = await client.post(
        f"/api/v1/versions/{version_slug}/dependencies",
        headers=auth_headers(token),
        json={"dependency_id": str(skill.id), "type": "skill", "fab_id": fab_a},
    )
    assert resp.status_code == 409, resp.text
    assert "F05" in resp.json()["detail"]


async def test_add_dependency_allowed_for_two_different_deployed_fabs_independently(client, db_session):
    user = await make_user(db_session, email="fs6@example.com", role=UserRole.member)
    token = await login(client, "fs6@example.com")
    version_slug = await _create_agent_and_draft_version(client, token, "fs-agent-6")
    fab_a = await _create_fab(client, token, "F06a")
    fab_b = await _create_fab(client, token, "F06b")
    await _set_version_fabs(client, token, version_slug, [fab_a, fab_b])
    skill = await _seed_skill(db_session, user, "fs-skill-6")
    await _assign_skill_fab(client, token, str(skill.id), fab_a)
    await _assign_skill_fab(client, token, str(skill.id), fab_b)

    resp_a = await client.post(
        f"/api/v1/versions/{version_slug}/dependencies",
        headers=auth_headers(token),
        json={"dependency_id": str(skill.id), "type": "skill", "fab_id": fab_a},
    )
    assert resp_a.status_code == 201, resp_a.text

    resp_b = await client.post(
        f"/api/v1/versions/{version_slug}/dependencies",
        headers=auth_headers(token),
        json={"dependency_id": str(skill.id), "type": "skill", "fab_id": fab_b},
    )
    assert resp_b.status_code == 201, resp_b.text
    assert resp_a.json()["id"] != resp_b.json()["id"]


async def test_add_dependency_duplicate_same_fab_rejected(client, db_session):
    user = await make_user(db_session, email="fs7@example.com", role=UserRole.member)
    token = await login(client, "fs7@example.com")
    version_slug = await _create_agent_and_draft_version(client, token, "fs-agent-7")
    fab_a = await _create_fab(client, token, "F07")
    await _set_version_fabs(client, token, version_slug, [fab_a])
    skill = await _seed_skill(db_session, user, "fs-skill-7")
    await _assign_skill_fab(client, token, str(skill.id), fab_a)

    payload = {"dependency_id": str(skill.id), "type": "skill", "fab_id": fab_a}
    first = await client.post(
        f"/api/v1/versions/{version_slug}/dependencies", headers=auth_headers(token), json=payload
    )
    assert first.status_code == 201, first.text
    second = await client.post(
        f"/api/v1/versions/{version_slug}/dependencies", headers=auth_headers(token), json=payload
    )
    assert second.status_code == 409, second.text


async def test_add_mcp_dependency_requires_available_status_at_fab(client, db_session):
    user = await make_user(db_session, email="fs8@example.com", role=UserRole.member)
    token = await login(client, "fs8@example.com")
    version_slug = await _create_agent_and_draft_version(client, token, "fs-agent-8")
    fab_a = await _create_fab(client, token, "F08")
    await _set_version_fabs(client, token, version_slug, [fab_a])

    mcp = await mcp_crud.create_mcp(
        db_session,
        name="fs-mcp-8",
        version="1.0.0",
        description=None,
        category=None,
        tags=[],
        created_by=user.id,
    )
    mcp_fab = await mcp_crud.create_mcp_fab(
        db_session, mcp_id=mcp.id, fab_id=uuid.UUID(fab_a), host="http://127.0.0.1:1"
    )
    mcp_crud.mark_fab_synced(mcp_fab, AvailabilityStatus.unavailable)
    await db_session.commit()

    resp = await client.post(
        f"/api/v1/versions/{version_slug}/dependencies",
        headers=auth_headers(token),
        json={"dependency_id": str(mcp.id), "type": "mcp", "fab_id": fab_a},
    )
    assert resp.status_code == 409, resp.text
    assert "F08" in resp.json()["detail"]


async def test_add_model_dependency_has_no_fab_dimension(client, db_session):
    # Regression test for the pre-existing bug where type=model looked itself up in
    # mcp_crud instead of ai_model_crud and therefore always 404'd.
    user = await make_user(db_session, email="fs9@example.com", role=UserRole.member)
    token = await login(client, "fs9@example.com")
    version_slug = await _create_agent_and_draft_version(client, token, "fs-agent-9")
    fab_a = await _create_fab(client, token, "F09")
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

    rejected = await client.post(
        f"/api/v1/versions/{version_slug}/dependencies",
        headers=auth_headers(token),
        json={"dependency_id": str(model.id), "type": "model", "fab_id": fab_a},
    )
    assert rejected.status_code == 400, rejected.text

    resp = await client.post(
        f"/api/v1/versions/{version_slug}/dependencies",
        headers=auth_headers(token),
        json={"dependency_id": str(model.id), "type": "model"},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["type"] == "model"
    assert resp.json()["fab_id"] is None


async def test_set_version_fabs_no_longer_requires_existing_dependencies_to_cover_new_fab(
    client, db_session
):
    user = await make_user(db_session, email="fs10@example.com", role=UserRole.member)
    token = await login(client, "fs10@example.com")
    version_slug = await _create_agent_and_draft_version(client, token, "fs-agent-10")
    fab_a = await _create_fab(client, token, "F10a")
    fab_b = await _create_fab(client, token, "F10b")
    await _set_version_fabs(client, token, version_slug, [fab_a])

    skill = await _seed_skill(db_session, user, "fs-skill-10")
    await _assign_skill_fab(client, token, str(skill.id), fab_a)
    resp = await client.post(
        f"/api/v1/versions/{version_slug}/dependencies",
        headers=auth_headers(token),
        json={"dependency_id": str(skill.id), "type": "skill", "fab_id": fab_a},
    )
    assert resp.status_code == 201, resp.text

    # fab_b has no dependency of its own yet — deploying to it is fine, same as a
    # freshly created version starting out with zero dependencies.
    resp = await _set_version_fabs(client, token, version_slug, [fab_a, fab_b])
    assert resp.status_code == 200, resp.text
