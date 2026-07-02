"""토론 최근 활동 도메인 모델."""
from datetime import datetime
from typing import Optional

from modules.discussion.audit_event import DiscussionAuditAction, DiscussionAuditEvent


class EmptyRecentActivityIdError(Exception):
    """최근 활동 id가 비어있을 때 발생."""

    pass


class MissingRecentActivityThreadIdError(Exception):
    """최근 활동이 참조하는 스레드 id가 비어있을 때 발생."""

    pass


_ACTIVITY_SUMMARIES = {
    DiscussionAuditAction.THREAD_CREATED: "새 토론 스레드가 생성되었습니다",
    DiscussionAuditAction.THREAD_CLOSED: "토론 스레드가 닫혔습니다",
    DiscussionAuditAction.THREAD_REOPENED: "토론 스레드가 다시 열렸습니다",
    DiscussionAuditAction.THREAD_PAUSED: "토론 스레드가 일시정지되었습니다",
    DiscussionAuditAction.COMMENT_ADDED: "새 댓글이 작성되었습니다",
    DiscussionAuditAction.COMMENT_HIDDEN: "댓글이 숨김 처리되었습니다",
}


class DiscussionRecentActivity:
    """
    문서/스레드에서 최근에 일어난 활동을 나타내는 읽기 전용 도메인 모델.

    감사 이벤트(DiscussionAuditEvent)를 사람이 읽기 쉬운 요약 문구와 함께
    노출하기 위한 표현 모델이다. 최근 활동을 조회/집계하는 로직은 후속
    태스크(서비스)에서 이 모델을 사용해 구현한다.
    """

    def __init__(
        self,
        id: str,
        thread_id: str,
        action: DiscussionAuditAction,
        occurred_at: datetime,
        comment_id: Optional[str] = None,
        actor_id: Optional[str] = None,
    ):
        """
        토론 최근 활동을 생성한다.

        Args:
            id: 최근 활동의 고유 식별자
            thread_id: 활동이 발생한 토론 스레드의 id
            action: 활동의 종류
            occurred_at: 활동이 발생한 시각
            comment_id: 활동과 관련된 댓글의 id (선택사항)
            actor_id: 활동을 수행한 사용자의 id (선택사항)

        Raises:
            EmptyRecentActivityIdError: 활동 id가 비어있거나 공백만 있는 경우
            MissingRecentActivityThreadIdError: 스레드 id가 비어있거나 공백만 있는 경우
        """
        if not id or not id.strip():
            raise EmptyRecentActivityIdError("최근 활동 id는 비어있을 수 없습니다")
        if not thread_id or not thread_id.strip():
            raise MissingRecentActivityThreadIdError("스레드 id는 비어있을 수 없습니다")

        self.id = id
        self.thread_id = thread_id
        self.action = action
        self.occurred_at = occurred_at
        self.comment_id = comment_id
        self.actor_id = actor_id

    @property
    def summary(self) -> str:
        """활동 종류에 대한 사람이 읽기 쉬운 요약 문구를 반환한다."""
        return _ACTIVITY_SUMMARIES[self.action]

    @classmethod
    def from_audit_event(cls, event: DiscussionAuditEvent) -> "DiscussionRecentActivity":
        """
        감사 이벤트로부터 최근 활동을 생성한다.

        Args:
            event: 변환할 감사 이벤트

        Returns:
            생성된 최근 활동
        """
        return cls(
            id=event.id,
            thread_id=event.thread_id,
            action=event.action,
            occurred_at=event.occurred_at,
            comment_id=event.comment_id,
            actor_id=event.actor_id,
        )
