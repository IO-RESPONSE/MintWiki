"""미처리 잡 실행기 테스트."""
from collections import deque
from typing import Optional

import pytest

from modules.jobs import (
    JobAuditRecorder,
    JobHandler,
    JobPayload,
    JobRegistry,
    JobResult,
    JobRunOutcome,
    JobStatus,
    PendingJobsRunner,
)
from modules.jobs.queue_backend import QueueBackend


class SamplePayload(JobPayload):
    def __init__(self, name: str):
        self.name = name

    @property
    def job_type(self) -> str:
        return "sample.job"


class SucceedingHandler(JobHandler):
    @property
    def job_type(self) -> str:
        return "sample.job"

    def handle(self, payload: JobPayload) -> JobResult:
        return JobResult.ok(data={"handled": payload.job_type})


class FailingHandler(JobHandler):
    @property
    def job_type(self) -> str:
        return "sample.job"

    def handle(self, payload: JobPayload) -> JobResult:
        return JobResult.fail("처리 실패")


class ConcreteQueueBackend(QueueBackend):
    """테스트용 구체적인 FIFO 메모리 큐 백엔드 구현."""

    def __init__(self):
        """빈 큐를 초기화한다."""
        self._items: deque[JobPayload] = deque()

    async def enqueue(self, payload: JobPayload) -> None:
        """잡 페이로드를 큐에 적재한다."""
        self._items.append(payload)

    async def dequeue(self) -> Optional[JobPayload]:
        """큐에서 다음 잡 페이로드를 꺼낸다."""
        if not self._items:
            return None
        return self._items.popleft()

    async def size(self) -> int:
        """큐에 남아 있는 잡 페이로드 개수를 반환한다."""
        return len(self._items)


class TestPendingJobsRunnerEmptyQueue:
    """큐가 비어 있을 때의 동작을 검증한다."""

    @pytest.mark.asyncio
    async def test_run_all_on_empty_queue_returns_empty_list(self):
        """빈 큐에서 run_all()은 빈 리스트를 반환한다."""
        queue = ConcreteQueueBackend()
        registry = JobRegistry()
        registry.register(SucceedingHandler())

        runner = PendingJobsRunner(queue=queue, registry=registry)
        outcomes = await runner.run_all()

        assert isinstance(outcomes, list)
        assert len(outcomes) == 0


class TestPendingJobsRunnerSingleJob:
    """큐에 잡이 하나 있을 때의 동작을 검증한다."""

    @pytest.mark.asyncio
    async def test_run_all_with_single_successful_job(self):
        """성공하는 잡 하나를 실행하면 SUCCEEDED 결과를 반환한다."""
        queue = ConcreteQueueBackend()
        await queue.enqueue(SamplePayload("test"))

        registry = JobRegistry()
        registry.register(SucceedingHandler())

        runner = PendingJobsRunner(queue=queue, registry=registry)
        outcomes = await runner.run_all()

        assert len(outcomes) == 1
        assert isinstance(outcomes[0], JobRunOutcome)
        assert outcomes[0].status == JobStatus.SUCCEEDED
        assert outcomes[0].result.success is True

    @pytest.mark.asyncio
    async def test_run_all_with_single_failing_job(self):
        """실패하는 잡 하나를 실행하면 FAILED 결과를 반환한다."""
        queue = ConcreteQueueBackend()
        await queue.enqueue(SamplePayload("test"))

        registry = JobRegistry()
        registry.register(FailingHandler())

        runner = PendingJobsRunner(queue=queue, registry=registry)
        outcomes = await runner.run_all()

        assert len(outcomes) == 1
        assert outcomes[0].status == JobStatus.FAILED
        assert outcomes[0].result.success is False
        assert outcomes[0].result.error == "처리 실패"


class TestPendingJobsRunnerMultipleJobs:
    """큐에 여러 개의 잡이 있을 때의 동작을 검증한다."""

    @pytest.mark.asyncio
    async def test_run_all_processes_multiple_jobs_in_order(self):
        """여러 잡을 적재한 순서대로 실행한다."""
        queue = ConcreteQueueBackend()
        await queue.enqueue(SamplePayload("first"))
        await queue.enqueue(SamplePayload("second"))
        await queue.enqueue(SamplePayload("third"))

        registry = JobRegistry()
        registry.register(SucceedingHandler())

        runner = PendingJobsRunner(queue=queue, registry=registry)
        outcomes = await runner.run_all()

        assert len(outcomes) == 3
        assert all(outcome.status == JobStatus.SUCCEEDED for outcome in outcomes)

    @pytest.mark.asyncio
    async def test_run_all_continues_on_failure(self):
        """한 잡이 실패해도 다음 잡을 계속 실행한다."""
        queue = ConcreteQueueBackend()
        await queue.enqueue(SamplePayload("first"))
        await queue.enqueue(SamplePayload("second"))

        registry = JobRegistry()
        registry.register(FailingHandler())

        runner = PendingJobsRunner(queue=queue, registry=registry)
        outcomes = await runner.run_all()

        assert len(outcomes) == 2
        assert outcomes[0].status == JobStatus.FAILED
        assert outcomes[1].status == JobStatus.FAILED


class TestPendingJobsRunnerWithCustomRunner:
    """커스텀 SyncJobRunner를 사용할 때의 동작을 검증한다."""

    @pytest.mark.asyncio
    async def test_run_all_uses_provided_sync_runner(self):
        """제공된 SyncJobRunner를 사용한다."""
        queue = ConcreteQueueBackend()
        await queue.enqueue(SamplePayload("test"))

        registry = JobRegistry()
        registry.register(SucceedingHandler())

        from modules.jobs import SyncJobRunner

        custom_runner = SyncJobRunner()
        pending_runner = PendingJobsRunner(
            queue=queue, registry=registry, sync_runner=custom_runner
        )
        outcomes = await pending_runner.run_all()

        assert len(outcomes) == 1
        assert outcomes[0].status == JobStatus.SUCCEEDED

    @pytest.mark.asyncio
    async def test_run_all_with_audit_recorder(self):
        """SyncJobRunner의 감사 기록이 누적된다."""
        queue = ConcreteQueueBackend()
        await queue.enqueue(SamplePayload("test"))

        registry = JobRegistry()
        registry.register(SucceedingHandler())

        from modules.jobs import SyncJobRunner

        recorder = JobAuditRecorder()
        custom_runner = SyncJobRunner(audit_recorder=recorder)
        pending_runner = PendingJobsRunner(
            queue=queue, registry=registry, sync_runner=custom_runner
        )

        await pending_runner.run_all()

        events = recorder.events()
        assert len(events) == 1
        assert events[0].job_type == "sample.job"
