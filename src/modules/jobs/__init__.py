"""Jobs module package."""
from modules.jobs.handler import JobHandler
from modules.jobs.payload import JobPayload
from modules.jobs.result import InvalidJobResultError, JobResult
from modules.jobs.retry_policy import InvalidRetryPolicyError, RetryPolicy
from modules.jobs.runner import JobRunOutcome, SyncJobRunner
from modules.jobs.status import JobStatus

# 레지스트리, 데드레터 처리 등 나머지 계약은 후속 태스크에서 추가되므로, 현재는
# 공통 페이로드 기반 클래스, 결과 값 객체, 상태 열거형, 핸들러 인터페이스,
# 동기 잡 실행기, 재시도 정책만 export한다.
__all__ = [
    "JobPayload",
    "JobResult",
    "InvalidJobResultError",
    "JobStatus",
    "JobHandler",
    "JobRunOutcome",
    "SyncJobRunner",
    "InvalidRetryPolicyError",
    "RetryPolicy",
]
