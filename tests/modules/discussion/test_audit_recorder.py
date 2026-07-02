"""DiscussionAuditRecorder 서비스 테스트."""
from datetime import datetime

from modules.discussion.audit_event import DiscussionAuditAction
from modules.discussion.audit_recorder import DiscussionAuditRecorder
from modules.discussion.comment import DiscussionComment
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


class TestDiscussionAuditRecorderRecordThreadCreated:
    """record_thread_created가 감사 이벤트를 남기는지 확인한다."""

    def test_records_thread_created_event(self):
        recorder = DiscussionAuditRecorder()
        thread = _thread()

        event = recorder.record_thread_created(thread, actor_id="user-1")

        assert event.action is DiscussionAuditAction.THREAD_CREATED
        assert event.thread_id == "thread-1"
        assert event.actor_id == "user-1"
        assert recorder.events() == [event]

    def test_defaults_actor_id_to_thread_created_by(self):
        recorder = DiscussionAuditRecorder()
        thread = _thread(created_by="user-2")

        event = recorder.record_thread_created(thread)

        assert event.actor_id == "user-2"

    def test_accumulates_events_across_multiple_threads(self):
        recorder = DiscussionAuditRecorder()
        thread1 = _thread(id="thread-1")
        thread2 = _thread(id="thread-2")

        event1 = recorder.record_thread_created(thread1)
        event2 = recorder.record_thread_created(thread2)

        assert recorder.events() == [event1, event2]

    def test_events_returns_copy_not_internal_list(self):
        recorder = DiscussionAuditRecorder()
        recorder.record_thread_created(_thread())

        result = recorder.events()
        result.clear()

        assert len(recorder.events()) == 1


class TestDiscussionAuditRecorderRecordCommentHidden:
    """record_comment_hidden이 감사 이벤트를 남기는지 확인한다."""

    def test_records_comment_hidden_event(self):
        recorder = DiscussionAuditRecorder()
        comment = _comment()

        event = recorder.record_comment_hidden(comment, actor_id="moderator-1")

        assert event.action is DiscussionAuditAction.COMMENT_HIDDEN
        assert event.thread_id == "thread-1"
        assert event.comment_id == "comment-1"
        assert event.actor_id == "moderator-1"
        assert recorder.events() == [event]

    def test_actor_id_is_none_when_not_provided(self):
        recorder = DiscussionAuditRecorder()
        comment = _comment()

        event = recorder.record_comment_hidden(comment)

        assert event.actor_id is None

    def test_uses_comment_thread_id(self):
        recorder = DiscussionAuditRecorder()
        comment = _comment(id="comment-2", thread_id="thread-2")

        event = recorder.record_comment_hidden(comment)

        assert event.thread_id == "thread-2"
        assert event.comment_id == "comment-2"

    def test_accumulates_events_across_multiple_comments(self):
        recorder = DiscussionAuditRecorder()
        comment1 = _comment(id="comment-1")
        comment2 = _comment(id="comment-2")

        event1 = recorder.record_comment_hidden(comment1)
        event2 = recorder.record_comment_hidden(comment2)

        assert recorder.events() == [event1, event2]
