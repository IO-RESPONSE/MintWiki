"""DB driver capability model 테스트."""

import pytest

from persistence.capability import DriverCapabilities, capabilities_for
from persistence.dialect import SqlDialect


class TestCapabilitiesFor:
    """capabilities_for() 조회 테스트."""

    def test_postgresql_supports_returning_json_and_fulltext(self):
        """PostgreSQL은 RETURNING/JSON/전문 검색을 모두 네이티브 지원한다."""
        caps = capabilities_for(SqlDialect.POSTGRESQL)

        assert caps.dialect == SqlDialect.POSTGRESQL
        assert caps.supports_returning is True
        assert caps.supports_json is True
        assert caps.supports_fulltext is True

    def test_mariadb_does_not_support_returning_json_or_fulltext(self):
        """MariaDB는 docs/mariadb-compatibility-matrix.md의 금지 목록대로
        RETURNING/JSON 연산자/전문 검색을 네이티브 지원하지 않는다."""
        caps = capabilities_for(SqlDialect.MARIADB)

        assert caps.dialect == SqlDialect.MARIADB
        assert caps.supports_returning is False
        assert caps.supports_json is False
        assert caps.supports_fulltext is False

    def test_unknown_dialect_raises_key_error(self):
        """등록되지 않은 dialect는 KeyError를 던진다."""
        with pytest.raises(KeyError):
            capabilities_for("oracle")


class TestDriverCapabilities:
    """DriverCapabilities 값 객체 테스트."""

    def test_is_frozen(self):
        """DriverCapabilities는 불변 값 객체다."""
        caps = capabilities_for(SqlDialect.POSTGRESQL)

        with pytest.raises(AttributeError):
            caps.supports_returning = False

    def test_can_construct_directly(self):
        """DriverCapabilities는 레지스트리 밖에서도 직접 생성할 수 있다."""
        caps = DriverCapabilities(
            dialect=SqlDialect.MARIADB,
            supports_returning=False,
            supports_json=False,
            supports_fulltext=False,
        )

        assert caps.dialect == SqlDialect.MARIADB
