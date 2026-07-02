"""토론 감사 이벤트 도메인 모델."""
from datetime import datetime
from enum import Enum
from typing import Optional


class DiscussionAuditAction(Enum):
    """
    토론 감사 이벤트가 기록하는 변경 동작의 종류.
    """

    THREAD_CREATED = "thread_created"
    THREAD_CLOSED = "thread_closed"
    THREAD_REOPENED = "thread_reopened"
    THREAD_PAUSED = "thread_paused"
    COMMENT_ADDED = "comment_added"


class EmptyDiscussionAuditEventIdError(Exception):
    """감사 이벤트 id가 비어있을 때 발생."""

    pass


class MissingDiscussionThreadIdError(Exception):
    """감사 이벤트가 참조하는 스레드 id가 비어있을 때 발생."""

    pass


class DiscussionAuditEvent:
    """
    토론 스레드/댓글 변경 내역을 기록하는 감사 이벤트 도메인 모델.

    이벤트는 어떤 스레드(thread_id)에 어떤 동작(action)이 일어났는지를
    기록하며, 관련 댓글이 있는 경우 comment_id, 누가 변경했는지
    actor_id를 함께 담아 상위 호출자가 변경 이력을 추적할 수 있게 한다.
    이벤트를 언제 기록할지(변경 시점에 실제로 남기는 로직)와 영속화
    방법은 이 모델이 아닌 상위 서비스가 담당한다.
    """

    def __init__(
        self,
        id: str,
        action: DiscussionAuditAction,
        thread_id: str,
        occurred_at: datetime,
        comment_id: Optional[str] = None,
        actor_id: Optional[str] = None,
    ):
        """
        토론 감사 이벤트를 생성한다.

        Args:
            id: 감사 이벤트의 고유 식별자
            action: 이벤트가 기록하는 변경 동작의 종류
            thread_id: 변경이 발생한 토론 스레드의 id
            occurred_at: 변경이 발생한 시각
            comment_id: 변경과 관련된 댓글의 id (선택사항)
            actor_id: 변경을 수행한 사용자의 id (선택사항)

        Raises:
            EmptyDiscussionAuditEventIdError: 이벤트 id가 비어있거나 공백만 있는 경우
            MissingDiscussionThreadIdError: 스레드 id가 비어있거나 공백만 있는 경우
        """
        if not id or not id.strip():
            raise EmptyDiscussionAuditEventIdError("감사 이벤트 id는 비어있을 수 없습니다")
        if not thread_id or not thread_id.strip():
            raise MissingDiscussionThreadIdError("스레드 id는 비어있을 수 없습니다")

        self.id = id
        self.action = action
        self.thread_id = thread_id
        self.occurred_at = occurred_at
        self.comment_id = comment_id
        self.actor_id = actor_id

    def is_thread_created(self) -> bool:
        """이벤트가 스레드 생성을 기록하는지 확인한다."""
        return self.action is DiscussionAuditAction.THREAD_CREATED

    def is_thread_closed(self) -> bool:
        """이벤트가 스레드 닫힘을 기록하는지 확인한다."""
        return self.action is DiscussionAuditAction.THREAD_CLOSED

    def is_thread_reopened(self) -> bool:
        """이벤트가 스레드 재개를 기록하는지 확인한다."""
        return self.action is DiscussionAuditAction.THREAD_REOPENED

    def is_thread_paused(self) -> bool:
        """이벤트가 스레드 일시정지를 기록하는지 확인한다."""
        return self.action is DiscussionAuditAction.THREAD_PAUSED

    def is_comment_added(self) -> bool:
        """이벤트가 댓글 추가를 기록하는지 확인한다."""
        return self.action is DiscussionAuditAction.COMMENT_ADDED
