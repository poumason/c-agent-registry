from app.models.enums import UserRole
from tests.conftest import auth_headers, login, make_user


async def _create_agent(client, token, slug, **extra):
    payload = {"slug": slug, "name": slug, "visibility": "internal", **extra}
    resp = await client.post("/api/v1/agents", headers=auth_headers(token), json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _create_draft_version(client, token, slug, **extra):
    resp = await client.post(
        f"/api/v1/agents/{slug}/versions", headers=auth_headers(token), json=extra
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_agent_create_accepts_new_fields(client, db_session):
    await make_user(db_session, email="af1@example.com", role=UserRole.member)
    token = await login(client, "af1@example.com")

    agent = await _create_agent(
        client,
        token,
        "agent-fields-1",
        icon_path="https://cdn.example.com/icon.png",
        category=["tool", "geospatial"],
        hello_msg="Hi, I can plan routes.",
        example_questions=["Plan a route to SF", "Avoid tolls"],
        audience="internal-agents",
        doc_url="https://docs.example.com/agent",
    )
    assert agent["icon_path"] == "https://cdn.example.com/icon.png"
    assert agent["category"] == ["tool", "geospatial"]
    assert agent["hello_msg"] == "Hi, I can plan routes."
    assert agent["example_questions"] == ["Plan a route to SF", "Avoid tolls"]
    assert agent["audience"] == "internal-agents"
    assert agent["doc_url"] == "https://docs.example.com/agent"


async def test_agent_create_defaults_category_to_tool(client, db_session):
    await make_user(db_session, email="af2@example.com", role=UserRole.member)
    token = await login(client, "af2@example.com")
    agent = await _create_agent(client, token, "agent-fields-2")
    assert agent["category"] == ["tool"]
    assert agent["example_questions"] == []


async def test_agent_update_new_fields(client, db_session):
    await make_user(db_session, email="af3@example.com", role=UserRole.member)
    token = await login(client, "af3@example.com")
    await _create_agent(client, token, "agent-fields-3")

    resp = await client.patch(
        "/api/v1/agents/agent-fields-3",
        headers=auth_headers(token),
        json={"category": ["chat"], "hello_msg": "updated"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["category"] == ["chat"]
    assert body["hello_msg"] == "updated"


async def test_version_create_no_longer_accepts_url(client, db_session):
    """AgentVersion.url doesn't exist anymore (moved to AgentFab) — sending it should
    just be silently ignored, not rejected or crash."""
    await make_user(db_session, email="af4@example.com", role=UserRole.member)
    token = await login(client, "af4@example.com")
    await _create_agent(client, token, "agent-fields-4")

    resp = await client.post(
        "/api/v1/agents/agent-fields-4/versions",
        headers=auth_headers(token),
        json={"url": "https://ignored.example.com", "streaming": True},
    )
    assert resp.status_code == 201, resp.text
    assert "url" not in resp.json()
    assert resp.json()["streaming"] is True


async def test_agent_fabs_set_replaces_and_lists(client, db_session):
    await make_user(db_session, email="af5@example.com", role=UserRole.member)
    token = await login(client, "af5@example.com")
    await _create_agent(client, token, "agent-fields-5")
    version = await _create_draft_version(client, token, "agent-fields-5")
    slug = version["slug"]

    fab1 = (await client.post("/api/v1/fabs", headers=auth_headers(token), json={"fab": "F31"})).json()
    fab2 = (await client.post("/api/v1/fabs", headers=auth_headers(token), json={"fab": "F32"})).json()

    resp = await client.put(
        f"/api/v1/versions/{slug}/fabs",
        headers=auth_headers(token),
        json={"fabs": [{"fab_id": fab1["id"], "url": "https://f31.example.com"}]},
    )
    assert resp.status_code == 200, resp.text
    assert len(resp.json()) == 1

    # Replace-all: second call with a different set drops the first entirely.
    resp = await client.put(
        f"/api/v1/versions/{slug}/fabs",
        headers=auth_headers(token),
        json={
            "fabs": [
                {"fab_id": fab1["id"], "url": "https://f31-updated.example.com"},
                {"fab_id": fab2["id"], "url": "https://f32.example.com"},
            ]
        },
    )
    assert resp.status_code == 200, resp.text

    resp = await client.get(f"/api/v1/versions/{slug}/fabs", headers=auth_headers(token))
    rows = resp.json()
    assert len(rows) == 2
    by_fab = {r["fab_id"]: r["url"] for r in rows}
    assert by_fab[fab1["id"]] == "https://f31-updated.example.com"
    assert by_fab[fab2["id"]] == "https://f32.example.com"


async def test_agent_fabs_set_rejects_unknown_fab_and_duplicates(client, db_session):
    import uuid

    await make_user(db_session, email="af6@example.com", role=UserRole.member)
    token = await login(client, "af6@example.com")
    await _create_agent(client, token, "agent-fields-6")
    version = await _create_draft_version(client, token, "agent-fields-6")
    slug = version["slug"]
    fab = (await client.post("/api/v1/fabs", headers=auth_headers(token), json={"fab": "F33"})).json()

    resp = await client.put(
        f"/api/v1/versions/{slug}/fabs",
        headers=auth_headers(token),
        json={"fabs": [{"fab_id": str(uuid.uuid4()), "url": "https://x.example.com"}]},
    )
    assert resp.status_code == 404

    resp = await client.put(
        f"/api/v1/versions/{slug}/fabs",
        headers=auth_headers(token),
        json={
            "fabs": [
                {"fab_id": fab["id"], "url": "https://a.example.com"},
                {"fab_id": fab["id"], "url": "https://b.example.com"},
            ]
        },
    )
    assert resp.status_code == 400


async def test_agent_card_assembly(client, db_session):
    await make_user(db_session, email="af7@example.com", role=UserRole.member)
    token = await login(client, "af7@example.com")
    await _create_agent(
        client,
        token,
        "agent-fields-7",
        name="Route Planner",
        description="Plans routes.",
        provider="Example Geo Services Inc.",
        icon_path="https://cdn.example.com/icon.png",
    )
    version = await _create_draft_version(
        client,
        token,
        "agent-fields-7",
        streaming=True,
        default_input_modes=["application/json", "text/plain"],
        default_output_modes=["application/json", "image/png"],
    )
    slug = version["slug"]

    resp = await client.patch(
        f"/api/v1/versions/{slug}",
        headers=auth_headers(token),
        json={
            "skills": [
                {
                    "id": "route-optimizer-traffic",
                    "name": "Traffic-Aware Route Optimizer",
                    "description": "Calculates the optimal route.",
                    "tags": ["maps", "routing"],
                    "examples": ["Plan a route to SF"],
                    "inputModes": ["application/json"],
                    "outputModes": ["application/json"],
                }
            ]
        },
    )
    assert resp.status_code == 200, resp.text

    fab = (await client.post("/api/v1/fabs", headers=auth_headers(token), json={"fab": "F34"})).json()
    await client.put(
        f"/api/v1/versions/{slug}/fabs",
        headers=auth_headers(token),
        json={"fabs": [{"fab_id": fab["id"], "url": "https://georoute-agent.example.com/a2a/v1"}]},
    )

    resp = await client.get(f"/api/v1/versions/{slug}/agent-card", headers=auth_headers(token))
    assert resp.status_code == 200, resp.text
    card = resp.json()

    assert card["name"] == "Route Planner"
    assert card["description"] == "Plans routes."
    assert card["supportedInterfaces"] == [
        {
            "url": "https://georoute-agent.example.com/a2a/v1",
            "protocolBinding": "JSONRPC",
            "protocolVersion": "1.0",
        }
    ]
    assert card["provider"] == {"organization": "Example Geo Services Inc.", "url": None}
    assert card["iconUrl"] == "https://cdn.example.com/icon.png"
    assert card["version"] == "1"
    assert card["capabilities"] == {
        "streaming": True,
        "pushNotifications": True,
        "extendedAgentCard": True,
    }
    assert card["defaultInputModes"] == ["application/json", "text/plain"]
    assert card["defaultOutputModes"] == ["application/json", "image/png"]
    assert card["skills"][0]["id"] == "route-optimizer-traffic"
