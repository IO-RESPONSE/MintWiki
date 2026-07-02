"""AdminBlockService 테스트."""
from datetime import datetime, timedelta
from typing import Dict, Optional

import pytest

from modules.admin.audit_event import AdminBlockAuditAction
from modules.admin.block_service import AdminBlockService
from modules.user.block import Block
from modules.user.block_repository import BlockRepository


class _FakeBlockRepository(BlockRepository):
    """테스트용 메모리 기반 차단 저장소."""

    def __init__(self):
        self._blocks: Dict[str, Block] = {}

    async def create(self, block: Block) -> Block:
        self._blocks[block.id] = block
        return block

    async def get(self, id: str) -> Optional[Block]:
        return self._blocks.get(id)

    async def get_by_user_id(self, user_id: str) -> Optional[Block]:
        for block in self._blocks.values():
            if block.user_id == user_id:
                return block
        return None

    async def delete(self, id: str) -> None:
        if id in self._blocks:
            del self._blocks[id]


class TestAdminBlockServiceCreateBlock:
    """차단 생성 테스트."""

    @pytest.mark.asyncio
    async def test_creates_block_with_required_fields(self):
        """필수 필드로 차단을 생성할 수 있다."""
        repository = _FakeBlockRepository()
        service = AdminBlockService(repository)

        block = await service.create_block(user_id="user1")

        assert block.id is not None
        assert block.user_id == "user1"
        assert block.created_at is not None
        assert block.expires_at is None
        assert block.reason is None
        assert block.blocked_by is None

    @pytest.mark.asyncio
    async def test_creates_block_with_all_fields(self):
        """모든 필드로 차단을 생성할 수 있다."""
        repository = _FakeBlockRepository()
        service = AdminBlockService(repository)
        expires_at = datetime(2026, 1, 8)

        block = await service.create_block(
            user_id="user1",
            reason="스팸",
            expires_at=expires_at,
            actor_id="admin1",
        )

        assert block.user_id == "user1"
        assert block.reason == "스팸"
        assert block.expires_at == expires_at
        assert block.blocked_by == "admin1"

    @pytest.mark.asyncio
    async def test_saves_block_to_repository(self):
        """생성된 차단이 저장소에 저장된다."""
        repository = _FakeBlockRepository()
        service = AdminBlockService(repository)

        block = await service.create_block(user_id="user1")

        retrieved = await repository.get(block.id)
        assert retrieved is not None
        assert retrieved.id == block.id
        assert retrieved.user_id == "user1"

    @pytest.mark.asyncio
    async def test_records_audit_event_for_block_creation(self):
        """차단 생성 시 감사 이벤트가 기록된다."""
        repository = _FakeBlockRepository()
        service = AdminBlockService(repository)

        block = await service.create_block(user_id="user1", actor_id="admin1")

        events = service.events()
        assert len(events) == 1
        assert events[0].action is AdminBlockAuditAction.BLOCK_CREATED
        assert events[0].block_id == block.id
        assert events[0].actor_id == "admin1"
        assert events[0].is_block_created() is True


class TestAdminBlockServiceDeleteBlock:
    """차단 삭제 테스트."""

    @pytest.mark.asyncio
    async def test_deletes_block_from_repository(self):
        """저장소에서 차단을 삭제할 수 있다."""
        repository = _FakeBlockRepository()
        service = AdminBlockService(repository)
        block = await service.create_block(user_id="user1")

        await service.delete_block(block.id)

        retrieved = await repository.get(block.id)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_records_audit_event_for_block_deletion(self):
        """차단 삭제 시 감사 이벤트가 기록된다."""
        repository = _FakeBlockRepository()
        service = AdminBlockService(repository)
        block = await service.create_block(user_id="user1")

        await service.delete_block(block.id, actor_id="admin1")

        events = service.events()
        assert len(events) == 2  # 생성 + 삭제
        assert events[1].action is AdminBlockAuditAction.BLOCK_DELETED
        assert events[1].block_id == block.id
        assert events[1].actor_id == "admin1"
        assert events[1].is_block_deleted() is True


class TestAdminBlockServiceEvents:
    """감사 이벤트 조회 테스트."""

    @pytest.mark.asyncio
    async def test_returns_events_in_order(self):
        """감사 이벤트가 시간 순서대로 반환된다."""
        repository = _FakeBlockRepository()
        service = AdminBlockService(repository)

        block1 = await service.create_block(user_id="user1")
        block2 = await service.create_block(user_id="user2")
        await service.delete_block(block1.id)

        events = service.events()
        assert len(events) == 3
        assert events[0].is_block_created() is True
        assert events[0].block_id == block1.id
        assert events[1].is_block_created() is True
        assert events[1].block_id == block2.id
        assert events[2].is_block_deleted() is True
        assert events[2].block_id == block1.id

    @pytest.mark.asyncio
    async def test_returns_copy_of_events(self):
        """반환된 이벤트 목록은 내부 목록의 복사본이다."""
        repository = _FakeBlockRepository()
        service = AdminBlockService(repository)

        await service.create_block(user_id="user1")
        events1 = service.events()
        await service.create_block(user_id="user2")
        events2 = service.events()

        assert len(events1) == 1
        assert len(events2) == 2
