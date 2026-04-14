import asyncio
import os
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# app 모델 임포트 (마이그레이션 자동 감지용)
from app.database import Base  # noqa: F401
import app.domain.cases.models  # noqa: F401
import app.domain.mails.models  # noqa: F401
import app.domain.drafts.models  # noqa: F401
import app.domain.users.models  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _get_db_url() -> str:
    """
    Railway는 DATABASE_URL 또는 POSTGRES_URL 환경변수를 제공.
    pydantic-settings의 Settings 클래스가 이미 변환해주므로 그걸 사용.
    """
    from app.config import get_settings
    return get_settings().async_database_url


def run_migrations_offline() -> None:
    url = _get_db_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    url = _get_db_url()
    connectable = async_engine_from_config(
        {"sqlalchemy.url": url},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
