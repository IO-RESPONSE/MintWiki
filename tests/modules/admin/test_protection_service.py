"""AdminProtectionService 테스트."""
from datetime import datetime, timedelta
from typing import Dict, Optional

import pytest

from modules.admin.protection_audit_event import AdminProtectionAuditAction
from modules.admin.protection_service import AdminProtectionService
from modules.document.protection import Protection
from modules.document.protection_repository import ProtectionRepository


class _FakeProtectionRepository(ProtectionRepository):
    """테스트용 메모리 기반 보호 저장소."""

    def __init__(self):
        self._protections: Dict[str, Protection] = {}

    async def create(self, protection: Protection) -> Protection:
        self._protections[protection.id] = protection
        return protection

    async def get(self, id: str) -> Optional[Protection]:
        return self._protections.get(id)

    async def get_by_document_id(self, document_id: str) -> Optional[Protection]:
        for protection in self._protections.values():
            if protection.document_id == document_id:
                return protection
        return None

    async def delete(self, id: str) -> None:
        if id in self._protections:
            del self._protections[id]


class TestAdminProtectionServiceCreateProtection:
    """보호 생성 테스트."""

    @pytest.mark.asyncio
    async def test_creates_protection_with_required_fields(self):
        """필수 필드로 보호를 생성할 수 있다."""
        repository = _FakeProtectionRepository()
        service = AdminProtectionService(repository)

        protection = await service.create_protection(document_id="doc1")

        assert protection.id is not None
        assert protection.document_id == "doc1"
        assert protection.created_at is not None
        assert protection.expires_at is None
        assert protection.reason is None
        assert protection.protected_by is None

    @pytest.mark.asyncio
    async def test_creates_protection_with_all_fields(self):
        """모든 필드로 보호를 생성할 수 있다."""
        repository = _FakeProtectionRepository()
        service = AdminProtectionService(repository)
        expires_at = datetime(2026, 1, 8)

        protection = await service.create_protection(
            document_id="doc1",
            reason="스팸 방지",
            expires_at=expires_at,
            actor_id="admin1",
        )

        assert protection.document_id == "doc1"
        assert protection.reason == "스팸 방지"
        assert protection.expires_at == expires_at
        assert protection.protected_by == "admin1"

    @pytest.mark.asyncio
    async def test_saves_protection_to_repository(self):
        """생성된 보호가 저장소에 저장된다."""
        repository = _FakeProtectionRepository()
        service = AdminProtectionService(repository)

        protection = await service.create_protection(document_id="doc1")

        retrieved = await repository.get(protection.id)
        assert retrieved is not None
        assert retrieved.id == protection.id
        assert retrieved.document_id == "doc1"

    @pytest.mark.asyncio
    async def test_records_audit_event_for_protection_creation(self):
        """보호 생성 시 감사 이벤트가 기록된다."""
        repository = _FakeProtectionRepository()
        service = AdminProtectionService(repository)

        protection = await service.create_protection(document_id="doc1", actor_id="admin1")

        events = service.events()
        assert len(events) == 1
        assert events[0].action is AdminProtectionAuditAction.PROTECTION_CREATED
        assert events[0].protection_id == protection.id
        assert events[0].actor_id == "admin1"
        assert events[0].is_protection_created() is True


class TestAdminProtectionServiceDeleteProtection:
    """보호 삭제 테스트."""

    @pytest.mark.asyncio
    async def test_deletes_protection_from_repository(self):
        """저장소에서 보호를 삭제할 수 있다."""
        repository = _FakeProtectionRepository()
        service = AdminProtectionService(repository)
        protection = await service.create_protection(document_id="doc1")

        await service.delete_protection(protection.id)

        retrieved = await repository.get(protection.id)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_records_audit_event_for_protection_deletion(self):
        """보호 삭제 시 감사 이벤트가 기록된다."""
        repository = _FakeProtectionRepository()
        service = AdminProtectionService(repository)
        protection = await service.create_protection(document_id="doc1")

        await service.delete_protection(protection.id, actor_id="admin1")

        events = service.events()
        assert len(events) == 2  # 생성 + 삭제
        assert events[1].action is AdminProtectionAuditAction.PROTECTION_DELETED
        assert events[1].protection_id == protection.id
        assert events[1].actor_id == "admin1"
        assert events[1].is_protection_deleted() is True


class TestAdminProtectionServiceEvents:
    """감사 이벤트 조회 테스트."""

    @pytest.mark.asyncio
    async def test_returns_events_in_order(self):
        """감사 이벤트가 시간 순서대로 반환된다."""
        repository = _FakeProtectionRepository()
        service = AdminProtectionService(repository)

        protection1 = await service.create_protection(document_id="doc1")
        protection2 = await service.create_protection(document_id="doc2")
        await service.delete_protection(protection1.id)

        events = service.events()
        assert len(events) == 3
        assert events[0].is_protection_created() is True
        assert events[0].protection_id == protection1.id
        assert events[1].is_protection_created() is True
        assert events[1].protection_id == protection2.id
        assert events[2].is_protection_deleted() is True
        assert events[2].protection_id == protection1.id

    @pytest.mark.asyncio
    async def test_returns_copy_of_events(self):
        """반환된 이벤트 목록은 내부 목록의 복사본이다."""
        repository = _FakeProtectionRepository()
        service = AdminProtectionService(repository)

        await service.create_protection(document_id="doc1")
        events1 = service.events()
        await service.create_protection(document_id="doc2")
        events2 = service.events()

        assert len(events1) == 1
        assert len(events2) == 2
