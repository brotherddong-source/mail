import asyncio
import os
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

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
    Railway DATABASE_URL / POSTGRES_URL 환경변수를 직접 읽어 asyncpg URL로 변환.
    없으면 alembic.ini 값 사용.
    """
    url = (
        os.environ.get("DATABASE_URL")
        or os.environ.get("POSTGRES_URL")
        or os.environ.get("POSTGRESQL_URL")
        or config.get_main_option("sqlalchemy.url", "")
    )
    # postgres:// 또는 postgresql:// → postgresql+asyncpg://
    url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    # 이미 asyncpg면 중복 치환 방지
    url = url.replace("postgresql+asyncpg+asyncpg://", "postgresql+asyncpg://")
    return url


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
    print(f"[alembic] DB URL host: {url.split('@')[-1].split('/')[0] if '@' in url else 'unknown'}")
    connectable = create_async_engine(
        url,
        poolclass=pool.NullPool,
        connect_args={"timeout": 5},  # 빠르게 실패하도록 5초 제한
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
