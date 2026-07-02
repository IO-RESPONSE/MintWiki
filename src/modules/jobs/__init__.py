"""Jobs module package."""
from modules.jobs.cache_purge_handler import CachePurgeJobHandler
from modules.jobs.cache_purge_payload import (
    CACHE_PURGE_JOB_TYPE,
    CachePurgeJobPayload,
    InvalidCachePurgeJobPayloadError,
)
from modules.jobs.dead_letter import DeadLetter, InvalidDeadLetterError
from modules.jobs.handler import JobHandler
from modules.jobs.payload import JobPayload
from modules.jobs.registry import (
    DuplicateJobTypeError,
    JobRegistry,
    UnknownJobTypeError,
)
from modules.jobs.result import InvalidJobResultError, JobResult
from modules.jobs.retry_policy import InvalidRetryPolicyError, RetryPolicy
from modules.jobs.runner import JobRunOutcome, SyncJobRunner
from modules.jobs.search_index_handler import SEARCH_INDEX_JOB_TYPE, SearchIndexJobHandler
from modules.jobs.status import JobStatus

# 큐 적재 등 나머지 계약은 후속 태스크에서 추가되므로, 현재는 공통
# 페이로드 기반 클래스, 결과 값 객체, 상태 열거형, 핸들러 인터페이스,
# 동기 잡 실행기, 재시도 정책, 데드레터 모델, 잡 레지스트리, 캐시 퍼지
# 페이로드/핸들러, 검색 색인 핸들러만 export한다.
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
    "InvalidDeadLetterError",
    "DeadLetter",
    "JobRegistry",
    "DuplicateJobTypeError",
    "UnknownJobTypeError",
    "CACHE_PURGE_JOB_TYPE",
    "CachePurgeJobPayload",
    "InvalidCachePurgeJobPayloadError",
    "CachePurgeJobHandler",
    "SEARCH_INDEX_JOB_TYPE",
    "SearchIndexJobHandler",
]
