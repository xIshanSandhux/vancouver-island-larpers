from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All configuration comes from environment variables (see .env.example)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str = ""
    claude_model: str = "claude-haiku-5-5"
    featherless_api_key: str = ""
    featherless_base_url: str = "https://api.featherless.ai/v1"
    featherless_model: str = ""
    commenter_provider: str = "featherless"  # or "anthropic"
    render_api_key: str = ""
    render_workflow_slug: str = ""
    workflow_event_secret: str = "change-me"
    web_base_url: str = "http://localhost:8000"
    cors_origins: str = Field(default="http://localhost:3000", description="comma separated")

    # Workflow granularity (architecture.md section 5.1). Tune after measuring on Render.
    variant_batches: int = 4
    commenter_batches_per_post: int = 2
    llm_concurrency: int = 12

    # Abuse guard (architecture.md section 10)
    max_active_runs: int = 2
    max_runs_per_hour: int = 60

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
