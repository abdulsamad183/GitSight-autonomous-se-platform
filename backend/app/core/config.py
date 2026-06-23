from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "development"
    database_url: str = "postgresql+asyncpg://localhost/postgres"
    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    supabase_service_role_key: str | None = None
    groq_api_key: str | None = None
    secret_key: str = "change-me-in-production"

    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440
    cookie_name: str = "access_token"
    cookie_samesite: str = "lax"

    api_v1_prefix: str = "/api/v1"
    service_name: str = "autonomous-software-engineer"
    version: str = "0.1.0"
    cors_origins: list[str] = ["http://localhost:3000"]

    @property
    def is_development(self) -> bool:
        return self.env == "development"

    @property
    def cookie_secure(self) -> bool:
        return self.env != "development"

    @property
    def sync_database_url(self) -> str:
        """Sync URL for Alembic migrations."""
        return self.database_url.replace("postgresql+asyncpg://", "postgresql://")


@lru_cache
def get_settings() -> Settings:
    return Settings()
