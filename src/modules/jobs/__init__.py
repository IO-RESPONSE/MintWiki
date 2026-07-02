"""Jobs module package."""
from modules.jobs.payload import JobPayload
from modules.jobs.result import InvalidJobResultError, JobResult

# 잡 상태, 핸들러, 실행기 등 나머지 계약은 후속 태스크에서 추가되므로,
# 현재는 공통 페이로드 기반 클래스와 결과 값 객체만 export한다.
__all__ = [
    "JobPayload",
    "JobResult",
    "InvalidJobResultError",
]
