"""잡 감사 이벤트를 기록하는 서비스."""
import uuid
from datetime import datetime, timezone
from typing import List

from modules.jobs.audit_event import JobAuditAction, JobAuditEvent


class JobAuditRecorder:
    """
    잡 실행 결과를 JobAuditEvent로 기록하는 서비스.

    현재는 잡 실패 시점의 감사 이벤트만 기록하며, 성공 시점의 기록은
    이후 태스크에서 채워진다. 이벤트는 메모리에 누적되며, 영속화
    (저장소 연동)는 이후 태스크에서 다룬다.
    """

    def __init__(self):
        self._events: List[JobAuditEvent] = []

    def record_job_failed(self, job_type: str, error: str) -> JobAuditEvent:
        """
        잡 실패를 감사 이벤트로 기록한다.

        Args:
            job_type: 실패한 잡의 종류를 식별하는 문자열
            error: 실패 사유

        Returns:
            기록된 감사 이벤트
        """
        event = JobAuditEvent(
            id=str(uuid.uuid4()),
            action=JobAuditAction.JOB_FAILED,
            job_type=job_type,
            occurred_at=datetime.now(timezone.utc),
            error=error,
        )
        self._events.append(event)
        return event

    def events(self) -> List[JobAuditEvent]:
        """지금까지 기록된 감사 이벤트 목록을 시간 순서대로 반환한다."""
        return list(self._events)
