from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import Settings


def build_engine(settings: Settings):
    """Create a database engine from settings."""
    return create_async_engine(
        settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
        echo=False,
    )


def get_session_factory(settings: Settings) -> sessionmaker:
    """Create a session factory from settings."""
    engine = build_engine(settings)
    return sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
