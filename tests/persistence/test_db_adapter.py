"""DB adapter 최소 계약 skeleton 테스트."""

import pytest

from persistence.db_adapter import DbAdapter


class TestDbAdapter:
    """DbAdapter ABC 테스트."""

    def test_cannot_instantiate_directly(self):
        """계약을 채우지 않은 채로는 인스턴스화할 수 없다."""
        with pytest.raises(TypeError):
            DbAdapter()

    @pytest.mark.asyncio
    async def test_concrete_subclass_can_satisfy_contract(self):
        """docs/db-adapter-contract.md §2의 다섯 가지 동작을 모두 구현하면 인스턴스화된다."""

        class InMemoryDbAdapter(DbAdapter):
            def __init__(self):
                self.rows = []
                self.committed = False

            async def add(self, row: object) -> None:
                self.rows.append(row)

            async def fetch_one(self, statement: object):
                return self.rows[0] if self.rows else None

            async def fetch_all(self, statement: object) -> list:
                return list(self.rows)

            async def execute(self, statement: object) -> None:
                pass

            async def commit(self) -> None:
                self.committed = True

            async def rollback(self) -> None:
                self.rows.clear()

        adapter = InMemoryDbAdapter()

        await adapter.add("row-1")
        assert await adapter.fetch_one(statement=None) == "row-1"
        assert await adapter.fetch_all(statement=None) == ["row-1"]

        await adapter.commit()
        assert adapter.committed is True

        await adapter.rollback()
        assert await adapter.fetch_all(statement=None) == []
