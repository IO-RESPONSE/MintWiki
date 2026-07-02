"""BlockCheckService 테스트."""
from datetime import datetime, timedelta
from typing import Dict, Optional

import pytest

from modules.user.block import Block
from modules.user.block_check_service import BlockCheckService
from modules.user.block_repository import BlockRepository


class _FakeBlockRepository(BlockRepository):
    """테스트용 메모리 기반 차단 저장소."""

    def __init__(self):
        self._blocks_by_user_id: Dict[str, Block] = {}

    async def create(self, block: Block) -> Block:
        self._blocks_by_user_id[block.user_id] = block
        return block

    async def get(self, id: str) -> Optional[Block]:
        for block in self._blocks_by_user_id.values():
            if block.id == id:
                return block
        return None

    async def get_by_user_id(self, user_id: str) -> Optional[Block]:
        return self._blocks_by_user_id.get(user_id)

    async def delete(self, id: str) -> None:
        for user_id, block in list(self._blocks_by_user_id.items()):
            if block.id == id:
                del self._blocks_by_user_id[user_id]


class TestBlockCheckServiceWithoutBlock:
    """차단 기록이 없는 사용자에 대한 확인 테스트."""

    @pytest.mark.asyncio
    async def test_returns_false_when_no_block_exists(self):
        """차단 기록이 없으면 차단되지 않은 것으로 판단한다."""
        service = BlockCheckService(_FakeBlockRepository())

        blocked = await service.is_blocked("user1", datetime(2026, 1, 1))

        assert blocked is False


class TestBlockCheckServiceWithActiveBlock:
    """유효한 차단이 있는 사용자에 대한 확인 테스트."""

    @pytest.mark.asyncio
    async def test_returns_true_for_indefinite_block(self):
        """만료 시각이 없는 차단은 항상 유효하다."""
        repository = _FakeBlockRepository()
        await repository.create(
            Block(id="block1", user_id="user1", created_at=datetime(2026, 1, 1))
        )
        service = BlockCheckService(repository)

        blocked = await service.is_blocked("user1", datetime(2099, 1, 1))

        assert blocked is True

    @pytest.mark.asyncio
    async def test_returns_true_before_expiry(self):
        """만료 시각 이전에는 차단된 것으로 판단한다."""
        created_at = datetime(2026, 1, 1)
        expires_at = created_at + timedelta(days=7)
        repository = _FakeBlockRepository()
        await repository.create(
            Block(
                id="block1",
                user_id="user1",
                created_at=created_at,
                expires_at=expires_at,
            )
        )
        service = BlockCheckService(repository)

        blocked = await service.is_blocked("user1", created_at + timedelta(days=1))

        assert blocked is True


class TestBlockCheckServiceWithExpiredBlock:
    """만료된 차단이 있는 사용자에 대한 확인 테스트."""

    @pytest.mark.asyncio
    async def test_returns_false_after_expiry(self):
        """만료 시각 이후에는 차단되지 않은 것으로 판단한다."""
        created_at = datetime(2026, 1, 1)
        expires_at = created_at + timedelta(days=7)
        repository = _FakeBlockRepository()
        await repository.create(
            Block(
                id="block1",
                user_id="user1",
                created_at=created_at,
                expires_at=expires_at,
            )
        )
        service = BlockCheckService(repository)

        blocked = await service.is_blocked("user1", expires_at + timedelta(seconds=1))

        assert blocked is False


class TestBlockCheckServiceIgnoresOtherUsers:
    """다른 사용자의 차단은 영향을 주지 않는지 확인한다."""

    @pytest.mark.asyncio
    async def test_returns_false_for_unblocked_user_when_another_is_blocked(self):
        """다른 사용자가 차단되어 있어도 조회 대상 사용자는 영향받지 않는다."""
        repository = _FakeBlockRepository()
        await repository.create(
            Block(id="block1", user_id="user1", created_at=datetime(2026, 1, 1))
        )
        service = BlockCheckService(repository)

        blocked = await service.is_blocked("user2", datetime(2026, 1, 2))

        assert blocked is False
