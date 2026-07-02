"""DiscussionRecentActivityService 테스트."""
from datetime import datetime

from modules.discussion.audit_event import DiscussionAuditAction
from modules.discussion.audit_recorder import DiscussionAuditRecorder
from modules.discussion.comment import DiscussionComment
from modules.discussion.recent_activity_service import DiscussionRecentActivityService
from modules.discussion.thread import DiscussionThread


def _thread(id: str = "thread-1", created_by: str = "user-1") -> DiscussionThread:
    return DiscussionThread(
        id=id,
        document_id="doc-1",
        title="제목",
        created_by=created_by,
        created_at=datetime(2026, 1, 1, 0, 0, 0),
    )


def _comment(
    id: str = "comment-1", thread_id: str = "thread-1", created_by: str = "user-1"
) -> DiscussionComment:
    return DiscussionComment(
        id=id,
        thread_id=thread_id,
        body="내용",
        created_by=created_by,
        created_at=datetime(2026, 1, 1, 0, 0, 0),
    )


class TestDiscussionRecentActivityServiceListRecentActivities:
    """list_recent_activities가 감사 이벤트를 최근 활동으로 변환하는지 확인한다."""

    def test_returns_empty_list_when_no_events(self):
        recorder = DiscussionAuditRecorder()
        service = DiscussionRecentActivityService(recorder)

        assert service.list_recent_activities() == []

    def test_converts_events_to_recent_activities(self):
        recorder = DiscussionAuditRecorder()
        service = DiscussionRecentActivityService(recorder)
        thread = _thread()

        event = recorder.record_thread_created(thread, actor_id="user-1")

        result = service.list_recent_activities()

        assert len(result) == 1
        assert result[0].id == event.id
        assert result[0].thread_id == event.thread_id
        assert result[0].action is DiscussionAuditAction.THREAD_CREATED
        assert result[0].actor_id == "user-1"
        assert result[0].summary == "새 토론 스레드가 생성되었습니다"

    def test_returns_most_recent_activity_first(self):
        recorder = DiscussionAuditRecorder()
        service = DiscussionRecentActivityService(recorder)
        thread = _thread()
        comment = _comment()

        thread_event = recorder.record_thread_created(thread)
        comment_event = recorder.record_comment_hidden(comment)

        result = service.list_recent_activities()

        assert [activity.id for activity in result] == [comment_event.id, thread_event.id]

    def test_filters_by_thread_id(self):
        recorder = DiscussionAuditRecorder()
        service = DiscussionRecentActivityService(recorder)
        thread1 = _thread(id="thread-1")
        thread2 = _thread(id="thread-2")
        recorder.record_thread_created(thread1)
        event2 = recorder.record_thread_created(thread2)

        result = service.list_recent_activities(thread_id="thread-2")

        assert len(result) == 1
        assert result[0].id == event2.id
        assert result[0].thread_id == "thread-2"

    def test_returns_empty_list_when_thread_id_has_no_activity(self):
        recorder = DiscussionAuditRecorder()
        service = DiscussionRecentActivityService(recorder)
        recorder.record_thread_created(_thread())

        result = service.list_recent_activities(thread_id="nonexistent")

        assert result == []

    def test_applies_limit(self):
        recorder = DiscussionAuditRecorder()
        service = DiscussionRecentActivityService(recorder)
        recorder.record_thread_created(_thread(id="thread-1"))
        event2 = recorder.record_thread_created(_thread(id="thread-2"))

        result = service.list_recent_activities(limit=1)

        assert len(result) == 1
        assert result[0].id == event2.id

    def test_limit_beyond_total_returns_all(self):
        recorder = DiscussionAuditRecorder()
        service = DiscussionRecentActivityService(recorder)
        recorder.record_thread_created(_thread())

        result = service.list_recent_activities(limit=10)

        assert len(result) == 1
