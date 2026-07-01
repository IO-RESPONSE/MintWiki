"""Alembic environment configuration."""

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import sys
from pathlib import Path

# Add src directory to path so we can import app settings
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.config import Settings

# Only access context.config when running through alembic
config = None
if hasattr(context, 'config') and context.config is not None:
    config = context.config
    if config.config_file_name is not None:
        fileConfig(config.config_file_name)

settings = Settings()


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")

    context.configure(
        url=url,
        target_metadata=None,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")

    configuration = {}
    if config is not None:
        configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = url

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=None)

        with context.begin_transaction():
            context.run_migrations()


# Only run migrations if context is in a valid state (i.e., running through alembic)
try:
    if context.is_offline_mode():
        run_migrations_offline()
    else:
        run_migrations_online()
except Exception:
    # If context is not initialized (e.g., imported outside of alembic), skip
    pass
