"""
Alembic environment configuration.

CRITICAL: This module imports ONLY models from common.models.
It does NOT import config, db, or any service-level code.
"""

import os
from logging.config import fileConfig
from urllib.parse import urlparse

from alembic import context
from sqlalchemy import engine_from_config, pool

# Import ONLY the Base and models - NO config or db imports
from common.models import Base

# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata from models
target_metadata = Base.metadata


def get_url():
    """
    Get database URL from environment variables.

    Supports two modes:
    1. Direct: DATABASE_URL environment variable
    2. Supabase: SUPABASE_URL + SUPABASE_SECRET_KEY environment variables
    
    Supabase mode constructs the PostgreSQL connection URL from Supabase credentials.
    """
    # Try DATABASE_URL first
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url
    
    # Build from Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_secret_key = os.getenv("SUPABASE_SECRET_KEY")
    
    if supabase_url and supabase_secret_key:
        # Parse Supabase URL to extract project ref
        parsed = urlparse(supabase_url)
        hostname = parsed.hostname or ""
        project_ref = hostname.split('.')[0] if hostname else ""
        
        if project_ref:
            # Build direct connection URL to Supabase PostgreSQL
            # Format: postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres
            return f"postgresql://postgres:{supabase_secret_key}@db.{project_ref}.supabase.co:5432/postgres"
    
    # Fallback (will fail, but provides clear error)
    raise ValueError(
        "Database connection not configured. Please set either:\n"
        "  1. DATABASE_URL environment variable, or\n"
        "  2. Both SUPABASE_URL and SUPABASE_SECRET_KEY environment variables"
    )


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine,
    though an Engine is acceptable here as well. By skipping the
    Engine creation we don't even need a DBAPI to be available.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    In this scenario we need to create an Engine and associate
    a connection with the context.
    """
    configuration = config.get_section(
        config.config_ini_section
    ) or {}
    configuration["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
