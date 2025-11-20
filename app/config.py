from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR.parent / "data.db"


class Settings(BaseSettings):
    app_name: str = "Operational Survey"
    secret_key: str = "change-me"  # should be overridden via env
    access_token_expire_minutes: int = 60 * 12
    algorithm: str = "HS256"
    database_url: str = f"sqlite:///{DB_PATH}"

    class Config:
        env_prefix = "SURVEY_"
        env_file = ".env"


def get_settings() -> Settings:
    return Settings()
