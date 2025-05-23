import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# The 'prepend_sys_path = .' in alembic.ini should add the current directory (python_components) to sys.path
# Or, ensure alembic is run from the python_components directory.
# No explicit sys.path manipulation here if alembic.ini's prepend_sys_path works as expected.
# If not, the alternative is to ensure the calling environment (e.g. shell CWD) is python_components.

# Import your models and settings using relative paths from python_components
from core.config import settings
from db.session import Base
# Import all models that Alembic should know about
from models import user # This will import user.py which defines User, Role models

# Set target_metadata for autogenerate support
target_metadata = Base.metadata

def get_url():
    return settings.DATABASE_URL

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Include user-defined types for PostgreSQL (like UUID) if not automatically handled
        # compare_type=True, # May be needed for certain types
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # This configuration uses the URL directly from settings
    configuration = config.get_section(config.config_ini_section)
    configuration['sqlalchemy.url'] = get_url()
    
    connectable = engine_from_config(
        configuration, # Use the modified configuration
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            # compare_type=True # May be needed for certain types
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
