"""토론 모듈 테스트 픽스처 로더."""
from datetime import datetime
from typing import List, NamedTuple

from modules.discussion.audit_event import DiscussionAuditAction, DiscussionAuditEvent
from modules.discussion.comment import DiscussionComment
from modules.discussion.thread import DiscussionThread


class DiscussionFixture(NamedTuple):
    """
    하나의 토론 시나리오를 나타내는 픽스처.

    스레드 하나와 그에 딸린 댓글 목록, 감사 이벤트 목록을 함께 묶어
    스레드/댓글/상태/로그를 아우르는 테스트에서 재사용할 수 있게 한다.
    """

    name: str
    thread: DiscussionThread
    comments: List[DiscussionComment]
    audit_events: List[DiscussionAuditEvent]


class DiscussionFixtureLoader:
    """토론 모듈 테스트 픽스처 로더."""

    @staticmethod
    def load_all() -> List[DiscussionFixture]:
        """
        모든 토론 테스트 픽스처를 로드한다.

        Returns:
            토론 테스트 픽스처 목록
        """
        return [
            DiscussionFixtureLoader._open_thread_with_no_comments(),
            DiscussionFixtureLoader._open_thread_with_comments(),
            DiscussionFixtureLoader._closed_thread_with_comments(),
            DiscussionFixtureLoader._paused_thread_with_comments(),
            DiscussionFixtureLoader._thread_with_hidden_comment(),
            DiscussionFixtureLoader._thread_with_multiple_hidden_comments(),
        ]

    @staticmethod
    def load_by_name(name: str) -> DiscussionFixture:
        """
        이름으로 특정 토론 테스트 픽스처를 로드한다.

        Args:
            name: 픽스처 이름

        Returns:
            토론 테스트 픽스처

        Raises:
            ValueError: 해당 이름의 픽스처가 없음
        """
        fixtures = {f.name: f for f in DiscussionFixtureLoader.load_all()}
        if name not in fixtures:
            raise ValueError(f"Unknown fixture: {name}")
        return fixtures[name]

    @staticmethod
    def _open_thread_with_no_comments() -> DiscussionFixture:
        """댓글 없이 생성만 된 열린 스레드 픽스처."""
        thread = DiscussionThread(
            id="thread-open-empty",
            document_id="doc-1",
            title="Open thread with no comments",
            created_by="user-1",
            created_at=datetime(2026, 1, 1, 9, 0, 0),
        )
        return DiscussionFixture(
            name="open_thread_with_no_comments",
            thread=thread,
            comments=[],
            audit_events=[
                DiscussionAuditEvent(
                    id="audit-open-empty-1",
                    action=DiscussionAuditAction.THREAD_CREATED,
                    thread_id=thread.id,
                    occurred_at=datetime(2026, 1, 1, 9, 0, 0),
                    actor_id="user-1",
                ),
            ],
        )

    @staticmethod
    def _open_thread_with_comments() -> DiscussionFixture:
        """숨김 처리되지 않은 댓글 두 개가 달린 열린 스레드 픽스처."""
        thread = DiscussionThread(
            id="thread-open-with-comments",
            document_id="doc-1",
            title="Open thread with comments",
            created_by="user-1",
            created_at=datetime(2026, 1, 2, 9, 0, 0),
        )
        comments = [
            DiscussionComment(
                id="comment-open-1",
                thread_id=thread.id,
                body="First comment",
                created_by="user-2",
                created_at=datetime(2026, 1, 2, 9, 5, 0),
            ),
            DiscussionComment(
                id="comment-open-2",
                thread_id=thread.id,
                body="Second comment",
                created_by="user-3",
                created_at=datetime(2026, 1, 2, 9, 10, 0),
            ),
        ]
        return DiscussionFixture(
            name="open_thread_with_comments",
            thread=thread,
            comments=comments,
            audit_events=[
                DiscussionAuditEvent(
                    id="audit-open-comments-1",
                    action=DiscussionAuditAction.THREAD_CREATED,
                    thread_id=thread.id,
                    occurred_at=datetime(2026, 1, 2, 9, 0, 0),
                    actor_id="user-1",
                ),
                DiscussionAuditEvent(
                    id="audit-open-comments-2",
                    action=DiscussionAuditAction.COMMENT_ADDED,
                    thread_id=thread.id,
                    occurred_at=datetime(2026, 1, 2, 9, 5, 0),
                    comment_id="comment-open-1",
                    actor_id="user-2",
                ),
                DiscussionAuditEvent(
                    id="audit-open-comments-3",
                    action=DiscussionAuditAction.COMMENT_ADDED,
                    thread_id=thread.id,
                    occurred_at=datetime(2026, 1, 2, 9, 10, 0),
                    comment_id="comment-open-2",
                    actor_id="user-3",
                ),
            ],
        )

    @staticmethod
    def _closed_thread_with_comments() -> DiscussionFixture:
        """댓글이 달린 뒤 닫힌 스레드 픽스처."""
        thread = DiscussionThread(
            id="thread-closed",
            document_id="doc-2",
            title="Closed thread with comments",
            created_by="user-1",
            created_at=datetime(2026, 1, 3, 9, 0, 0),
            status="closed",
            closed_at=datetime(2026, 1, 3, 10, 0, 0),
        )
        comments = [
            DiscussionComment(
                id="comment-closed-1",
                thread_id=thread.id,
                body="Comment before closing",
                created_by="user-2",
                created_at=datetime(2026, 1, 3, 9, 30, 0),
            ),
        ]
        return DiscussionFixture(
            name="closed_thread_with_comments",
            thread=thread,
            comments=comments,
            audit_events=[
                DiscussionAuditEvent(
                    id="audit-closed-1",
                    action=DiscussionAuditAction.THREAD_CREATED,
                    thread_id=thread.id,
                    occurred_at=datetime(2026, 1, 3, 9, 0, 0),
                    actor_id="user-1",
                ),
                DiscussionAuditEvent(
                    id="audit-closed-2",
                    action=DiscussionAuditAction.COMMENT_ADDED,
                    thread_id=thread.id,
                    occurred_at=datetime(2026, 1, 3, 9, 30, 0),
                    comment_id="comment-closed-1",
                    actor_id="user-2",
                ),
                DiscussionAuditEvent(
                    id="audit-closed-3",
                    action=DiscussionAuditAction.THREAD_CLOSED,
                    thread_id=thread.id,
                    occurred_at=datetime(2026, 1, 3, 10, 0, 0),
                    actor_id="user-1",
                ),
            ],
        )

    @staticmethod
    def _paused_thread_with_comments() -> DiscussionFixture:
        """댓글이 달린 뒤 일시정지된 스레드 픽스처."""
        thread = DiscussionThread(
            id="thread-paused",
            document_id="doc-2",
            title="Paused thread with comments",
            created_by="user-1",
            created_at=datetime(2026, 1, 4, 9, 0, 0),
            status="paused",
            paused_at=datetime(2026, 1, 4, 10, 0, 0),
        )
        comments = [
            DiscussionComment(
                id="comment-paused-1",
                thread_id=thread.id,
                body="Comment before pausing",
                created_by="user-2",
                created_at=datetime(2026, 1, 4, 9, 30, 0),
            ),
        ]
        return DiscussionFixture(
            name="paused_thread_with_comments",
            thread=thread,
            comments=comments,
            audit_events=[
                DiscussionAuditEvent(
                    id="audit-paused-1",
                    action=DiscussionAuditAction.THREAD_CREATED,
                    thread_id=thread.id,
                    occurred_at=datetime(2026, 1, 4, 9, 0, 0),
                    actor_id="user-1",
                ),
                DiscussionAuditEvent(
                    id="audit-paused-2",
                    action=DiscussionAuditAction.COMMENT_ADDED,
                    thread_id=thread.id,
                    occurred_at=datetime(2026, 1, 4, 9, 30, 0),
                    comment_id="comment-paused-1",
                    actor_id="user-2",
                ),
                DiscussionAuditEvent(
                    id="audit-paused-3",
                    action=DiscussionAuditAction.THREAD_PAUSED,
                    thread_id=thread.id,
                    occurred_at=datetime(2026, 1, 4, 10, 0, 0),
                    actor_id="user-1",
                ),
            ],
        )

    @staticmethod
    def _thread_with_hidden_comment() -> DiscussionFixture:
        """댓글 하나가 모더레이터에 의해 숨김 처리된 스레드 픽스처."""
        thread = DiscussionThread(
            id="thread-hidden-comment",
            document_id="doc-3",
            title="Thread with a hidden comment",
            created_by="user-1",
            created_at=datetime(2026, 1, 5, 9, 0, 0),
        )
        comments = [
            DiscussionComment(
                id="comment-hidden-1",
                thread_id=thread.id,
                body="This comment was hidden",
                created_by="user-2",
                created_at=datetime(2026, 1, 5, 9, 10, 0),
                is_hidden=True,
                hidden_at=datetime(2026, 1, 5, 9, 20, 0),
            ),
        ]
        return DiscussionFixture(
            name="thread_with_hidden_comment",
            thread=thread,
            comments=comments,
            audit_events=[
                DiscussionAuditEvent(
                    id="audit-hidden-1",
                    action=DiscussionAuditAction.THREAD_CREATED,
                    thread_id=thread.id,
                    occurred_at=datetime(2026, 1, 5, 9, 0, 0),
                    actor_id="user-1",
                ),
                DiscussionAuditEvent(
                    id="audit-hidden-2",
                    action=DiscussionAuditAction.COMMENT_ADDED,
                    thread_id=thread.id,
                    occurred_at=datetime(2026, 1, 5, 9, 10, 0),
                    comment_id="comment-hidden-1",
                    actor_id="user-2",
                ),
                DiscussionAuditEvent(
                    id="audit-hidden-3",
                    action=DiscussionAuditAction.COMMENT_HIDDEN,
                    thread_id=thread.id,
                    occurred_at=datetime(2026, 1, 5, 9, 20, 0),
                    comment_id="comment-hidden-1",
                    actor_id="moderator-1",
                ),
            ],
        )

    @staticmethod
    def _thread_with_multiple_hidden_comments() -> DiscussionFixture:
        """숨겨진 댓글과 숨겨지지 않은 댓글이 섞여 있는 스레드 픽스처."""
        thread = DiscussionThread(
            id="thread-mixed-visibility",
            document_id="doc-3",
            title="Thread with mixed comment visibility",
            created_by="user-1",
            created_at=datetime(2026, 1, 6, 9, 0, 0),
        )
        comments = [
            DiscussionComment(
                id="comment-mixed-1",
                thread_id=thread.id,
                body="Visible comment",
                created_by="user-2",
                created_at=datetime(2026, 1, 6, 9, 10, 0),
            ),
            DiscussionComment(
                id="comment-mixed-2",
                thread_id=thread.id,
                body="Hidden comment one",
                created_by="user-3",
                created_at=datetime(2026, 1, 6, 9, 20, 0),
                is_hidden=True,
                hidden_at=datetime(2026, 1, 6, 9, 25, 0),
            ),
            DiscussionComment(
                id="comment-mixed-3",
                thread_id=thread.id,
                body="Hidden comment two",
                created_by="user-2",
                created_at=datetime(2026, 1, 6, 9, 30, 0),
                is_hidden=True,
                hidden_at=datetime(2026, 1, 6, 9, 35, 0),
            ),
        ]
        return DiscussionFixture(
            name="thread_with_multiple_hidden_comments",
            thread=thread,
            comments=comments,
            audit_events=[
                DiscussionAuditEvent(
                    id="audit-mixed-1",
                    action=DiscussionAuditAction.THREAD_CREATED,
                    thread_id=thread.id,
                    occurred_at=datetime(2026, 1, 6, 9, 0, 0),
                    actor_id="user-1",
                ),
                DiscussionAuditEvent(
                    id="audit-mixed-2",
                    action=DiscussionAuditAction.COMMENT_HIDDEN,
                    thread_id=thread.id,
                    occurred_at=datetime(2026, 1, 6, 9, 25, 0),
                    comment_id="comment-mixed-2",
                    actor_id="moderator-1",
                ),
                DiscussionAuditEvent(
                    id="audit-mixed-3",
                    action=DiscussionAuditAction.COMMENT_HIDDEN,
                    thread_id=thread.id,
                    occurred_at=datetime(2026, 1, 6, 9, 35, 0),
                    comment_id="comment-mixed-3",
                    actor_id="moderator-1",
                ),
            ],
        )


__all__ = ["DiscussionFixture", "DiscussionFixtureLoader"]
