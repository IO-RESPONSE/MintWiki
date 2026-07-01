import pytest
from app.config import Settings


def test_settings_defaults():
    """Verify default settings values for local development."""
    settings = Settings()
    assert settings.app_name == "wiki-engine"
    assert settings.environment == "development"
    assert settings.database_url == "postgresql://localhost/wiki_engine"
    assert settings.redis_url == "redis://localhost:6379/0"


def test_settings_from_env(monkeypatch):
    """Verify settings can be loaded from environment variables."""
    monkeypatch.setenv("WIKI_DATABASE_URL", "postgresql://custom:pass@db.example.com/mydb")
    monkeypatch.setenv("WIKI_REDIS_URL", "redis://redis.example.com:6380/1")

    settings = Settings()
    assert settings.database_url == "postgresql://custom:pass@db.example.com/mydb"
    assert settings.redis_url == "redis://redis.example.com:6380/1"


def test_settings_partial_env_override(monkeypatch):
    """Verify environment variables override defaults partially."""
    monkeypatch.setenv("WIKI_DATABASE_URL", "postgresql://prod:pass@prod.db/wiki")

    settings = Settings()
    assert settings.database_url == "postgresql://prod:pass@prod.db/wiki"
    assert settings.redis_url == "redis://localhost:6379/0"
