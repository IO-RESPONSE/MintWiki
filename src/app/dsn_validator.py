"""DSN validation and dialect detection.

지원 dialect(PostgreSQL, MariaDB)에 따른 DSN 검증과
dialect 추출 기능을 제공한다.
"""

from urllib.parse import urlparse
from typing import Literal


class InvalidDsnError(ValueError):
    """DSN 형식이 유효하지 않은 경우 발생한다."""

    pass


class UnsupportedDialectError(ValueError):
    """지원되지 않는 dialect를 감지한 경우 발생한다."""

    pass


def extract_dialect(dsn: str) -> Literal["postgresql", "mariadb"]:
    """DSN에서 dialect를 추출한다.

    Args:
        dsn: 데이터베이스 DSN 문자열.

    Returns:
        추출된 dialect ("postgresql" 또는 "mariadb").

    Raises:
        InvalidDsnError: DSN 형식이 유효하지 않은 경우.
        UnsupportedDialectError: 지원되지 않는 dialect인 경우.
    """
    if not dsn or not isinstance(dsn, str):
        raise InvalidDsnError(f"DSN must be a non-empty string, got: {type(dsn)}")

    try:
        parsed = urlparse(dsn)
    except Exception as e:
        raise InvalidDsnError(f"Failed to parse DSN: {e}")

    if not parsed.scheme:
        raise InvalidDsnError(f"DSN is missing scheme: {dsn}")

    scheme = parsed.scheme.lower()

    # PostgreSQL 방언 감지
    if scheme == "postgresql" or scheme == "postgres":
        return "postgresql"

    # MariaDB/MySQL 방언 감지
    # mysql, mysql+pymysql, mysql+mysqldb, mysql+aiomysql 등을 지원한다.
    if scheme == "mysql" or scheme.startswith("mysql+"):
        return "mariadb"

    # 지원되지 않는 방언
    raise UnsupportedDialectError(
        f"Unsupported dialect: {scheme}. "
        f"Supported dialects: postgresql, mariadb (mysql)"
    )


def validate_postgresql_dsn(dsn: str) -> bool:
    """PostgreSQL DSN 형식을 검증한다.

    Args:
        dsn: 검증할 PostgreSQL DSN 문자열.

    Returns:
        True if the DSN is valid for PostgreSQL.

    Raises:
        InvalidDsnError: DSN 형식이 유효하지 않은 경우.
    """
    dialect = extract_dialect(dsn)
    if dialect != "postgresql":
        raise InvalidDsnError(
            f"Expected PostgreSQL DSN (postgresql://...), got {dialect} dialect"
        )

    try:
        parsed = urlparse(dsn)
    except Exception as e:
        raise InvalidDsnError(f"Failed to parse PostgreSQL DSN: {e}")

    if not parsed.hostname:
        raise InvalidDsnError(f"PostgreSQL DSN is missing hostname: {dsn}")

    if not parsed.path or parsed.path == "/":
        raise InvalidDsnError(f"PostgreSQL DSN is missing database name: {dsn}")

    return True


def validate_mariadb_dsn(dsn: str) -> bool:
    """MariaDB DSN 형식을 검증한다.

    Args:
        dsn: 검증할 MariaDB DSN 문자열.

    Returns:
        True if the DSN is valid for MariaDB.

    Raises:
        InvalidDsnError: DSN 형식이 유효하지 않은 경우.
    """
    dialect = extract_dialect(dsn)
    if dialect != "mariadb":
        raise InvalidDsnError(
            f"Expected MariaDB DSN (mysql://... or mysql+driver://...), "
            f"got {dialect} dialect"
        )

    try:
        parsed = urlparse(dsn)
    except Exception as e:
        raise InvalidDsnError(f"Failed to parse MariaDB DSN: {e}")

    if not parsed.hostname:
        raise InvalidDsnError(f"MariaDB DSN is missing hostname: {dsn}")

    if not parsed.path or parsed.path == "/":
        raise InvalidDsnError(f"MariaDB DSN is missing database name: {dsn}")

    return True
