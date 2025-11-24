from pydantic import AnyUrl, field_validator
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
    def ensure_real_database_url(cls, value: AnyUrl) -> AnyUrl:
        url_str = str(value)
        decoded_url = unquote(url_str)

        placeholder_markers = [
            "<YOUR_DB_USER_HERE>",
            "<YOUR_DB_PASSWORD_HERE>",
            "<YOUR_DB_NAME_HERE>",
        ]

        if any(marker in decoded_url for marker in placeholder_markers):
            raise ValueError(
                "Please replace the placeholder database credentials in .env with real values "
                "(e.g., DB user, password, and database name)."
            )

        return value

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
