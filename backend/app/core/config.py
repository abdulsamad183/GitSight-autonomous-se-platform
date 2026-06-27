import json
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

INSECURE_SECRET_KEYS = frozenset(
    {"change-me-in-production", "test-secret-key", "test-secret-key-for-ci"}
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "development"
    database_url: str = "postgresql+asyncpg://localhost/postgres"
    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    supabase_service_role_key: str | None = None
    groq_api_key: str | None = None
    google_api_key: str | None = None
    secret_key: str = "change-me-in-production"

    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440
    cookie_name: str = "access_token"
    cookie_samesite: str = "lax"

    api_v1_prefix: str = "/api/v1"
    service_name: str = "autonomous-software-engineer"
    version: str = "0.1.0"
    cors_origins: list[str] = ["http://localhost:3000"]

    clone_base_dir: str = "/tmp/gitsight"
    max_file_size_bytes: int = 1_048_576
    max_branches_to_analyze: int = 1
    clone_depth: int = 0
    github_token: str | None = None

    embedding_model_name: str = "BAAI/bge-small-en-v1.5"
    embedding_provider: str = "local"
    embedding_dimension: int = 384
    embedding_batch_size: int = 32
    embedding_threads: int = 1
    embedding_gc_between_batches: bool | None = None

    search_default_limit: int = 20
    search_max_limit: int = 100
    search_keyword_weight: float = 0.4
    search_semantic_weight: float = 0.6
    search_similarity_threshold: float = 0.3
    search_candidate_multiplier: int = 3

    file_chunk_max_lines: int = 120
    file_chunk_whole_file_max_lines: int = 200
    max_diff_bytes: int = 500_000

    llm_provider: str = "groq"
    llm_model: str = "groq/compound-mini"
    llm_model_fallbacks: list[str] = [
        "groq/compound",
        "meta-llama/llama-4-scout-17b-16e-instruct",
    ]
    llm_temperature: float = 0.2
    llm_max_tokens: int = 8192
    rag_top_k: int = 5
    rag_max_context_chars: int = 48_000

    llm_planner_model: str | None = None
    llm_planner_temperature: float = 0.0
    llm_planner_max_tokens: int = 1024
    tool_max_steps: int = 4
    graph_traversal_max_depth: int = 5
    pr_review_max_tool_steps: int = 8
    pr_review_max_diff_chunks: int = 30
    pr_review_max_graph_files: int = 3

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        return cls._parse_string_list(value)

    @field_validator("llm_model_fallbacks", mode="before")
    @classmethod
    def parse_llm_model_fallbacks(cls, value: object) -> object:
        return cls._parse_string_list(value)

    @staticmethod
    def _parse_string_list(value: object) -> object:
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.startswith("["):
                return json.loads(stripped)
            return [item.strip() for item in stripped.split(",") if item.strip()]
        return value

    @staticmethod
    def _dedupe_models(primary: str, fallbacks: list[str]) -> list[str]:
        chain: list[str] = []
        seen: set[str] = set()
        for model in [primary, *fallbacks]:
            if model not in seen:
                seen.add(model)
                chain.append(model)
        return chain

    @property
    def effective_planner_model(self) -> str:
        return self.llm_planner_model or self.llm_model

    @property
    def llm_models_chain(self) -> list[str]:
        return self._dedupe_models(self.llm_model, self.llm_model_fallbacks)

    @property
    def planner_models_chain(self) -> list[str]:
        return self._dedupe_models(self.effective_planner_model, self.llm_model_fallbacks)

    @property
    def effective_embedding_batch_size(self) -> int:
        if self.is_development:
            return self.embedding_batch_size
        if self.embedding_provider == "google":
            return min(self.embedding_batch_size, 32)
        return min(self.embedding_batch_size, 8)

    @property
    def effective_embedding_model_name(self) -> str:
        return self.embedding_model_name

    @property
    def should_gc_between_embedding_batches(self) -> bool:
        if self.embedding_gc_between_batches is not None:
            return self.embedding_gc_between_batches
        return not self.is_development

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

    def validate_production_settings(self) -> None:
        if self.is_development:
            return

        if self.secret_key in INSECURE_SECRET_KEYS or len(self.secret_key) < 32:
            raise ValueError(
                "SECRET_KEY must be a secure random string of at least 32 characters in production"
            )

        lowered_db_url = self.database_url.lower()
        if "localhost" in lowered_db_url or "127.0.0.1" in lowered_db_url:
            raise ValueError("DATABASE_URL must not point to localhost in production")

        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY is required in production")

        if self.embedding_provider == "google" and not self.google_api_key:
            raise ValueError("GOOGLE_API_KEY is required when EMBEDDING_PROVIDER=google")


@lru_cache
def get_settings() -> Settings:
    return Settings()
