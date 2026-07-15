from alembic import context
from sqlalchemy import engine_from_config,pool
from app.core.config import settings
from app.core.database import Base, database_url
from app.models import *
config=context.config; config.set_main_option("sqlalchemy.url",database_url); target_metadata=Base.metadata
def offline(): context.configure(url=settings.database_url,target_metadata=target_metadata,literal_binds=True,compare_type=True); context.run_migrations()
def online():
    with engine_from_config(config.get_section(config.config_ini_section),prefix="sqlalchemy.",poolclass=pool.NullPool).connect() as connection:
        context.configure(connection=connection,target_metadata=target_metadata,compare_type=True)
        with context.begin_transaction(): context.run_migrations()
offline() if context.is_offline_mode() else online()
