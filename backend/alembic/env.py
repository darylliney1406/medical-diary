import re
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Import all models so Alembic sees them
from app.database import Base
import app.models  # noqa: F401 — registers all models

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _make_sync_url(url: str) -> str:
    """Convert asyncpg URL to psycopg2 for Alembic's sync engine."""
    return re.sub(r"postgresql\+asyncpg", "postgresql+psycopg2", url)


def run_migrations_offline() -> None:
    from app.config import get_settings
    url = _make_sync_url(get_settings().DATABASE_URL)
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    from app.config import get_settings
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = _make_sync_url(get_settings().DATABASE_URL)
    connectable = engine_from_config(configuration, prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
