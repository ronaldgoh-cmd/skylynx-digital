import os
from dotenv import load_dotenv

load_dotenv()

# Always replace placeholders when deploying
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./skylynx.db",
)
SECRET_KEY = os.getenv("SECRET_KEY", "localdev-secret-key")
ACCESS_TOKEN_EXPIRE_MINUTES = 60