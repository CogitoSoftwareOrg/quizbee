import logging
from urllib.parse import urlparse

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings


from .utils.extract_pr import extract_pr_id_from_coolify_url


class Settings(BaseSettings):
    env: str = Field(default="local", alias="PUBLIC_ENV")
    coolify_url: str | None = Field(default=None)
    pr_id: int | None = Field(default=None)
    redis_prefix: str = Field(default="")

    pb_url: str = Field(default="http://localhost:8090", alias="PUBLIC_PB_URL")
    pb_email: str = Field(default="admin@admin.com")
    pb_password: str = Field(default="admin")

    redis_dsn: str = Field(default="redis://redis:6379/0")

    openai_api_key: str = Field(default="key")

    meilisearch_url: str = Field(default="http://localhost:7700")
    meilisearch_master_key: str = Field(default="key")

    brave_search_url: str = Field(default="https://search.brave.com")
    brave_search_api_key: str = Field(default="key")

    # Logging configuration
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")
    log_requests: bool = Field(default=True)
    log_slow_requests_threshold: float = Field(default=1.0)

    # Langfuse configuration
    langfuse_public_key: str = Field(default="key")
    langfuse_secret_key: str = Field(default="key")
    langfuse_host: str = Field(default="https://cloud.langfuse.com")

    # Telegram configuration
    tg_token: str = Field(default="key")
    tg_id: str = Field(default="key")

    @model_validator(mode="after")
    def derive_pr_id(self) -> "Settings":
        if self.env == "preview" and self.coolify_url is not None:
            maybe_pr = extract_pr_id_from_coolify_url(self.coolify_url)
            if maybe_pr is not None:
                self.pr_id = maybe_pr

        if self.env == "preview" and self.pr_id is not None:
            parsed = urlparse(self.pb_url)
            hostname = parsed.hostname or ""
            self.pb_url = f"https://{self.pr_id}.{hostname}"

        return self

    class Config:
        env_file = ".env"


settings = Settings()
