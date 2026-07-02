"""관리자 보호 감사 이벤트 테스트."""
from datetime import datetime

import pytest

from modules.admin.protection_audit_event import (
    AdminProtectionAuditAction,
    AdminProtectionAuditEvent,
    EmptyAdminProtectionAuditEventIdError,
    MissingAdminProtectionAuditEventProtectionIdError,
)


class TestAdminProtectionAuditEventCreation:
    """감사 이벤트 생성 테스트."""

    def test_creates_event_with_required_fields(self):
        """필수 필드로 이벤트를 생성할 수 있다."""
        event = AdminProtectionAuditEvent(
            id="event1",
            action=AdminProtectionAuditAction.PROTECTION_CREATED,
            protection_id="protection1",
            occurred_at=datetime(2026, 1, 1),
        )

        assert event.id == "event1"
        assert event.action is AdminProtectionAuditAction.PROTECTION_CREATED
        assert event.protection_id == "protection1"
        assert event.occurred_at == datetime(2026, 1, 1)
        assert event.actor_id is None

    def test_creates_event_with_all_fields(self):
        """모든 필드로 이벤트를 생성할 수 있다."""
        event = AdminProtectionAuditEvent(
            id="event1",
            action=AdminProtectionAuditAction.PROTECTION_CREATED,
            protection_id="protection1",
            occurred_at=datetime(2026, 1, 1),
            actor_id="admin1",
        )

        assert event.id == "event1"
        assert event.action is AdminProtectionAuditAction.PROTECTION_CREATED
        assert event.protection_id == "protection1"
        assert event.occurred_at == datetime(2026, 1, 1)
        assert event.actor_id == "admin1"

    def test_raises_error_when_id_is_empty(self):
        """id가 비어있으면 예외가 발생한다."""
        with pytest.raises(EmptyAdminProtectionAuditEventIdError):
            AdminProtectionAuditEvent(
                id="",
                action=AdminProtectionAuditAction.PROTECTION_CREATED,
                protection_id="protection1",
                occurred_at=datetime(2026, 1, 1),
            )

    def test_raises_error_when_id_is_whitespace(self):
        """id가 공백만 있으면 예외가 발생한다."""
        with pytest.raises(EmptyAdminProtectionAuditEventIdError):
            AdminProtectionAuditEvent(
                id="   ",
                action=AdminProtectionAuditAction.PROTECTION_CREATED,
                protection_id="protection1",
                occurred_at=datetime(2026, 1, 1),
            )

    def test_raises_error_when_protection_id_is_empty(self):
        """protection_id가 비어있으면 예외가 발생한다."""
        with pytest.raises(MissingAdminProtectionAuditEventProtectionIdError):
            AdminProtectionAuditEvent(
                id="event1",
                action=AdminProtectionAuditAction.PROTECTION_CREATED,
                protection_id="",
                occurred_at=datetime(2026, 1, 1),
            )

    def test_raises_error_when_protection_id_is_whitespace(self):
        """protection_id가 공백만 있으면 예외가 발생한다."""
        with pytest.raises(MissingAdminProtectionAuditEventProtectionIdError):
            AdminProtectionAuditEvent(
                id="event1",
                action=AdminProtectionAuditAction.PROTECTION_CREATED,
                protection_id="   ",
                occurred_at=datetime(2026, 1, 1),
            )


class TestAdminProtectionAuditEventActions:
    """이벤트의 동작 확인 메서드 테스트."""

    def test_is_protection_created(self):
        """PROTECTION_CREATED 액션을 올바르게 확인한다."""
        event = AdminProtectionAuditEvent(
            id="event1",
            action=AdminProtectionAuditAction.PROTECTION_CREATED,
            protection_id="protection1",
            occurred_at=datetime(2026, 1, 1),
        )

        assert event.is_protection_created() is True
        assert event.is_protection_deleted() is False

    def test_is_protection_deleted(self):
        """PROTECTION_DELETED 액션을 올바르게 확인한다."""
        event = AdminProtectionAuditEvent(
            id="event1",
            action=AdminProtectionAuditAction.PROTECTION_DELETED,
            protection_id="protection1",
            occurred_at=datetime(2026, 1, 1),
        )

        assert event.is_protection_created() is False
        assert event.is_protection_deleted() is True
