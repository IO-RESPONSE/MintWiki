import pytest
from app.config import Settings
from app.dsn_validator import (
    extract_dialect,
    validate_postgresql_dsn,
    validate_mariadb_dsn,
    InvalidDsnError,
    UnsupportedDialectError,
)


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


# ============================================================================
# DSN Dialect 추출 및 검증 테스트
# ============================================================================


class TestExtractDialect:
    """DSN에서 dialect를 추출하는 기능을 테스트한다."""

    def test_extract_postgresql_dialect_from_standard_dsn(self):
        """표준 PostgreSQL DSN에서 dialect를 추출한다."""
        dialect = extract_dialect("postgresql://localhost/wiki_engine")
        assert dialect == "postgresql"

    def test_extract_postgresql_dialect_from_postgres_alias(self):
        """postgres 별칭 DSN에서 dialect를 추출한다."""
        dialect = extract_dialect("postgres://localhost/wiki_engine")
        assert dialect == "postgresql"

    def test_extract_postgresql_dialect_with_credentials(self):
        """인증 정보가 포함된 PostgreSQL DSN에서 dialect를 추출한다."""
        dialect = extract_dialect("postgresql://user:password@localhost:5432/wiki_engine")
        assert dialect == "postgresql"

    def test_extract_mariadb_dialect_from_mysql_dsn(self):
        """mysql 스킴 DSN에서 dialect를 추출한다."""
        dialect = extract_dialect("mysql://wiki:wiki@localhost:3306/wiki_engine")
        assert dialect == "mariadb"

    def test_extract_mariadb_dialect_with_driver(self):
        """mysql+pymysql 형태의 DSN에서 dialect를 추출한다."""
        dialect = extract_dialect("mysql+pymysql://wiki:wiki@localhost:3306/wiki_engine")
        assert dialect == "mariadb"

    def test_extract_mariadb_dialect_with_mysqldb_driver(self):
        """mysql+mysqldb 형태의 DSN에서 dialect를 추출한다."""
        dialect = extract_dialect("mysql+mysqldb://wiki:wiki@localhost:3306/wiki_engine")
        assert dialect == "mariadb"

    def test_extract_mariadb_dialect_with_aiomysql_driver(self):
        """mysql+aiomysql 형태의 DSN에서 dialect를 추출한다."""
        dialect = extract_dialect("mysql+aiomysql://wiki:wiki@localhost:3306/wiki_engine")
        assert dialect == "mariadb"

    def test_extract_dialect_from_uppercase_scheme(self):
        """대문자 스킴을 정규화하여 dialect를 추출한다."""
        dialect = extract_dialect("POSTGRESQL://localhost/wiki_engine")
        assert dialect == "postgresql"

        dialect = extract_dialect("MYSQL+PYMYSQL://localhost/wiki_engine")
        assert dialect == "mariadb"

    def test_extract_dialect_raises_on_empty_dsn(self):
        """빈 문자열 DSN에서 InvalidDsnError를 발생시킨다."""
        with pytest.raises(InvalidDsnError):
            extract_dialect("")

    def test_extract_dialect_raises_on_none_dsn(self):
        """None DSN에서 InvalidDsnError를 발생시킨다."""
        with pytest.raises(InvalidDsnError):
            extract_dialect(None)

    def test_extract_dialect_raises_on_missing_scheme(self):
        """스킴이 없는 DSN에서 InvalidDsnError를 발생시킨다."""
        with pytest.raises(InvalidDsnError):
            extract_dialect("localhost/wiki_engine")

    def test_extract_dialect_raises_on_unsupported_scheme(self):
        """지원되지 않는 스킴에서 UnsupportedDialectError를 발생시킨다."""
        with pytest.raises(UnsupportedDialectError):
            extract_dialect("sqlite:///wiki_engine.db")

    def test_extract_dialect_raises_on_http_scheme(self):
        """HTTP 스킴에서 UnsupportedDialectError를 발생시킨다."""
        with pytest.raises(UnsupportedDialectError):
            extract_dialect("http://localhost/wiki_engine")

    def test_extract_dialect_raises_on_redis_scheme(self):
        """Redis 스킴에서 UnsupportedDialectError를 발생시킨다."""
        with pytest.raises(UnsupportedDialectError):
            extract_dialect("redis://localhost:6379/0")


