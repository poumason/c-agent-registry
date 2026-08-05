from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

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

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
