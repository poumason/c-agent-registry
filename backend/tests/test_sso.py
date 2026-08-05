import uuid

import app.core.security as security_module
from app.core.security import create_access_token, create_sso_state_token, decode_sso_state_token
from app.crud import user as user_crud
from app.models.enums import UserRole, UserStatus
from app.services import sso as sso_service
from tests.conftest import auth_headers, make_user


def test_sso_state_round_trip():
    token = create_sso_state_token(nonce="abc", code_verifier="xyz")
    payload = decode_sso_state_token(token)
    assert payload is not None
    assert payload["nonce"] == "abc"
    assert payload["code_verifier"] == "xyz"


def test_sso_state_rejects_tampered_token():
    token = create_sso_state_token(nonce="abc", code_verifier="xyz")
    tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
    assert decode_sso_state_token(tampered) is None


def test_sso_state_rejects_real_access_token():
    access_token = create_access_token(uuid.uuid4())
    assert decode_sso_state_token(access_token) is None


def test_sso_state_expired(monkeypatch):
    monkeypatch.setattr(security_module, "SSO_STATE_EXPIRE_MINUTES", -1)
    token = create_sso_state_token(nonce="abc", code_verifier="xyz")
    assert decode_sso_state_token(token) is None


async def test_get_or_create_by_sso_provisions_member(db_session):
    user = await user_crud.get_or_create_by_sso(
        db_session, email="brandnew@example.com", name="Brand New"
    )
    assert user.role == UserRole.member
    assert user.status == UserStatus.active
    assert user.email == "brandnew@example.com"


async def test_get_or_create_by_sso_does_not_change_existing_role(db_session):
    existing = await make_user(db_session, email="already@example.com", role=UserRole.reviewer)
    found = await user_crud.get_or_create_by_sso(
        db_session, email="already@example.com", name="Ignored Name"
    )
    assert found.id == existing.id
    assert found.role == UserRole.reviewer


async def test_sso_callback_rejects_invalid_state(client):
    resp = await client.get(
        "/api/v1/auth/sso/callback", params={"code": "abc", "state": "not-a-real-token"}
    )
    assert resp.status_code == 400


async def test_sso_callback_provisions_new_member_and_logs_in(client, db_session, monkeypatch):
    state = create_sso_state_token(nonce="n1", code_verifier="cv1")

    async def fake_exchange_code(*, code, code_verifier, nonce):
        assert code == "authcode123"
        assert code_verifier == "cv1"
        assert nonce == "n1"
        return sso_service.SsoClaims(email="newsso@example.com", name="New SSO User")

    monkeypatch.setattr(sso_service, "exchange_code", fake_exchange_code)

    resp = await client.get(
        "/api/v1/auth/sso/callback", params={"code": "authcode123", "state": state}
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["token_type"] == "bearer"

    resp2 = await client.get("/api/v1/auth/me", headers=auth_headers(body["access_token"]))
    assert resp2.status_code == 200
    me = resp2.json()
    assert me["email"] == "newsso@example.com"
    assert me["role"] == "member"
    assert me["status"] == "active"


async def test_sso_callback_existing_user_role_is_untouched(client, db_session, monkeypatch):
    await make_user(db_session, email="existingsso@example.com", role=UserRole.reviewer)
    state = create_sso_state_token(nonce="n2", code_verifier="cv2")

    async def fake_exchange_code(*, code, code_verifier, nonce):
        return sso_service.SsoClaims(email="existingsso@example.com", name="Existing")

    monkeypatch.setattr(sso_service, "exchange_code", fake_exchange_code)

    resp = await client.get("/api/v1/auth/sso/callback", params={"code": "c2", "state": state})
    assert resp.status_code == 200
    body = resp.json()

    resp2 = await client.get("/api/v1/auth/me", headers=auth_headers(body["access_token"]))
    assert resp2.json()["role"] == "reviewer"


async def test_sso_callback_rejects_disabled_user(client, db_session, monkeypatch):
    await make_user(db_session, email="disabledsso@example.com", role=UserRole.member)
    disabled = await user_crud.get_by_email(db_session, "disabledsso@example.com")
    await user_crud.update_user(db_session, disabled, status=UserStatus.disabled)

    state = create_sso_state_token(nonce="n3", code_verifier="cv3")

    async def fake_exchange_code(*, code, code_verifier, nonce):
        return sso_service.SsoClaims(email="disabledsso@example.com", name="Disabled")

    monkeypatch.setattr(sso_service, "exchange_code", fake_exchange_code)

    resp = await client.get("/api/v1/auth/sso/callback", params={"code": "c3", "state": state})
    assert resp.status_code == 403


async def test_password_login_still_works_alongside_sso(client, db_session):
    await make_user(db_session, email="stillpw@example.com", password="mypassword1")
    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "stillpw@example.com", "password": "mypassword1"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()
