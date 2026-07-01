import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import Settings
from app.database import build_engine, get_session_factory


def test_build_engine_from_settings():
    """Verify engine can be built from settings."""
    settings = Settings(database_url="postgresql://localhost/test_db")
    engine = build_engine(settings)
    assert engine is not None


def test_build_engine_converts_url_scheme():
    """Verify engine builds async-compatible URL."""
    settings = Settings(database_url="postgresql://localhost/test_db")
    engine = build_engine(settings)
    assert "asyncpg" in str(engine.url)


def test_get_session_factory_from_settings():
    """Verify session factory can be created from settings."""
    settings = Settings(database_url="postgresql://localhost/test_db")
    factory = get_session_factory(settings)
    assert isinstance(factory, sessionmaker)


def test_session_factory_creates_async_sessions():
    """Verify session factory is configured for AsyncSession."""
    settings = Settings(database_url="postgresql://localhost/test_db")
    factory = get_session_factory(settings)
    assert factory.class_.__name__ == "AsyncSession"
