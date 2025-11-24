import logging

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from urllib.parse import unquote


SQLITE_FALLBACK_URL = "sqlite:///./skylynx_local.db"


class Settings(BaseSettings):
    # Default to a local SQLite database so development can proceed even if
    # environment variables are missing or contain placeholder template values.
    database_url: str = SQLITE_FALLBACK_URL
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    @field_validator("database_url")
    @classmethod
    def ensure_real_database_url(cls, value: str) -> str:
        """Force SQLite for local development until a real database is configured."""

        decoded_url = unquote(value) if value else ""

        placeholder_markers = [
            "<YOUR_DB_USER_HERE>",
            "<YOUR_DB_PASSWORD_HERE>",
            "<YOUR_DB_NAME_HERE>",
        ]

        if not decoded_url:
            logging.info(
                "DATABASE_URL not provided; using local SQLite at %s.", SQLITE_FALLBACK_URL
            )
            return SQLITE_FALLBACK_URL

        if any(marker in decoded_url for marker in placeholder_markers):
            logging.info(
                "Detected placeholder credentials in DATABASE_URL; forcing local SQLite at %s for now.",
                SQLITE_FALLBACK_URL,
            )
            return SQLITE_FALLBACK_URL

        if not decoded_url.startswith("sqlite:"):
            logging.info(
                "Non-SQLite DATABASE_URL provided (%s); using local SQLite at %s until remote DB is configured.",
                decoded_url,
                SQLITE_FALLBACK_URL,
            )
            return SQLITE_FALLBACK_URL

        return decoded_url

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
