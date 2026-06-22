import os
import sys
from logging.config import fileConfig

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

from app.db.session import Base
from app.models import User


# ==============================
# Alembic Config
# ==============================
config = context.config


# ==============================
# 优先使用环境变量 DATABASE_URL
#
# 作用：
# 1. 本地如果没有设置 DATABASE_URL，则继续使用 alembic.ini
# 2. GitHub Actions 中设置了 DATABASE_URL，则自动使用 CI 数据库
# 3. 避免 CI 里仍然读取 alembic.ini 中的 rag_user
# ==============================
database_url = os.getenv("DATABASE_URL")

if database_url:
    config.set_main_option("sqlalchemy.url", database_url)


# ==============================
# 日志配置
# ==============================
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# ==============================
# 模型元数据
# 用于 Alembic autogenerate
# ==============================
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in offline mode.
    """

    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
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

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
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