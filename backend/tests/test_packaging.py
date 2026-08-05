import io
import json
import zipfile

import httpx
import yaml

from app.models.enums import UserRole
from tests.conftest import auth_headers, login, make_user


async def test_approval_generates_downloadable_package(client, db_session):
    await make_user(db_session, email="pm@example.com", role=UserRole.member)
    reviewer = await make_user(db_session, email="po@example.com", role=UserRole.reviewer)
    member_token = await login(client, "pm@example.com")
    reviewer_token = await login(client, "po@example.com")

    resp = await client.post(
        "/api/v1/agents",
        headers=auth_headers(member_token),
        json={
            "slug": "pkg-agent",
            "name": "Package Agent",
            "description": "desc",
            "provider": "acme",
            "visibility": "internal",
        },
    )
    assert resp.status_code == 201

    resp = await client.post(
        "/api/v1/agents/pkg-agent/versions",
        headers=auth_headers(member_token),
        json={
            "url": "https://agents.example.com/pkg",
            "streaming": True,
            "default_input_modes": ["text/plain"],
            "default_output_modes": ["text/plain"],
        },
    )
    assert resp.status_code == 201
    version_slug = resp.json()["slug"]

    skill_content = b"print('packaged skill')"
    resp = await client.post(
        "/api/v1/skills",
        headers=auth_headers(member_token),
        files={"file": ("run.py", skill_content, "text/plain")},
        data={"name": "packaged-skill", "version": "2.0.0"},
    )
    assert resp.status_code == 201
    skill_id = resp.json()["id"]

    resp = await client.post(
        f"/api/v1/versions/{version_slug}/dependencies",
        headers=auth_headers(member_token),
        json={"dependency_id": skill_id, "type": "skill"},
    )
    assert resp.status_code == 201

    resp = await client.post(
        f"/api/v1/versions/{version_slug}/submit",
        headers=auth_headers(member_token),
        json={"reviewer_ids": [str(reviewer.id)]},
    )
    assert resp.status_code == 200

    resp = await client.get(
        f"/api/v1/versions/{version_slug}/reviews", headers=auth_headers(member_token)
    )
    review_id = resp.json()[0]["id"]
    resp = await client.post(
        f"/api/v1/reviews/{review_id}/decision",
        headers=auth_headers(reviewer_token),
        json={"result": "approved"},
    )
    assert resp.status_code == 200

    resp = await client.get(
        f"/api/v1/versions/{version_slug}/download", headers=auth_headers(member_token)
    )
    assert resp.status_code == 200
    download_url = resp.json()["url"]

    async with httpx.AsyncClient() as raw_client:
        zip_resp = await raw_client.get(download_url)
    assert zip_resp.status_code == 200

    with zipfile.ZipFile(io.BytesIO(zip_resp.content)) as zf:
        names = set(zf.namelist())
        assert "agent_card.json" in names
        assert "install.yaml" in names
        assert "skills/packaged-skill/run.py" in names

        agent_card = json.loads(zf.read("agent_card.json"))
        assert agent_card["slug"] == "pkg-agent"
        assert agent_card["streaming"] is True
        assert agent_card["default_input_modes"] == ["text/plain"]

        install_manifest = yaml.safe_load(zf.read("install.yaml"))
        assert install_manifest["skills"][0]["name"] == "packaged-skill"
        assert install_manifest["mcp"] == []

        assert zf.read("skills/packaged-skill/run.py") == skill_content
