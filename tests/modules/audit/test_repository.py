"""감사 이벤트 저장소 인터페이스 테스트."""
from datetime import datetime

import pytest

from modules.audit.model import (
    AuditEvent,
    DuplicateAuditEventIdError,
)
from modules.audit.repository import (
    AuditRepository,
    InMemoryAuditRepository,
)


class TestAuditRepositoryInterface:
    """저장소 인터페이스 테스트."""

    def test_repository_is_abstract(self):
        """저장소는 추상 클래스이다."""
        with pytest.raises(TypeError):
            AuditRepository()

    def test_create_method_exists(self):
        """저장소는 create 메서드를 정의한다."""
        assert hasattr(AuditRepository, "create")

    def test_get_method_exists(self):
        """저장소는 get 메서드를 정의한다."""
        assert hasattr(AuditRepository, "get")

    def test_get_by_resource_id_method_exists(self):
        """저장소는 get_by_resource_id 메서드를 정의한다."""
        assert hasattr(AuditRepository, "get_by_resource_id")

    def test_list_all_method_exists(self):
        """저장소는 list_all 메서드를 정의한다."""
        assert hasattr(AuditRepository, "list_all")


class TestInMemoryAuditRepository:
    """인메모리 저장소 구현 테스트."""

    @pytest.mark.asyncio
    async def test_can_create_event(self):
        """인메모리 저장소는 감사 이벤트를 생성할 수 있다."""
        repo = InMemoryAuditRepository()
        event = AuditEvent(
            id="event-1",
            event_type="document",
            action="created",
            resource_id="doc-1",
            occurred_at=datetime(2026, 1, 1, 0, 0, 0),
            actor_id="user-1",
        )
        result = await repo.create(event)
        assert result.id == "event-1"
        assert result.event_type == "document"
        assert result.action == "created"
        assert result.resource_id == "doc-1"

    @pytest.mark.asyncio
    async def test_can_fetch_event_by_id(self):
        """인메모리 저장소는 id로 이벤트를 조회할 수 있다."""
        repo = InMemoryAuditRepository()
        event = AuditEvent(
            id="event-1",
            event_type="document",
            action="created",
            resource_id="doc-1",
            occurred_at=datetime(2026, 1, 1, 0, 0, 0),
            actor_id="user-1",
        )
        await repo.create(event)
        result = await repo.get("event-1")
        assert result is not None
        assert result.id == "event-1"
        assert result.event_type == "document"
        assert result.action == "created"

    @pytest.mark.asyncio
    async def test_returns_none_for_missing_id(self):
        """인메모리 저장소는 없는 id를 조회하면 None을 반환한다."""
        repo = InMemoryAuditRepository()
        result = await repo.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_can_fetch_events_by_resource_id(self):
        """인메모리 저장소는 리소스 id로 이벤트들을 조회할 수 있다."""
        repo = InMemoryAuditRepository()
        event1 = AuditEvent(
            id="event-1",
            event_type="document",
            action="created",
            resource_id="doc-1",
            occurred_at=datetime(2026, 1, 1, 0, 0, 0),
        )
        event2 = AuditEvent(
            id="event-2",
            event_type="document",
            action="updated",
            resource_id="doc-1",
            occurred_at=datetime(2026, 1, 1, 1, 0, 0),
        )
        event3 = AuditEvent(
            id="event-3",
            event_type="document",
            action="created",
            resource_id="doc-2",
            occurred_at=datetime(2026, 1, 1, 2, 0, 0),
        )
        await repo.create(event1)
        await repo.create(event2)
        await repo.create(event3)

        results = await repo.get_by_resource_id("doc-1")
        assert len(results) == 2
        assert results[0].id == "event-1"
        assert results[1].id == "event-2"

    @pytest.mark.asyncio
    async def test_returns_empty_list_for_missing_resource_id(self):
        """인메모리 저장소는 없는 리소스 id를 조회하면 빈 리스트를 반환한다."""
        repo = InMemoryAuditRepository()
        result = await repo.get_by_resource_id("nonexistent")
        assert result == []

    @pytest.mark.asyncio
    async def test_can_list_all_events(self):
        """인메모리 저장소는 모든 이벤트를 조회할 수 있다."""
        repo = InMemoryAuditRepository()
        event1 = AuditEvent(
            id="event-1",
            event_type="document",
            action="created",
            resource_id="doc-1",
            occurred_at=datetime(2026, 1, 1, 0, 0, 0),
        )
        event2 = AuditEvent(
            id="event-2",
            event_type="admin",
            action="updated",
            resource_id="rule-1",
            occurred_at=datetime(2026, 1, 1, 1, 0, 0),
        )
        await repo.create(event1)
        await repo.create(event2)

        results = await repo.list_all()
        assert len(results) == 2
        assert results[0].id == "event-1"
        assert results[1].id == "event-2"

    @pytest.mark.asyncio
    async def test_list_all_returns_empty_list_for_empty_repo(self):
        """인메모리 저장소는 비어있으면 list_all에서 빈 리스트를 반환한다."""
        repo = InMemoryAuditRepository()
        result = await repo.list_all()
        assert result == []

    @pytest.mark.asyncio
    async def test_can_store_multiple_events_with_different_resource_ids(self):
        """인메모리 저장소는 여러 리소스의 이벤트를 저장할 수 있다."""
        repo = InMemoryAuditRepository()
        event1 = AuditEvent(
            id="event-1",
            event_type="document",
            action="created",
            resource_id="doc-1",
            occurred_at=datetime(2026, 1, 1, 0, 0, 0),
        )
        event2 = AuditEvent(
            id="event-2",
            event_type="document",
            action="created",
            resource_id="doc-2",
            occurred_at=datetime(2026, 1, 1, 1, 0, 0),
        )
        event3 = AuditEvent(
            id="event-3",
            event_type="admin",
            action="created",
            resource_id="rule-1",
            occurred_at=datetime(2026, 1, 1, 2, 0, 0),
        )
        await repo.create(event1)
        await repo.create(event2)
        await repo.create(event3)

        all_events = await repo.list_all()
        doc1_events = await repo.get_by_resource_id("doc-1")
        doc2_events = await repo.get_by_resource_id("doc-2")
        rule1_events = await repo.get_by_resource_id("rule-1")

        assert len(all_events) == 3
        assert len(doc1_events) == 1
        assert len(doc2_events) == 1
        assert len(rule1_events) == 1

    @pytest.mark.asyncio
    async def test_preserves_event_details_through_create_and_get(self):
        """인메모리 저장소는 조회 시 이벤트 세부사항을 유지한다."""
        repo = InMemoryAuditRepository()
        occurred_at = datetime(2026, 1, 1, 12, 30, 45)
        event = AuditEvent(
            id="event-1",
            event_type="admin",
            action="updated",
            resource_id="rule-1",
            occurred_at=occurred_at,
            actor_id="admin-1",
        )
        await repo.create(event)

        result = await repo.get("event-1")
        assert result.id == "event-1"
        assert result.event_type == "admin"
        assert result.action == "updated"
        assert result.resource_id == "rule-1"
        assert result.occurred_at == occurred_at
        assert result.actor_id == "admin-1"

    @pytest.mark.asyncio
    async def test_raises_on_duplicate_event_id(self):
        """인메모리 저장소는 동일한 id로 생성 시 DuplicateAuditEventIdError를 발생시킨다."""
        repo = InMemoryAuditRepository()
        event1 = AuditEvent(
            id="event-1",
            event_type="document",
            action="created",
            resource_id="doc-1",
            occurred_at=datetime(2026, 1, 1, 0, 0, 0),
        )
        event2 = AuditEvent(
            id="event-1",
            event_type="admin",
            action="updated",
            resource_id="doc-1",
            occurred_at=datetime(2026, 1, 1, 1, 0, 0),
        )
        await repo.create(event1)
        with pytest.raises(DuplicateAuditEventIdError):
            await repo.create(event2)

    @pytest.mark.asyncio
    async def test_event_ordering_in_get_by_resource_id(self):
        """인메모리 저장소는 리소스별 조회 시 생성 순서를 유지한다."""
        repo = InMemoryAuditRepository()
        event1 = AuditEvent(
            id="event-1",
            event_type="document",
            action="created",
            resource_id="doc-1",
            occurred_at=datetime(2026, 1, 1, 0, 0, 0),
        )
        event2 = AuditEvent(
            id="event-2",
            event_type="document",
            action="updated",
            resource_id="doc-1",
            occurred_at=datetime(2026, 1, 1, 1, 0, 0),
        )
        event3 = AuditEvent(
            id="event-3",
            event_type="document",
            action="deleted",
            resource_id="doc-1",
            occurred_at=datetime(2026, 1, 1, 2, 0, 0),
        )
        await repo.create(event1)
        await repo.create(event2)
        await repo.create(event3)

        results = await repo.get_by_resource_id("doc-1")
        assert [e.id for e in results] == ["event-1", "event-2", "event-3"]


