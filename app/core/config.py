from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "AI Knowledge Base"
    APP_ENV: str = "dev"
    API_PREFIX: str = "/api"

    class Config:
        env_file = ".env"


settings = Settings()
