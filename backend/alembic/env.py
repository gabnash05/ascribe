import os
from logging.config import fileConfig

from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

from alembic import context

# Import your models for autogenerate support
from app.core.database import Base

load_dotenv()

config = context.config

DATABASE_URL = os.getenv("DATABASE_URL")


# Convert async URL to sync URL for Alembic
def get_sync_database_url() -> str:
    """Convert async database URL to sync URL for Alembic migrations."""
    if DATABASE_URL:
        # Replace asyncpg with psycopg2 for sync connections
        sync_url = DATABASE_URL.replace("+asyncpg", "")
        # Also handle any other async drivers if needed
        sync_url = sync_url.replace("+aiopg", "")
        return sync_url
    return "postgresql://postgres:postgres@localhost:5432/postgres"


# Set the database URL in Alembic config (always set, fallback handled in get_sync_database_url)
config.set_main_option("sqlalchemy.url", get_sync_database_url())
# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target_metadata for autogenerate support
# This should be your SQLAlchemy Base metadata
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Get sync database URL
    sync_url = get_sync_database_url()

    # Get the configuration section and set the URL
    configuration = config.get_section(config.config_ini_section)
    if configuration is None:
        configuration = {}
    configuration["sqlalchemy.url"] = sync_url

    # Create the engine with sync configuration
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
