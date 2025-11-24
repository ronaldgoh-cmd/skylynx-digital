# File: backend/app/config.py (NEW FILE)
from pydantic import BaseSettings, AnyUrl

class Settings(BaseSettings):
    database_url: AnyUrl
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings(
    _env_file=".env",
    _env_file_encoding="utf-8",
)