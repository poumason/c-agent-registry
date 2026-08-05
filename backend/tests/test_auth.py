from app.models.enums import UserRole
from tests.conftest import auth_headers, login, make_user


async def test_login_success_and_me(client, db_session):
    await make_user(db_session, email="alice@example.com", role=UserRole.member)
    token = await login(client, "alice@example.com")
    resp = await client.get("/api/v1/auth/me", headers=auth_headers(token))
    assert resp.status_code == 200
    assert resp.json()["email"] == "alice@example.com"


async def test_login_wrong_password(client, db_session):
    await make_user(db_session, email="bob@example.com", password="correct-pw")
    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "bob@example.com", "password": "wrong-pw"},
    )
    assert resp.status_code == 401


async def test_only_admin_can_create_users(client, db_session):
    await make_user(db_session, email="member@example.com", role=UserRole.member)
    token = await login(client, "member@example.com")
    resp = await client.post(
        "/api/v1/users",
        headers=auth_headers(token),
        json={"email": "new@example.com", "password": "pw123456", "name": "New"},
    )
    assert resp.status_code == 403


async def test_admin_can_create_and_list_users(client, db_session):
    await make_user(db_session, email="admin@example.com", role=UserRole.admin)
    token = await login(client, "admin@example.com")
    resp = await client.post(
        "/api/v1/users",
        headers=auth_headers(token),
        json={"email": "new@example.com", "password": "pw123456", "name": "New", "role": "owner"},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["role"] == "owner"

    resp = await client.get("/api/v1/users", headers=auth_headers(token))
    assert resp.status_code == 200
    emails = {u["email"] for u in resp.json()}
    assert {"admin@example.com", "new@example.com"} <= emails
