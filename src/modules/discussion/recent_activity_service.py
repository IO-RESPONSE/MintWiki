"""토론 최근 활동 조회 서비스."""
from typing import List, Optional

from modules.discussion.audit_recorder import DiscussionAuditRecorder
from modules.discussion.recent_activity import DiscussionRecentActivity


class DiscussionRecentActivityService:
    """
    감사 이벤트 기록기(DiscussionAuditRecorder)에 쌓인 이벤트를
    DiscussionRecentActivity로 변환해 조회하는 서비스.

    감사 이벤트는 발생 순서대로 누적되므로, 이 서비스는 최근 활동을
    최신순(가장 나중에 발생한 활동이 먼저)으로 뒤집어 반환한다.
    """

    def __init__(self, audit_recorder: DiscussionAuditRecorder):
        """
        서비스를 초기화한다.

        Args:
            audit_recorder: 조회 대상이 되는 감사 이벤트 기록기
        """
        self.audit_recorder = audit_recorder

    def list_recent_activities(
        self, thread_id: Optional[str] = None, limit: Optional[int] = None
    ) -> List[DiscussionRecentActivity]:
        """
        최근 활동 목록을 최신순으로 조회한다.

        Args:
            thread_id: 조회할 스레드의 id (선택사항, 생략하면 모든 스레드의
                활동을 조회한다)
            limit: 반환할 최대 개수 (선택사항, 생략하면 제한 없음)

        Returns:
            최신순으로 정렬된 최근 활동 목록 (thread_id/limit 적용됨)
        """
        events = self.audit_recorder.events()
        if thread_id is not None:
            events = [event for event in events if event.thread_id == thread_id]
        activities = [
            DiscussionRecentActivity.from_audit_event(event) for event in reversed(events)
        ]
        if limit is not None:
            activities = activities[:limit]
        return activities
