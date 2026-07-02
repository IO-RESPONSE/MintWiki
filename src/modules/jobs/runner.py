"""동기 잡 실행기."""
from typing import NamedTuple

from modules.jobs.handler import JobHandler
from modules.jobs.payload import JobPayload
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
    나머지 계약은 후속 태스크(재시도 정책, 잡 레지스트리 등)에서 다룬다.
    """

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
        return JobRunOutcome(status=status, result=result)


__all__ = ["JobRunOutcome", "SyncJobRunner"]
