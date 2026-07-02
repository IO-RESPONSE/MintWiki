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


def test_settings_mariadb_dsn_defaults_to_none():
    """MariaDB DSN은 아직 드라이버 전환 전 placeholder이므로 기본값은 None이다."""
    settings = Settings()
    assert settings.mariadb_dsn is None


def test_settings_mariadb_dsn_from_env(monkeypatch):
    """MariaDB DSN 값은 환경 변수로 읽어둘 수 있지만 아직 어디에서도 사용되지 않는다."""
    monkeypatch.setenv("WIKI_MARIADB_DSN", "mysql+pymysql://wiki:wiki@localhost:3306/wiki_engine")

    settings = Settings()
    assert settings.mariadb_dsn == "mysql+pymysql://wiki:wiki@localhost:3306/wiki_engine"
    # database_url은 여전히 postgresql 경로를 유지한다(드라이버 전환은 이 태스크 범위 밖).
    assert settings.database_url == "postgresql://localhost/wiki_engine"
