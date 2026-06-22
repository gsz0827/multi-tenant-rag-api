import os
import sys
from logging.config import fileConfig

from sqlalchemy import create_engine
from sqlalchemy import pool
from alembic import context

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Alembic Config
config = context.config


def get_database_url() -> str:
    """
    获取数据库连接地址。

    优先级：
    1. GitHub Actions / 本地环境变量 DATABASE_URL
    2. alembic.ini 中的 sqlalchemy.url
    """

    database_url = os.getenv("DATABASE_URL")

    if database_url:
        # 强制覆盖 alembic.ini 中的 sqlalchemy.url
        config.set_main_option("sqlalchemy.url", database_url)
        print("[Alembic] Using DATABASE_URL from environment")
        return database_url

    database_url = config.get_main_option("sqlalchemy.url")
    print("[Alembic] Using sqlalchemy.url from alembic.ini")
    return database_url


# 尽早设置数据库 URL，避免后续导入 app 配置时受到 .env 影响
DATABASE_URL = get_database_url()


# 日志配置
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# 导入模型元数据
from app.db.session import Base
from app.models import User

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in offline mode.
    """

    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named"
        },
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in online mode.
    """

    # 不再使用 engine_from_config，避免继续读取 alembic.ini 里的 rag_user
    connectable = create_engine(
        DATABASE_URL,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()