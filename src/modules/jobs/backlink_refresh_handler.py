"""백링크 갱신 잡 핸들러 (placeholder)."""
from modules.jobs.backlink_refresh_payload import (
    BACKLINK_REFRESH_JOB_TYPE,
    BacklinkRefreshJobPayload,
)
from modules.jobs.handler import JobHandler
from modules.jobs.payload import JobPayload
from modules.jobs.result import JobResult


class BacklinkRefreshJobHandler(JobHandler):
    """
    BacklinkRefreshJobPayload를 받는 placeholder 핸들러.

    실제 백링크 색인을 재계산할 backlinks 모듈이 아직 없으므로, 이
    핸들러는 페이로드 계약(job_type, page_name)만 검증하고 성공 결과를
    돌려준다. 잡 레지스트리/실행기가 backlink.refresh 잡 타입을 미리
    배선할 수 있도록 하기 위한 자리표시자이며, 실제 백링크 갱신 로직은
    후속 태스크에서 추가된다.
    """

    @property
    def job_type(self) -> str:
        return BACKLINK_REFRESH_JOB_TYPE

    def handle(self, payload: JobPayload) -> JobResult:
        """
        백링크 갱신 페이로드를 검증만 하고 성공 결과를 반환한다.

        Args:
            payload: 실행할 BacklinkRefreshJobPayload

        Returns:
            페이로드 타입이 맞으면 page_name을 담은 성공 JobResult,
            아니면 실패 JobResult
        """
        if not isinstance(payload, BacklinkRefreshJobPayload):
            return JobResult.fail(
                "BacklinkRefreshJobHandler는 BacklinkRefreshJobPayload만 처리할 수 있습니다: "
                f"{type(payload).__name__}"
            )

        return JobResult.ok(data={"page_name": payload.page_name})


__all__ = ["BacklinkRefreshJobHandler"]
