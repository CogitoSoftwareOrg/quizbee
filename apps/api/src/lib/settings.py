import logging
import os
from pathlib import Path
from urllib.parse import urlparse

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


from .utils.extract_pr import extract_pr_id_from_coolify_url

# Get absolute path to the .env file
_ROOT_DIR = Path(__file__).parent.parent.parent.parent.parent
_ENV_FILE = _ROOT_DIR / "envs" / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    env: str = Field(default="local")
    coolify_url: str | None = Field(default=None)
    pr_id: int | None = Field(default=None)
    redis_prefix: str = Field(default="")

    app_url: str = Field(default="http://localhost:5173", alias="PUBLIC_APP_URL")

    pb_url: str = Field(default="http://localhost:8090")
    pb_email: str = Field(default="admin@admin.com")
    pb_password: str = Field(default="admin")

    redis_dsn: str = Field(default="redis://redis:6379/0")

    openai_api_key: str = Field(default="key")

    meili_url: str = Field(default="http://localhost:7700")
    meili_master_key: str = Field(default="key")

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

    # Stripe configuration
    stripe_api_key: str = Field(default="key")
    stripe_webhook_secret: str = Field(default="key")

    @model_validator(mode="after")
    def derive_pr_id(self) -> "Settings":
        if self.env == "preview" and self.coolify_url is not None:
            maybe_pr = extract_pr_id_from_coolify_url(self.coolify_url)
            if maybe_pr is not None:
                self.pr_id = maybe_pr

        if self.env == "preview" and self.pr_id is not None:
            parsed = urlparse(self.pb_url)
            hostname = parsed.hostname or ""
            self.pb_url = f"https://{self.pr_id}-{hostname}/"

            app_url = urlparse(self.app_url)
            self.app_url = f"https://{self.pr_id}-{app_url.hostname}/"

        return self

    def model_post_init(self, __context) -> None:
        """Export all settings to environment variables after initialization."""
        for field_name, field_info in self.model_fields.items():
            # Get the actual value
            value = getattr(self, field_name)

            # Convert field name to uppercase for environment variable
            env_var_name = field_name.upper()

            # Only export non-None string values
            if value is not None:
                os.environ[env_var_name] = str(value)


settings = Settings()
