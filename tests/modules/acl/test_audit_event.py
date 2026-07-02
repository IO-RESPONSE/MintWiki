"""AclAuditEvent 도메인 모델 테스트."""
from datetime import datetime

import pytest

from modules.acl.audit_event import (
    AclAuditAction,
    AclAuditEvent,
    EmptyAclAuditEventIdError,
    MissingRuleIdError,
)


class TestAclAuditEventCreation:
    """AclAuditEvent 생성 시 필드가 올바르게 설정되는지 확인한다."""

    def test_creates_rule_added_event(self):
        occurred_at = datetime(2026, 1, 1, 0, 0, 0)
        event = AclAuditEvent(
            id="event-1",
            action=AclAuditAction.RULE_ADDED,
            rule_id="rule-1",
            occurred_at=occurred_at,
            document_id="doc-1",
            actor_id="user-1",
        )

        assert event.id == "event-1"
        assert event.action is AclAuditAction.RULE_ADDED
        assert event.rule_id == "rule-1"
        assert event.occurred_at == occurred_at
        assert event.document_id == "doc-1"
        assert event.actor_id == "user-1"

    def test_creates_event_without_optional_fields(self):
        event = AclAuditEvent(
            id="event-2",
            action=AclAuditAction.RULE_REMOVED,
            rule_id="rule-2",
            occurred_at=datetime(2026, 1, 1, 0, 0, 0),
        )

        assert event.document_id is None
        assert event.actor_id is None

    def test_raises_when_id_is_empty(self):
        with pytest.raises(EmptyAclAuditEventIdError):
            AclAuditEvent(
                id="",
                action=AclAuditAction.RULE_ADDED,
                rule_id="rule-3",
                occurred_at=datetime(2026, 1, 1, 0, 0, 0),
            )

    def test_raises_when_id_is_blank(self):
        with pytest.raises(EmptyAclAuditEventIdError):
            AclAuditEvent(
                id="   ",
                action=AclAuditAction.RULE_ADDED,
                rule_id="rule-4",
                occurred_at=datetime(2026, 1, 1, 0, 0, 0),
            )

    def test_raises_when_rule_id_is_empty(self):
        with pytest.raises(MissingRuleIdError):
            AclAuditEvent(
                id="event-5",
                action=AclAuditAction.RULE_ADDED,
                rule_id="",
                occurred_at=datetime(2026, 1, 1, 0, 0, 0),
            )

    def test_raises_when_rule_id_is_blank(self):
        with pytest.raises(MissingRuleIdError):
            AclAuditEvent(
                id="event-6",
                action=AclAuditAction.RULE_ADDED,
                rule_id="   ",
                occurred_at=datetime(2026, 1, 1, 0, 0, 0),
            )


class TestAclAuditEventIsRuleAdded:
    """is_rule_added 메서드가 동작 종류를 올바르게 판단하는지 확인한다."""

    def test_returns_true_for_rule_added_action(self):
        event = AclAuditEvent(
            id="event-7",
            action=AclAuditAction.RULE_ADDED,
            rule_id="rule-7",
            occurred_at=datetime(2026, 1, 1, 0, 0, 0),
        )

        assert event.is_rule_added() is True
        assert event.is_rule_removed() is False

    def test_returns_false_for_rule_removed_action(self):
        event = AclAuditEvent(
            id="event-8",
            action=AclAuditAction.RULE_REMOVED,
            rule_id="rule-8",
            occurred_at=datetime(2026, 1, 1, 0, 0, 0),
        )

        assert event.is_rule_added() is False


class TestAclAuditEventIsRuleRemoved:
    """is_rule_removed 메서드가 동작 종류를 올바르게 판단하는지 확인한다."""

    def test_returns_true_for_rule_removed_action(self):
        event = AclAuditEvent(
            id="event-9",
            action=AclAuditAction.RULE_REMOVED,
            rule_id="rule-9",
            occurred_at=datetime(2026, 1, 1, 0, 0, 0),
        )

        assert event.is_rule_removed() is True
