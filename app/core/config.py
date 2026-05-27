from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    APP_NAME: str = "AI Knowledge Base"
    APP_ENV: str = "dev"
    API_PREFIX: str = "/api"

    DATABASE_URL: str

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    STORAGE_DIR: str = "storage"

    EMBEDDING_PROVIDER: str = "aliyun"

    OPENAI_API_KEY: str | None = None
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    ALIYUN_API_KEY: str | None = None
    ALIYUN_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    ALIYUN_EMBEDDING_MODEL: str = "text-embedding-v4"
    ALIYUN_EMBEDDING_DIMENSION: int = 1536

    model_config = SettingsConfigDict(env_file=ENV_FILE)


settings = Settings()