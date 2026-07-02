"""토론 감사 이벤트를 기록하는 서비스."""
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from modules.discussion.audit_event import DiscussionAuditAction, DiscussionAuditEvent
from modules.discussion.thread import DiscussionThread


class DiscussionAuditRecorder:
    """
    토론 스레드/댓글 변경을 DiscussionAuditEvent로 기록하는 서비스.

    현재는 스레드 생성 시점의 감사 이벤트만 기록하며, 다른 동작(스레드
    상태 전환, 댓글 숨김 등)에 대한 기록은 이후 태스크에서 채워진다.
    이벤트는 메모리에 누적되며, 영속화(저장소 연동)는 이후 태스크에서
    다룬다.
    """

    def __init__(self):
        self._events: List[DiscussionAuditEvent] = []

    def record_thread_created(
        self, thread: DiscussionThread, actor_id: Optional[str] = None
    ) -> DiscussionAuditEvent:
        """
        스레드 생성을 감사 이벤트로 기록한다.

        Args:
            thread: 생성된 토론 스레드
            actor_id: 스레드를 생성한 사용자의 id (선택사항, 생략하면
                스레드의 created_by를 사용)

        Returns:
            기록된 감사 이벤트
        """
        event = DiscussionAuditEvent(
            id=str(uuid.uuid4()),
            action=DiscussionAuditAction.THREAD_CREATED,
            thread_id=thread.id,
            occurred_at=datetime.now(timezone.utc),
            actor_id=actor_id if actor_id is not None else thread.created_by,
        )
        self._events.append(event)
        return event

    def events(self) -> List[DiscussionAuditEvent]:
        """지금까지 기록된 감사 이벤트 목록을 시간 순서대로 반환한다."""
        return list(self._events)
