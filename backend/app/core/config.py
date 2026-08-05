from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Repo root's .env (backend/app/core/config.py -> core -> app -> backend -> repo root),
# so `uv run` picks it up regardless of whether it's invoked from the repo root or from
# backend/ (the documented dev workflow). Docker-compose instead injects real env vars
# via its own `env_file:`, so this path is irrelevant there.
_REPO_ROOT_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_REPO_ROOT_ENV_FILE, extra="ignore")

    postgres_user: str = "agent_registry"
    postgres_password: str = "agent_registry"
    postgres_db: str = "agent_registry"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_secure: bool = False
    minio_skills_bucket: str = "skills"
    minio_packages_bucket: str = "packages"

    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    bootstrap_admin_email: str = "admin@example.com"
    bootstrap_admin_password: str = "change-me-admin"
    bootstrap_admin_name: str = "Administrator"

    # SSO (generic OIDC) - all optional so the app still boots without SSO configured.
    oidc_issuer: str | None = None
    oidc_client_id: str | None = None
    oidc_client_secret: str | None = None
    # Must exactly match what's registered as a redirect URI at the IdP:
    # {backend_base_url}/api/v1/auth/sso/callback
    backend_base_url: str = "http://localhost:8000"
    # Where to send the browser after a successful SSO login, with the token in the URL
    # fragment. Left unset (no frontend yet) makes /auth/sso/callback return JSON instead.
    frontend_sso_redirect_url: str | None = None

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def oidc_redirect_uri(self) -> str:
        return f"{self.backend_base_url}/api/v1/auth/sso/callback"


@lru_cache
def get_settings() -> Settings:
    return Settings()
