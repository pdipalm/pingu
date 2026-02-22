import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = None


def _apply_database_url_fallback() -> str | None:
    """
    If alembic was invoked with an explicit sqlalchemy.url (eg tests),
    do not override it. Otherwise, fall back to DATABASE_URL.
    """
    existing_url = config.get_main_option("sqlalchemy.url")
    if existing_url:
        return existing_url

    env_url = os.getenv("DATABASE_URL")
    if env_url:
        config.set_main_option("sqlalchemy.url", env_url)
        return env_url

    return None


def run_migrations_offline() -> None:
    url = _apply_database_url_fallback()
    if not url:
        raise RuntimeError(
            "No database URL configured for Alembic (sqlalchemy.url or DATABASE_URL)."
        )

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    _apply_database_url_fallback()

    connectable = engine_from_config(
        config.get_section(config.config_ini_section) or {},
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
