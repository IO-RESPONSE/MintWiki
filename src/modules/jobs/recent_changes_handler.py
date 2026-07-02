"""최근 변경 내역 잡 핸들러 (placeholder)."""
from modules.jobs.handler import JobHandler
from modules.jobs.payload import JobPayload
from modules.jobs.recent_changes_payload import (
    RECENT_CHANGES_JOB_TYPE,
    RecentChangesJobPayload,
)
from modules.jobs.result import JobResult


class RecentChangesJobHandler(JobHandler):
    """
    RecentChangesJobPayload를 받는 placeholder 핸들러.

    실제로 최근 변경 내역 목록에 기록을 남길 recent changes 모듈이 아직
    없으므로, 이 핸들러는 페이로드 계약(job_type, page_name, author_id,
    occurred_at, summary)만 검증하고 성공 결과를 돌려준다. 잡 레지스트리/
    실행기가 recent_changes.record 잡 타입을 미리 배선할 수 있도록 하기
    위한 자리표시자이며, 실제 최근 변경 내역 기록 로직은 후속 태스크에서
    추가된다.
    """

    @property
    def job_type(self) -> str:
        return RECENT_CHANGES_JOB_TYPE

    def handle(self, payload: JobPayload) -> JobResult:
        """
        최근 변경 내역 페이로드를 검증만 하고 성공 결과를 반환한다.

        Args:
            payload: 실행할 RecentChangesJobPayload

        Returns:
            페이로드 타입이 맞으면 page_name, author_id, occurred_at,
            summary를 담은 성공 JobResult, 아니면 실패 JobResult
        """
        if not isinstance(payload, RecentChangesJobPayload):
            return JobResult.fail(
                "RecentChangesJobHandler는 RecentChangesJobPayload만 처리할 수 있습니다: "
                f"{type(payload).__name__}"
            )

        return JobResult.ok(
            data={
                "page_name": payload.page_name,
                "author_id": payload.author_id,
                "occurred_at": payload.occurred_at,
                "summary": payload.summary,
            }
        )


__all__ = ["RecentChangesJobHandler"]
