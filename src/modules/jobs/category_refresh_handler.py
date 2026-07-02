"""카테고리 갱신 잡 핸들러 (placeholder)."""
from modules.jobs.category_refresh_payload import (
    CATEGORY_REFRESH_JOB_TYPE,
    CategoryRefreshJobPayload,
)
from modules.jobs.handler import JobHandler
from modules.jobs.payload import JobPayload
from modules.jobs.result import JobResult


class CategoryRefreshJobHandler(JobHandler):
    """
    CategoryRefreshJobPayload를 받는 placeholder 핸들러.

    실제 카테고리 색인을 재계산할 categories 모듈이 아직 없으므로, 이
    핸들러는 페이로드 계약(job_type, category_name)만 검증하고 성공
    결과를 돌려준다. 잡 레지스트리/실행기가 category.refresh 잡 타입을
    미리 배선할 수 있도록 하기 위한 자리표시자이며, 실제 카테고리 갱신
    로직은 후속 태스크에서 추가된다.
    """

    @property
    def job_type(self) -> str:
        return CATEGORY_REFRESH_JOB_TYPE

    def handle(self, payload: JobPayload) -> JobResult:
        """
        카테고리 갱신 페이로드를 검증만 하고 성공 결과를 반환한다.

        Args:
            payload: 실행할 CategoryRefreshJobPayload

        Returns:
            페이로드 타입이 맞으면 category_name을 담은 성공 JobResult,
            아니면 실패 JobResult
        """
        if not isinstance(payload, CategoryRefreshJobPayload):
            return JobResult.fail(
                "CategoryRefreshJobHandler는 CategoryRefreshJobPayload만 처리할 수 있습니다: "
                f"{type(payload).__name__}"
            )

        return JobResult.ok(data={"category_name": payload.category_name})


__all__ = ["CategoryRefreshJobHandler"]
