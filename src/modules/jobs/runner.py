"""동기 잡 실행기."""
from typing import List, NamedTuple, Optional

from modules.jobs.audit_recorder import JobAuditRecorder
from modules.jobs.handler import JobHandler
from modules.jobs.payload import JobPayload
from modules.jobs.queue_backend import QueueBackend
from modules.jobs.registry import JobRegistry
from modules.jobs.result import JobResult
from modules.jobs.status import JobStatus


class JobRunOutcome(NamedTuple):
    """SyncJobRunner가 잡 하나를 실행한 뒤 반환하는 상태와 결과의 묶음."""

    status: JobStatus
    result: JobResult


class SyncJobRunner:
    """
    핸들러를 호출한 스레드에서 즉시(동기적으로) 잡을 한 번 실행하는 실행기.

    큐 적재, 재시도 정책, 레지스트리를 통한 핸들러 조회는 다루지 않으며,
    호출자가 이미 알고 있는 핸들러와 페이로드 쌍을 한 번 실행해 상태
    전이(RUNNING -> SUCCEEDED/FAILED)를 계산하는 최소 계약만 담당한다.
    잡이 성공하든 실패하든 audit_recorder를 통해 감사 이벤트를 함께
    남긴다. 재시도 정책, 잡 레지스트리 등 나머지 계약은 후속 태스크에서
    다룬다.
    """

    def __init__(self, audit_recorder: Optional[JobAuditRecorder] = None):
        """
        실행기를 초기화한다.

        Args:
            audit_recorder: 감사 이벤트 기록기 (선택사항, 생략하면 새로
                생성한다)
        """
        self.audit_recorder = audit_recorder or JobAuditRecorder()

    def run(self, handler: JobHandler, payload: JobPayload) -> JobRunOutcome:
        """
        핸들러로 페이로드를 한 번 실행하고 상태 전이 결과를 반환한다.

        핸들러가 예외를 던지면 이를 잡아 실패한 JobResult로 변환하므로,
        run()은 예외를 밖으로 전파하지 않는다.

        Args:
            handler: 실행에 사용할 잡 핸들러
            payload: 실행할 잡의 페이로드

        Returns:
            최종 상태(SUCCEEDED 또는 FAILED)와 결과를 담은 JobRunOutcome
        """
        try:
            result = handler.handle(payload)
        except Exception as exc:  # noqa: BLE001 - 핸들러 예외를 실패 결과로 변환
            result = JobResult.fail(str(exc))

        status = JobStatus.SUCCEEDED if result.success else JobStatus.FAILED
        if status is JobStatus.SUCCEEDED:
            self.audit_recorder.record_job_succeeded(job_type=payload.job_type)
        else:
            self.audit_recorder.record_job_failed(
                job_type=payload.job_type, error=result.error
            )
        return JobRunOutcome(status=status, result=result)


class PendingJobsRunner:
    """
    큐에 적재된 미처리 잡들을 모두 처리하는 비동기 실행기.

    QueueBackend에서 잡을 하나씩 꺼내 JobRegistry에서 핸들러를 조회한 뒤,
    SyncJobRunner를 사용해 각 잡을 실행한다. 큐가 빌 때까지 반복하며,
    모든 실행 결과를 누적해 반환한다.
    """

    def __init__(
        self,
        queue: QueueBackend,
        registry: JobRegistry,
        sync_runner: Optional[SyncJobRunner] = None,
    ):
        """
        미처리 잡 실행기를 초기화한다.

        Args:
            queue: 잡을 가져올 큐 백엔드
            registry: job_type에서 핸들러를 조회할 레지스트리
            sync_runner: 각 잡을 실행할 동기 실행기 (선택사항, 생략하면 새로
                생성한다)
        """
        self.queue = queue
        self.registry = registry
        self.sync_runner = sync_runner or SyncJobRunner()

    async def run_all(self) -> List[JobRunOutcome]:
        """
        큐에 남아 있는 모든 잡을 처리하고 실행 결과 목록을 반환한다.

        각 잡에 대해:
        1. 큐에서 페이로드를 꺼낸다
        2. registry에서 job_type에 해당하는 핸들러를 조회한다
        3. sync_runner로 잡을 실행한다
        4. 결과를 누적한다

        큐가 비면 반복을 종료하고 누적된 결과 목록을 반환한다.

        Returns:
            큐의 모든 잡에 대한 JobRunOutcome 목록 (실행 순서대로)
        """
        outcomes: List[JobRunOutcome] = []

        while True:
            payload = await self.queue.dequeue()
            if payload is None:
                break

            handler = self.registry.get(payload.job_type)
            outcome = self.sync_runner.run(handler, payload)
            outcomes.append(outcome)

        return outcomes


__all__ = ["JobRunOutcome", "SyncJobRunner", "PendingJobsRunner"]
