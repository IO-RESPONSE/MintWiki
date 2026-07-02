"""DiscussionRecentActivity 도메인 모델 테스트."""
from datetime import datetime

import pytest

from modules.discussion.audit_event import DiscussionAuditAction, DiscussionAuditEvent
from modules.discussion.recent_activity import (
    DiscussionRecentActivity,
    EmptyRecentActivityIdError,
    MissingRecentActivityThreadIdError,
)


class TestDiscussionRecentActivityCreation:
    """DiscussionRecentActivity 생성 시 필드가 올바르게 설정되는지 확인한다."""

    def test_creates_recent_activity(self):
        occurred_at = datetime(2026, 1, 1, 0, 0, 0)
        activity = DiscussionRecentActivity(
            id="activity-1",
            thread_id="thread-1",
            action=DiscussionAuditAction.THREAD_CREATED,
            occurred_at=occurred_at,
            comment_id="comment-1",
            actor_id="user-1",
        )

        assert activity.id == "activity-1"
        assert activity.thread_id == "thread-1"
        assert activity.action is DiscussionAuditAction.THREAD_CREATED
        assert activity.occurred_at == occurred_at
        assert activity.comment_id == "comment-1"
        assert activity.actor_id == "user-1"

    def test_creates_activity_without_optional_fields(self):
        activity = DiscussionRecentActivity(
            id="activity-2",
            thread_id="thread-2",
            action=DiscussionAuditAction.THREAD_CLOSED,
            occurred_at=datetime(2026, 1, 1, 0, 0, 0),
        )

        assert activity.comment_id is None
        assert activity.actor_id is None

    def test_raises_when_id_is_empty(self):
        with pytest.raises(EmptyRecentActivityIdError):
            DiscussionRecentActivity(
                id="",
                thread_id="thread-3",
                action=DiscussionAuditAction.THREAD_CREATED,
                occurred_at=datetime(2026, 1, 1, 0, 0, 0),
            )

    def test_raises_when_id_is_blank(self):
        with pytest.raises(EmptyRecentActivityIdError):
            DiscussionRecentActivity(
                id="   ",
                thread_id="thread-4",
                action=DiscussionAuditAction.THREAD_CREATED,
                occurred_at=datetime(2026, 1, 1, 0, 0, 0),
            )

    def test_raises_when_thread_id_is_empty(self):
        with pytest.raises(MissingRecentActivityThreadIdError):
            DiscussionRecentActivity(
                id="activity-5",
                thread_id="",
                action=DiscussionAuditAction.THREAD_CREATED,
                occurred_at=datetime(2026, 1, 1, 0, 0, 0),
            )

    def test_raises_when_thread_id_is_blank(self):
        with pytest.raises(MissingRecentActivityThreadIdError):
            DiscussionRecentActivity(
                id="activity-6",
                thread_id="   ",
                action=DiscussionAuditAction.THREAD_CREATED,
                occurred_at=datetime(2026, 1, 1, 0, 0, 0),
            )


class TestDiscussionRecentActivitySummary:
    """summary 속성이 활동 종류별로 올바른 요약 문구를 반환하는지 확인한다."""

    def _make_activity(self, action: DiscussionAuditAction) -> DiscussionRecentActivity:
        return DiscussionRecentActivity(
            id="activity-7",
            thread_id="thread-7",
            action=action,
            occurred_at=datetime(2026, 1, 1, 0, 0, 0),
        )

    def test_summary_for_thread_created(self):
        activity = self._make_activity(DiscussionAuditAction.THREAD_CREATED)
        assert activity.summary == "새 토론 스레드가 생성되었습니다"

    def test_summary_for_thread_closed(self):
        activity = self._make_activity(DiscussionAuditAction.THREAD_CLOSED)
        assert activity.summary == "토론 스레드가 닫혔습니다"

    def test_summary_for_thread_reopened(self):
        activity = self._make_activity(DiscussionAuditAction.THREAD_REOPENED)
        assert activity.summary == "토론 스레드가 다시 열렸습니다"

    def test_summary_for_thread_paused(self):
        activity = self._make_activity(DiscussionAuditAction.THREAD_PAUSED)
        assert activity.summary == "토론 스레드가 일시정지되었습니다"

    def test_summary_for_comment_added(self):
        activity = self._make_activity(DiscussionAuditAction.COMMENT_ADDED)
        assert activity.summary == "새 댓글이 작성되었습니다"

    def test_summary_for_comment_hidden(self):
        activity = self._make_activity(DiscussionAuditAction.COMMENT_HIDDEN)
        assert activity.summary == "댓글이 숨김 처리되었습니다"


class TestDiscussionRecentActivityFromAuditEvent:
    """from_audit_event가 감사 이벤트로부터 최근 활동을 올바르게 만드는지 확인한다."""

    def test_creates_from_audit_event(self):
        event = DiscussionAuditEvent(
            id="event-1",
            action=DiscussionAuditAction.COMMENT_HIDDEN,
            thread_id="thread-1",
            occurred_at=datetime(2026, 1, 1, 0, 0, 0),
            comment_id="comment-1",
            actor_id="moderator-1",
        )

        activity = DiscussionRecentActivity.from_audit_event(event)

        assert activity.id == event.id
        assert activity.thread_id == event.thread_id
        assert activity.action is event.action
        assert activity.occurred_at == event.occurred_at
        assert activity.comment_id == event.comment_id
        assert activity.actor_id == event.actor_id
        assert activity.summary == "댓글이 숨김 처리되었습니다"
