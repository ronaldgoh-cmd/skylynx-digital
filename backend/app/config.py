import logging

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from urllib.parse import unquote


class Settings(BaseSettings):
    # Default to a local SQLite database so development can proceed even if
    # environment variables are missing or contain placeholder template values.
    database_url: str = "sqlite:///./skylynx_local.db"
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    @field_validator("database_url")
    @classmethod
    def ensure_real_database_url(cls, value: str) -> str:
        """Warn on placeholder credentials and return a safe local fallback."""

        decoded_url = unquote(value)

        placeholder_markers = [
            "<YOUR_DB_USER_HERE>",
            "<YOUR_DB_PASSWORD_HERE>",
            "<YOUR_DB_NAME_HERE>",
        ]

        if any(marker in decoded_url for marker in placeholder_markers):
            fallback_url = "sqlite:///./skylynx_local.db"
            logging.warning(
                "Detected placeholder database credentials in .env; falling back to local SQLite at %s.",
                fallback_url,
            )
            return fallback_url

        if not decoded_url:
            logging.warning(
                "DATABASE_URL not provided; using local SQLite at %s.",
                value,
            )

        return value

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
