"""관리자 차단 감사 이벤트 테스트."""
from datetime import datetime

import pytest

from modules.admin.audit_event import (
    AdminBlockAuditAction,
    AdminBlockAuditEvent,
    EmptyAdminBlockAuditEventIdError,
    MissingAdminBlockAuditEventBlockIdError,
)


class TestAdminBlockAuditEventCreation:
    """감사 이벤트 생성 테스트."""

    def test_creates_event_with_required_fields(self):
        """필수 필드로 이벤트를 생성할 수 있다."""
        event = AdminBlockAuditEvent(
            id="event1",
            action=AdminBlockAuditAction.BLOCK_CREATED,
            block_id="block1",
            occurred_at=datetime(2026, 1, 1),
        )

        assert event.id == "event1"
        assert event.action is AdminBlockAuditAction.BLOCK_CREATED
        assert event.block_id == "block1"
        assert event.occurred_at == datetime(2026, 1, 1)
        assert event.actor_id is None

    def test_creates_event_with_all_fields(self):
        """모든 필드로 이벤트를 생성할 수 있다."""
        event = AdminBlockAuditEvent(
            id="event1",
            action=AdminBlockAuditAction.BLOCK_CREATED,
            block_id="block1",
            occurred_at=datetime(2026, 1, 1),
            actor_id="admin1",
        )

        assert event.id == "event1"
        assert event.action is AdminBlockAuditAction.BLOCK_CREATED
        assert event.block_id == "block1"
        assert event.occurred_at == datetime(2026, 1, 1)
        assert event.actor_id == "admin1"

    def test_raises_error_when_id_is_empty(self):
        """id가 비어있으면 예외가 발생한다."""
        with pytest.raises(EmptyAdminBlockAuditEventIdError):
            AdminBlockAuditEvent(
                id="",
                action=AdminBlockAuditAction.BLOCK_CREATED,
                block_id="block1",
                occurred_at=datetime(2026, 1, 1),
            )

    def test_raises_error_when_id_is_whitespace(self):
        """id가 공백만 있으면 예외가 발생한다."""
        with pytest.raises(EmptyAdminBlockAuditEventIdError):
            AdminBlockAuditEvent(
                id="   ",
                action=AdminBlockAuditAction.BLOCK_CREATED,
                block_id="block1",
                occurred_at=datetime(2026, 1, 1),
            )

    def test_raises_error_when_block_id_is_empty(self):
        """block_id가 비어있으면 예외가 발생한다."""
        with pytest.raises(MissingAdminBlockAuditEventBlockIdError):
            AdminBlockAuditEvent(
                id="event1",
                action=AdminBlockAuditAction.BLOCK_CREATED,
                block_id="",
                occurred_at=datetime(2026, 1, 1),
            )

    def test_raises_error_when_block_id_is_whitespace(self):
        """block_id가 공백만 있으면 예외가 발생한다."""
        with pytest.raises(MissingAdminBlockAuditEventBlockIdError):
            AdminBlockAuditEvent(
                id="event1",
                action=AdminBlockAuditAction.BLOCK_CREATED,
                block_id="   ",
                occurred_at=datetime(2026, 1, 1),
            )


class TestAdminBlockAuditEventActions:
    """이벤트의 동작 확인 메서드 테스트."""

    def test_is_block_created(self):
        """BLOCK_CREATED 액션을 올바르게 확인한다."""
        event = AdminBlockAuditEvent(
            id="event1",
            action=AdminBlockAuditAction.BLOCK_CREATED,
            block_id="block1",
            occurred_at=datetime(2026, 1, 1),
        )

        assert event.is_block_created() is True
        assert event.is_block_deleted() is False

    def test_is_block_deleted(self):
        """BLOCK_DELETED 액션을 올바르게 확인한다."""
        event = AdminBlockAuditEvent(
            id="event1",
            action=AdminBlockAuditAction.BLOCK_DELETED,
            block_id="block1",
            occurred_at=datetime(2026, 1, 1),
        )

        assert event.is_block_created() is False
        assert event.is_block_deleted() is True
