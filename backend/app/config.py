from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All configuration comes from environment variables (see .env.example)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Anthropic is the only model provider (architecture.md section 12).
    anthropic_api_key: str = ""
    claude_model: str = "claude-haiku-5-5"
    # Effort and thinking are the cost levers. Haiku 5.5 accepts thinking "disabled"
    # only at effort "high" or below, and rejects temperature outright.
    llm_effort: str = "low"
    llm_thinking_disabled: bool = True
    # Structured outputs make the model return schema-valid JSON. Flip off if the API
    # rejects the format parameter; the client still parses and validates either way.
    llm_structured_outputs: bool = True
    llm_timeout_seconds: float = 20.0

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
    per_ip_cooldown_seconds: float = 10.0
    per_ip_runs_per_hour: int = 20

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
