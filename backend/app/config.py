import os
from dotenv import load_dotenv

load_dotenv()

# Always replace placeholders when deploying
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://<DB_USER>:<DB_PASSWORD>@localhost:5432/<DB_NAME>"
)
SECRET_KEY = os.getenv("SECRET_KEY", "<CHANGE_ME_TO_RANDOM_STRING>")
ACCESS_TOKEN_EXPIRE_MINUTES = 60