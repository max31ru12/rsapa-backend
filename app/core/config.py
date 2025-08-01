from os import getenv
from pathlib import Path

from dotenv import load_dotenv
from fastapi_mail import ConnectionConfig
from pydantic_settings import BaseSettings

load_dotenv()

DEV_MODE: bool = getenv("DEV_MODE", "true").strip().lower() in {"true", "1", "yes"}

# ~\Desktop\rsapa-backend
BASE_DIR = Path(__file__).parent.parent.parent

CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Settings(BaseSettings):
    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"
    DB_PASSWORD: str = "test"
    DB_USER: str = "test"
    DB_NAME: str = "test"

    SECRET_KEY: str
    ALGORITHM: str

    ACCESS_TOKEN_LIFESPAN_HOURS: int = 1
    REFRESH_TOKEN_LIFETIME_DAYS: int = 1
    REFRESH_TOKEN_REMEMBER_ME_LIFETIME_DAYS: int = 30

    MEDIA_DIR_NAME: str = "media"
    MEDIA_API_PATH: str = "/api/media"
    MEDIA_STORAGE_PATH: Path = BASE_DIR / "media"

    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str

    class ConfigDict:
        env: Path = BASE_DIR / ".env"


settings = Settings()

DB_URL: str = f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
TEST_DB_URL: str = (
    f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/test"
)

MAIL_CONFIG = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)
