"""DiscussionAuditEvent 도메인 모델 테스트."""
from datetime import datetime

import pytest

from modules.discussion.audit_event import (
    DiscussionAuditAction,
    DiscussionAuditEvent,
    EmptyDiscussionAuditEventIdError,
    MissingDiscussionThreadIdError,
)


class TestDiscussionAuditEventCreation:
    """DiscussionAuditEvent 생성 시 필드가 올바르게 설정되는지 확인한다."""

    def test_creates_thread_created_event(self):
        occurred_at = datetime(2026, 1, 1, 0, 0, 0)
        event = DiscussionAuditEvent(
            id="event-1",
            action=DiscussionAuditAction.THREAD_CREATED,
            thread_id="thread-1",
            occurred_at=occurred_at,
            comment_id="comment-1",
            actor_id="user-1",
        )

        assert event.id == "event-1"
        assert event.action is DiscussionAuditAction.THREAD_CREATED
        assert event.thread_id == "thread-1"
        assert event.occurred_at == occurred_at
        assert event.comment_id == "comment-1"
        assert event.actor_id == "user-1"

    def test_creates_event_without_optional_fields(self):
        event = DiscussionAuditEvent(
            id="event-2",
            action=DiscussionAuditAction.THREAD_CLOSED,
            thread_id="thread-2",
            occurred_at=datetime(2026, 1, 1, 0, 0, 0),
        )

        assert event.comment_id is None
        assert event.actor_id is None

    def test_raises_when_id_is_empty(self):
        with pytest.raises(EmptyDiscussionAuditEventIdError):
            DiscussionAuditEvent(
                id="",
                action=DiscussionAuditAction.THREAD_CREATED,
                thread_id="thread-3",
                occurred_at=datetime(2026, 1, 1, 0, 0, 0),
            )

    def test_raises_when_id_is_blank(self):
        with pytest.raises(EmptyDiscussionAuditEventIdError):
            DiscussionAuditEvent(
                id="   ",
                action=DiscussionAuditAction.THREAD_CREATED,
                thread_id="thread-4",
                occurred_at=datetime(2026, 1, 1, 0, 0, 0),
            )

    def test_raises_when_thread_id_is_empty(self):
        with pytest.raises(MissingDiscussionThreadIdError):
            DiscussionAuditEvent(
                id="event-5",
                action=DiscussionAuditAction.THREAD_CREATED,
                thread_id="",
                occurred_at=datetime(2026, 1, 1, 0, 0, 0),
            )

    def test_raises_when_thread_id_is_blank(self):
        with pytest.raises(MissingDiscussionThreadIdError):
            DiscussionAuditEvent(
                id="event-6",
                action=DiscussionAuditAction.THREAD_CREATED,
                thread_id="   ",
                occurred_at=datetime(2026, 1, 1, 0, 0, 0),
            )


class TestDiscussionAuditEventActionChecks:
    """action 판단 메서드가 동작 종류를 올바르게 판단하는지 확인한다."""

    def _make_event(self, action: DiscussionAuditAction) -> DiscussionAuditEvent:
        return DiscussionAuditEvent(
            id="event-7",
            action=action,
            thread_id="thread-7",
            occurred_at=datetime(2026, 1, 1, 0, 0, 0),
        )

    def test_is_thread_created(self):
        event = self._make_event(DiscussionAuditAction.THREAD_CREATED)
        assert event.is_thread_created() is True
        assert event.is_thread_closed() is False
        assert event.is_thread_reopened() is False
        assert event.is_thread_paused() is False
        assert event.is_comment_added() is False

    def test_is_thread_closed(self):
        event = self._make_event(DiscussionAuditAction.THREAD_CLOSED)
        assert event.is_thread_closed() is True
        assert event.is_thread_created() is False

    def test_is_thread_reopened(self):
        event = self._make_event(DiscussionAuditAction.THREAD_REOPENED)
        assert event.is_thread_reopened() is True
        assert event.is_thread_closed() is False

    def test_is_thread_paused(self):
        event = self._make_event(DiscussionAuditAction.THREAD_PAUSED)
        assert event.is_thread_paused() is True
        assert event.is_thread_reopened() is False

    def test_is_comment_added(self):
        event = self._make_event(DiscussionAuditAction.COMMENT_ADDED)
        assert event.is_comment_added() is True
        assert event.is_thread_paused() is False