class TestValidatePostgresqlDsn:
    """PostgreSQL DSN 검증 기능을 테스트한다."""

    def test_validate_standard_postgresql_dsn(self):
        """표준 PostgreSQL DSN을 검증한다."""
        assert validate_postgresql_dsn("postgresql://localhost/wiki_engine") is True

    def test_validate_postgresql_dsn_with_credentials(self):
        """인증 정보가 포함된 PostgreSQL DSN을 검증한다."""
        result = validate_postgresql_dsn(
            "postgresql://wiki:wiki@localhost:5432/wiki_engine"
        )
        assert result is True

    def test_validate_postgresql_dsn_with_port(self):
        """포트가 명시된 PostgreSQL DSN을 검증한다."""
        result = validate_postgresql_dsn(
            "postgresql://localhost:5432/wiki_engine"
        )
        assert result is True

    def test_validate_postgresql_dsn_with_postgres_alias(self):
        """postgres 별칭으로 된 PostgreSQL DSN을 검증한다."""
        assert validate_postgresql_dsn("postgres://localhost/wiki_engine") is True

    def test_validate_postgresql_dsn_raises_on_mariadb_dsn(self):
        """MariaDB DSN을 PostgreSQL 검증에 전달하면 InvalidDsnError를 발생시킨다."""
        with pytest.raises(InvalidDsnError):
            validate_postgresql_dsn(
                "mysql+pymysql://wiki:wiki@localhost:3306/wiki_engine"
            )

    def test_validate_postgresql_dsn_raises_on_missing_hostname(self):
        """호스트명이 없는 DSN을 검증하면 InvalidDsnError를 발생시킨다."""
        with pytest.raises(InvalidDsnError):
            validate_postgresql_dsn("postgresql:///wiki_engine")

    def test_validate_postgresql_dsn_raises_on_missing_database(self):
        """데이터베이스명이 없는 DSN을 검증하면 InvalidDsnError를 발생시킨다."""
        with pytest.raises(InvalidDsnError):
            validate_postgresql_dsn("postgresql://localhost")

    def test_validate_postgresql_dsn_raises_on_missing_database_with_slash(self):
        """경로만 있고 데이터베이스명이 없는 DSN을 검증하면 InvalidDsnError를 발생시킨다."""
        with pytest.raises(InvalidDsnError):
            validate_postgresql_dsn("postgresql://localhost/")


class TestValidateMariadbDsn:
    """MariaDB DSN 검증 기능을 테스트한다."""

    def test_validate_mariadb_dsn_with_pymysql_driver(self):
        """mysql+pymysql 형태의 MariaDB DSN을 검증한다."""
        result = validate_mariadb_dsn(
            "mysql+pymysql://wiki:wiki@localhost:3306/wiki_engine"
        )
        assert result is True

    def test_validate_mariadb_dsn_with_standard_mysql_scheme(self):
        """표준 mysql 스킴 DSN을 검증한다."""
        result = validate_mariadb_dsn("mysql://wiki:wiki@localhost:3306/wiki_engine")
        assert result is True

    def test_validate_mariadb_dsn_with_mysqldb_driver(self):
        """mysql+mysqldb 형태의 MariaDB DSN을 검증한다."""
        result = validate_mariadb_dsn(
            "mysql+mysqldb://wiki:wiki@localhost:3306/wiki_engine"
        )
        assert result is True

    def test_validate_mariadb_dsn_with_aiomysql_driver(self):
        """mysql+aiomysql 형태의 MariaDB DSN을 검증한다."""
        result = validate_mariadb_dsn(
            "mysql+aiomysql://wiki:wiki@localhost:3306/wiki_engine"
        )
        assert result is True

    def test_validate_mariadb_dsn_with_port(self):
        """포트가 명시된 MariaDB DSN을 검증한다."""
        result = validate_mariadb_dsn("mysql://localhost:3306/wiki_engine")
        assert result is True

    def test_validate_mariadb_dsn_raises_on_postgresql_dsn(self):
        """PostgreSQL DSN을 MariaDB 검증에 전달하면 InvalidDsnError를 발생시킨다."""
        with pytest.raises(InvalidDsnError):
            validate_mariadb_dsn("postgresql://localhost/wiki_engine")

    def test_validate_mariadb_dsn_raises_on_missing_hostname(self):
        """호스트명이 없는 MariaDB DSN을 검증하면 InvalidDsnError를 발생시킨다."""
        with pytest.raises(InvalidDsnError):
            validate_mariadb_dsn("mysql:///wiki_engine")

    def test_validate_mariadb_dsn_raises_on_missing_database(self):
        """데이터베이스명이 없는 MariaDB DSN을 검증하면 InvalidDsnError를 발생시킨다."""
        with pytest.raises(InvalidDsnError):
            validate_mariadb_dsn("mysql://localhost:3306")

    def test_validate_mariadb_dsn_raises_on_missing_database_with_slash(self):
        """경로만 있고 데이터베이스명이 없는 MariaDB DSN을 검증하면 InvalidDsnError를 발생시킨다."""
        with pytest.raises(InvalidDsnError):
            validate_mariadb_dsn("mysql://localhost:3306/")