class TestAppendOnlyBehavior:
    """감사 저장소의 append-only 동작을 테스트한다."""

    @pytest.mark.asyncio
    async def test_append_only_prevents_duplicate_ids_across_resources(self):
        """동일한 id는 다른 리소스에도 허용되지 않는다."""
        repo = InMemoryAuditRepository()
        event1 = AuditEvent(
            id="event-1",
            event_type="document",
            action="created",
            resource_id="doc-1",
            occurred_at=datetime(2026, 1, 1, 0, 0, 0),
        )
        event2 = AuditEvent(
            id="event-1",
            event_type="admin",
            action="created",
            resource_id="rule-1",
            occurred_at=datetime(2026, 1, 1, 1, 0, 0),
        )
        await repo.create(event1)
        with pytest.raises(DuplicateAuditEventIdError):
            await repo.create(event2)

    @pytest.mark.asyncio
    async def test_append_only_maintains_event_count_after_duplicate_attempt(self):
        """중복 id 생성 시도 후에도 이벤트 개수는 변하지 않는다."""
        repo = InMemoryAuditRepository()
        event1 = AuditEvent(
            id="event-1",
            event_type="document",
            action="created",
            resource_id="doc-1",
            occurred_at=datetime(2026, 1, 1, 0, 0, 0),
        )
        event2 = AuditEvent(
            id="event-1",
            event_type="admin",
            action="updated",
            resource_id="doc-1",
            occurred_at=datetime(2026, 1, 1, 1, 0, 0),
        )
        await repo.create(event1)
        initial_count = len(await repo.list_all())

        try:
            await repo.create(event2)
        except DuplicateAuditEventIdError:
            pass

        final_count = len(await repo.list_all())
        assert initial_count == final_count == 1

    @pytest.mark.asyncio
    async def test_append_only_preserves_original_event_on_duplicate_attempt(self):
        """중복 id 생성 시도 후에도 원본 이벤트는 변하지 않는다."""
        repo = InMemoryAuditRepository()
        event1 = AuditEvent(
            id="event-1",
            event_type="document",
            action="created",
            resource_id="doc-1",
            occurred_at=datetime(2026, 1, 1, 0, 0, 0),
            actor_id="user-1",
        )
        event2 = AuditEvent(
            id="event-1",
            event_type="admin",
            action="updated",
            resource_id="doc-1",
            occurred_at=datetime(2026, 1, 1, 1, 0, 0),
            actor_id="admin-1",
        )
        await repo.create(event1)

        try:
            await repo.create(event2)
        except DuplicateAuditEventIdError:
            pass

        result = await repo.get("event-1")
        assert result.event_type == "document"
        assert result.action == "created"
        assert result.actor_id == "user-1"

    @pytest.mark.asyncio
    async def test_append_only_multiple_sequential_creates_maintains_order(self):
        """여러 순차적 이벤트 생성이 순서를 유지한다."""
        repo = InMemoryAuditRepository()
        event_ids = []
        for i in range(10):
            event = AuditEvent(
                id=f"event-{i}",
                event_type="document",
                action="created",
                resource_id="doc-1",
                occurred_at=datetime(2026, 1, 1, i, 0, 0),
            )
            await repo.create(event)
            event_ids.append(event.id)

        results = await repo.get_by_resource_id("doc-1")
        assert [e.id for e in results] == event_ids

    @pytest.mark.asyncio
    async def test_append_only_error_message_includes_id(self):
        """중복 id 에러 메시지가 해당 id를 포함한다."""
        repo = InMemoryAuditRepository()
        event1 = AuditEvent(
            id="duplicate-event-123",
            event_type="document",
            action="created",
            resource_id="doc-1",
            occurred_at=datetime(2026, 1, 1, 0, 0, 0),
        )
        event2 = AuditEvent(
            id="duplicate-event-123",
            event_type="admin",
            action="updated",
            resource_id="doc-1",
            occurred_at=datetime(2026, 1, 1, 1, 0, 0),
        )
        await repo.create(event1)

        with pytest.raises(DuplicateAuditEventIdError) as exc_info:
            await repo.create(event2)

        assert "duplicate-event-123" in str(exc_info.value)
