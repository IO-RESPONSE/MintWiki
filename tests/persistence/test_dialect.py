"""SQL dialect abstraction skeleton 테스트."""

import pytest

from persistence.dialect import DialectStrategy, SqlDialect


class TestSqlDialect:
    """SqlDialect enum 테스트."""

    def test_supports_postgresql_and_mariadb(self):
        """docs/mariadb-compatibility-matrix.md 가 확정한 두 dialect를 지원한다."""
        assert SqlDialect.POSTGRESQL == "postgresql"
        assert SqlDialect.MARIADB == "mariadb"


class TestDialectStrategy:
    """DialectStrategy skeleton 테스트."""

    def test_cannot_instantiate_without_upsert_statement(self):
        """upsert_statement를 구현하지 않으면 인스턴스화할 수 없다."""
        with pytest.raises(TypeError):
            DialectStrategy()

    def test_concrete_subclass_can_implement_contract(self):
        """구체 dialect 구현체는 upsert_statement를 채워 계약을 만족시킬 수 있다."""

        class PlaceholderDialect(DialectStrategy):
            dialect = SqlDialect.POSTGRESQL

            def upsert_statement(self, table, values, conflict_columns):
                raise NotImplementedError

        strategy = PlaceholderDialect()

        assert strategy.dialect == SqlDialect.POSTGRESQL
        with pytest.raises(NotImplementedError):
            strategy.upsert_statement(table=None, values={}, conflict_columns=[])
