"""색인 작업 조율 서비스."""
from modules.jobs.payload import JobPayload
from modules.jobs.registry import JobRegistry
from modules.jobs.result import JobResult
from modules.jobs.runner import SyncJobRunner


class IndexingOrchestrationService:
    """
    색인 관련 작업들을 조율하고 실행하는 서비스.

    검색 색인, 백링크 갱신, 카테고리 갱신 등 다양한 색인 작업을 JobRegistry를
    통해 발견하고 조율한다. 각 색인 작업 페이로드는 대응하는 핸들러로 라우팅되어
    SyncJobRunner를 통해 실행된다.
    """

    def __init__(self, registry: JobRegistry, runner: SyncJobRunner):
        """
        색인 조율 서비스를 초기화한다.

        Args:
            registry: 색인 작업 핸들러를 조회할 잡 레지스트리
            runner: 색인 작업을 실행할 동기 잡 실행기
        """
        self._registry = registry
        self._runner = runner

    def execute_indexing_job(self, payload: JobPayload) -> JobResult:
        """
        주어진 색인 작업 페이로드를 실행한다.

        페이로드의 job_type에 해당하는 핸들러를 레지스트리에서 찾아 실행한다.

        Args:
            payload: 실행할 색인 작업 페이로드

        Returns:
            작업 실행 결과를 담은 JobResult
        """
        handler = self._registry.get(payload.job_type)
        outcome = self._runner.run(handler, payload)
        return outcome.result


__all__ = ["IndexingOrchestrationService"]
