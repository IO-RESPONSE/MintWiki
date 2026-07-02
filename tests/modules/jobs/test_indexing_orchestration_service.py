"""색인 조율 서비스 테스트."""
from modules.jobs.indexing_orchestration_service import IndexingOrchestrationService
from modules.jobs.registry import JobRegistry
from modules.jobs.result import JobResult
from modules.jobs.runner import SyncJobRunner
from modules.jobs import (
    CachePurgeJobHandler,
    CachePurgeJobPayload,
    JobHandler,
    JobPayload,
)
from modules.cache import InMemoryCacheBackend


class TestIndexingOrchestrationServiceJobType:
    """색인 조율 서비스의 기본 속성 테스트."""

    def test_initializes_with_registry_and_runner(self):
        """색인 조율 서비스는 레지스트리와 실행기로 초기화된다."""
        registry = JobRegistry()
        runner = SyncJobRunner()
        service = IndexingOrchestrationService(registry, runner)

        assert service is not None


class TestIndexingOrchestrationServiceExecutesJobs:
    """색인 조율 서비스가 색인 작업을 올바르게 실행하는지 확인."""

    def test_execute_indexing_job_delegates_to_handler(self):
        """실행할 색인 작업 페이로드를 핸들러에 위임하고 결과를 반환한다."""
        backend = InMemoryCacheBackend()
        handler = CachePurgeJobHandler(backend)
        payload = CachePurgeJobPayload(source="test.md", parser_version="1.0.0")

        registry = JobRegistry()
        registry.register(handler)

        runner = SyncJobRunner()
        service = IndexingOrchestrationService(registry, runner)

        result = service.execute_indexing_job(payload)

        assert isinstance(result, JobResult)
        assert result.success is True

    def test_execute_indexing_job_returns_handler_result(self):
        """핸들러가 반환한 결과를 그대로 전달한다."""
        backend = InMemoryCacheBackend()
        handler = CachePurgeJobHandler(backend)
        payload = CachePurgeJobPayload(source="test.md", parser_version="1.0.0")

        registry = JobRegistry()
        registry.register(handler)

        runner = SyncJobRunner()
        service = IndexingOrchestrationService(registry, runner)

        result = service.execute_indexing_job(payload)

        assert result.success is True
        assert result.data is not None
        assert result.data["source"] == "test.md"
        assert result.data["parser_version"] == "1.0.0"


__all__ = ["TestIndexingOrchestrationServiceJobType", "TestIndexingOrchestrationServiceExecutesJobs"]
