from app.models.enums import UserRole
from tests.conftest import auth_headers, login, make_user


async def test_create_and_list_fabs(client, db_session):
    await make_user(db_session, email="fab1@example.com", role=UserRole.member)
    token = await login(client, "fab1@example.com")

    resp = await client.post("/api/v1/fabs", headers=auth_headers(token), json={"fab": "F15"})
    assert resp.status_code == 201, resp.text
    assert resp.json()["fab"] == "F15"

    resp = await client.get("/api/v1/fabs", headers=auth_headers(token))
    assert resp.status_code == 200
    assert any(f["fab"] == "F15" for f in resp.json())


async def test_create_fab_rejects_duplicate(client, db_session):
    await make_user(db_session, email="fab2@example.com", role=UserRole.member)
    token = await login(client, "fab2@example.com")

    resp = await client.post("/api/v1/fabs", headers=auth_headers(token), json={"fab": "F12"})
    assert resp.status_code == 201

    resp = await client.post("/api/v1/fabs", headers=auth_headers(token), json={"fab": "F12"})
    assert resp.status_code == 409
