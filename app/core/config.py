from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


# 找到根目录下的 .env 文件
BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    # 应用基础配置
    APP_NAME: str = "AI Knowledge Base"
    APP_ENV: str = "dev"
    API_PREFIX: str = "/api"

    # 数据库配置
    DATABASE_URL: str

    # JWT认证配置
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # 文件存储目录
    STORAGE_DIR: str = "storage"

    # Embedding 配置
    EMBEDDING_PROVIDER: str = "aliyun"

    OPENAI_API_KEY: str | None = None
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    ALIYUN_API_KEY: str | None = None
    ALIYUN_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    ALIYUN_EMBEDDING_MODEL: str = "text-embedding-v4"
    ALIYUN_EMBEDDING_DIMENSION: int = 1536

    # LLM 配置
    LLM_PROVIDER: str = "aliyun"
    ALIYUN_CHAT_MODEL: str = "qwen-plus"

    # RAG 最小相似度阈值（过滤太不相关的 chunk）
    RAG_MIN_SCORE: float = 0.2

    # Celery + Redis 配置
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    model_config = SettingsConfigDict(env_file=ENV_FILE)

# 创建全局 settings 对象
settings = Settings()