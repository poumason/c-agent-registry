import secrets
from dataclasses import dataclass

import httpx
from authlib.integrations.httpx_client import AsyncOAuth2Client
from jose import JWTError
from jose import jwt as jose_jwt

from app.core.config import get_settings
from app.core.security import create_sso_state_token

settings = get_settings()

_discovery_cache: dict | None = None
_jwks_cache: dict | None = None


class SsoNotConfigured(Exception):
    pass


class SsoError(Exception):
    pass


@dataclass
class SsoClaims:
    email: str
    name: str


def _require_configured() -> None:
    if not (settings.oidc_issuer and settings.oidc_client_id and settings.oidc_client_secret):
        raise SsoNotConfigured(
            "SSO is not configured (OIDC_ISSUER/OIDC_CLIENT_ID/OIDC_CLIENT_SECRET)"
        )


async def _discovery() -> dict:
    global _discovery_cache
    if _discovery_cache is None:
        _require_configured()
        url = f"{settings.oidc_issuer.rstrip('/')}/.well-known/openid-configuration"
        async with httpx.AsyncClient(timeout=10) as http:
            resp = await http.get(url)
            resp.raise_for_status()
            _discovery_cache = resp.json()
    return _discovery_cache


async def _jwks() -> dict:
    global _jwks_cache
    if _jwks_cache is None:
        discovery = await _discovery()
        async with httpx.AsyncClient(timeout=10) as http:
            resp = await http.get(discovery["jwks_uri"])
            resp.raise_for_status()
            _jwks_cache = resp.json()
    return _jwks_cache


def _oauth_client() -> AsyncOAuth2Client:
    return AsyncOAuth2Client(
        settings.oidc_client_id,
        settings.oidc_client_secret,
        redirect_uri=settings.oidc_redirect_uri,
        code_challenge_method="S256",
    )


async def build_authorization_url() -> str:
    """Builds the IdP login URL. The PKCE code_verifier + nonce are embedded in the
    signed `state` param (see create_sso_state_token) so no server-side session is needed.
    """
    _require_configured()
    discovery = await _discovery()
    code_verifier = secrets.token_urlsafe(64)
    nonce = secrets.token_urlsafe(32)
    state = create_sso_state_token(nonce=nonce, code_verifier=code_verifier)
    client = _oauth_client()
    url, _ = client.create_authorization_url(
        discovery["authorization_endpoint"],
        state=state,
        code_verifier=code_verifier,
        nonce=nonce,
        scope="openid email profile",
    )
    return url


async def exchange_code(*, code: str, code_verifier: str, nonce: str) -> SsoClaims:
    """Exchanges the auth code for tokens and validates the id_token (signature via
    JWKS, issuer, audience, expiry, nonce). Returns the user's email/name.
    """
    _require_configured()
    discovery = await _discovery()
    client = _oauth_client()
    try:
        token = await client.fetch_token(
            discovery["token_endpoint"], code=code, code_verifier=code_verifier
        )
    except Exception as exc:
        raise SsoError(f"Token exchange failed: {exc}") from exc

    id_token = token.get("id_token")
    if not id_token:
        raise SsoError("IdP did not return an id_token")

    try:
        claims = jose_jwt.decode(
            id_token,
            await _jwks(),
            algorithms=["RS256"],
            audience=settings.oidc_client_id,
            issuer=discovery.get("issuer", settings.oidc_issuer),
        )
    except JWTError as exc:
        raise SsoError(f"Invalid id_token: {exc}") from exc

    if claims.get("nonce") != nonce:
        raise SsoError("id_token nonce mismatch")
    if claims.get("email_verified") is False:
        raise SsoError("IdP reports the email address is not verified")

    email = claims.get("email")
    name = claims.get("name")
    if not email:
        # Some providers (GitLab included, depending on config) only expose email via
        # the userinfo endpoint rather than the id_token itself.
        userinfo_endpoint = discovery.get("userinfo_endpoint")
        if userinfo_endpoint:
            resp = await client.get(userinfo_endpoint)
            resp.raise_for_status()
            userinfo = resp.json()
            email = userinfo.get("email")
            name = name or userinfo.get("name")

    if not email:
        raise SsoError("IdP did not provide an email address")

    return SsoClaims(email=email, name=name or email.split("@")[0])
