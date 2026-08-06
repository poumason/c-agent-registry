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
        json={"email": "new@example.com", "password": "pw123456", "name": "New", "role": "reviewer"},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["role"] == "reviewer"

    resp = await client.get("/api/v1/users", headers=auth_headers(token))
    assert resp.status_code == 200
    emails = {u["email"] for u in resp.json()}
    assert {"admin@example.com", "new@example.com"} <= emails


async def test_admin_cannot_delete_self(client, db_session):
    admin = await make_user(db_session, email="solo-admin@example.com", role=UserRole.admin)
    token = await login(client, "solo-admin@example.com")
    resp = await client.delete(f"/api/v1/users/{admin.id}", headers=auth_headers(token))
    assert resp.status_code == 409


async def test_admin_can_delete_user_and_deleted_user_cannot_login(client, db_session):
    await make_user(db_session, email="admin2@example.com", role=UserRole.admin)
    target = await make_user(db_session, email="doomed@example.com", password="pw123456")
    admin_token = await login(client, "admin2@example.com")
    target_token = await login(client, "doomed@example.com", "pw123456")

    resp = await client.delete(f"/api/v1/users/{target.id}", headers=auth_headers(admin_token))
    assert resp.status_code == 204

    # deleted user disappears from the admin list
    resp = await client.get("/api/v1/users", headers=auth_headers(admin_token))
    assert "doomed@example.com" not in {u["email"] for u in resp.json()}

    # can't log in with password anymore
    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "doomed@example.com", "password": "pw123456"},
    )
    assert resp.status_code == 401

    # existing token is also rejected
    resp = await client.get("/api/v1/auth/me", headers=auth_headers(target_token))
    assert resp.status_code == 401
