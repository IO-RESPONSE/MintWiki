"""AuditEvent 도메인 모델 테스트."""
from datetime import datetime

import pytest

from modules.audit.model import (
    AuditEvent,
    EmptyAuditEventIdError,
    MissingActionError,
    MissingEventTypeError,
    MissingResourceIdError,
)


class TestAuditEventCreation:
    """AuditEvent 생성 시 필드가 올바르게 설정되는지 확인한다."""

    def test_creates_audit_event(self):
        occurred_at = datetime(2026, 1, 1, 0, 0, 0)
        event = AuditEvent(
            id="event-1",
            event_type="document",
            action="created",
            resource_id="doc-1",
            occurred_at=occurred_at,
            actor_id="user-1",
        )

        assert event.id == "event-1"
        assert event.event_type == "document"
        assert event.action == "created"
        assert event.resource_id == "doc-1"
        assert event.occurred_at == occurred_at
        assert event.actor_id == "user-1"

    def test_creates_event_without_optional_actor_id(self):
        event = AuditEvent(
            id="event-2",
            event_type="admin",
            action="updated",
            resource_id="rule-1",
            occurred_at=datetime(2026, 1, 1, 0, 0, 0),
        )

        assert event.actor_id is None

    def test_creates_event_with_different_event_types(self):
        event_types = ["document", "admin", "permission", "auth", "job"]
        for event_type in event_types:
            event = AuditEvent(
                id=f"event-{event_type}",
                event_type=event_type,
                action="modified",
                resource_id="res-1",
                occurred_at=datetime(2026, 1, 1, 0, 0, 0),
            )
            assert event.event_type == event_type

    def test_raises_when_id_is_empty(self):
        with pytest.raises(EmptyAuditEventIdError):
            AuditEvent(
                id="",
                event_type="document",
                action="created",
                resource_id="doc-1",
                occurred_at=datetime(2026, 1, 1, 0, 0, 0),
            )

    def test_raises_when_id_is_blank(self):
        with pytest.raises(EmptyAuditEventIdError):
            AuditEvent(
                id="   ",
                event_type="document",
                action="created",
                resource_id="doc-1",
                occurred_at=datetime(2026, 1, 1, 0, 0, 0),
            )

    def test_raises_when_event_type_is_empty(self):
        with pytest.raises(MissingEventTypeError):
            AuditEvent(
                id="event-3",
                event_type="",
                action="created",
                resource_id="doc-1",
                occurred_at=datetime(2026, 1, 1, 0, 0, 0),
            )

    def test_raises_when_event_type_is_blank(self):
        with pytest.raises(MissingEventTypeError):
            AuditEvent(
                id="event-4",
                event_type="   ",
                action="created",
                resource_id="doc-1",
                occurred_at=datetime(2026, 1, 1, 0, 0, 0),
            )

    def test_raises_when_action_is_empty(self):
        with pytest.raises(MissingActionError):
            AuditEvent(
                id="event-5",
                event_type="document",
                action="",
                resource_id="doc-1",
                occurred_at=datetime(2026, 1, 1, 0, 0, 0),
            )

    def test_raises_when_action_is_blank(self):
        with pytest.raises(MissingActionError):
            AuditEvent(
                id="event-6",
                event_type="document",
                action="   ",
                resource_id="doc-1",
                occurred_at=datetime(2026, 1, 1, 0, 0, 0),
            )

    def test_raises_when_resource_id_is_empty(self):
        with pytest.raises(MissingResourceIdError):
            AuditEvent(
                id="event-7",
                event_type="document",
                action="created",
                resource_id="",
                occurred_at=datetime(2026, 1, 1, 0, 0, 0),
            )

    def test_raises_when_resource_id_is_blank(self):
        with pytest.raises(MissingResourceIdError):
            AuditEvent(
                id="event-8",
                event_type="document",
                action="created",
                resource_id="   ",
                occurred_at=datetime(2026, 1, 1, 0, 0, 0),
            )


class TestAuditEventWithDifferentActions:
    """다양한 action 값을 가진 AuditEvent를 생성할 수 있는지 확인한다."""

    def test_creates_event_with_various_actions(self):
        actions = ["created", "updated", "deleted", "archived", "restored"]
        for action in actions:
            event = AuditEvent(
                id=f"event-{action}",
                event_type="document",
                action=action,
                resource_id="doc-1",
                occurred_at=datetime(2026, 1, 1, 0, 0, 0),
            )
            assert event.action == action

    def test_creates_event_with_various_resource_ids(self):
        resource_ids = ["doc-1", "admin-rule-2", "perm-3", "auth-4", "job-5"]
        for resource_id in resource_ids:
            event = AuditEvent(
                id=f"event-{resource_id}",
                event_type="document",
                action="created",
                resource_id=resource_id,
                occurred_at=datetime(2026, 1, 1, 0, 0, 0),
            )
            assert event.resource_id == resource_id
