from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "AI Knowledge Base"
    APP_ENV: str = "dev"
    API_PREFIX: str = "/api"

    DATABASE_URL: str = "sqlite:///./dev.db"

    SECRET_KEY: str = "change-this-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    class Config:
        env_file = ".env"


settings = Settings()
