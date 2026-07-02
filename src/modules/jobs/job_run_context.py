"""잡 실행 컨텍스트 모델."""
from datetime import datetime
from typing import Optional

from modules.jobs.payload import JobPayload
from modules.jobs.result import JobResult
from modules.jobs.status import JobStatus


class InvalidJobRunContextError(Exception):
    """잡 실행 컨텍스트 파라미터가 유효하지 않을 때 발생."""

    pass


class JobRunContext:
    """
    잡의 한 번의 실행 동안 유지되는 런타임 컨텍스트.

    잡 ID, 페이로드, 현재 상태, 시작/종료 시각, 실행 결과 등을 담아
    잡 실행 전체 생명주기의 상태를 추적할 수 있게 한다. SyncJobRunner와
    큐 기반 실행기는 이 컨텍스트를 관리하며, 핸들러는 페이로드만 받아
    처리하고 잡 상태 관리는 실행기가 담당한다.
    """

    def __init__(
        self,
        job_id: str,
        payload: JobPayload,
        status: JobStatus,
        started_at: datetime,
        completed_at: Optional[datetime] = None,
        result: Optional[JobResult] = None,
    ):
        """
        잡 실행 컨텍스트를 생성한다.

        Args:
            job_id: 이 실행의 고유한 식별자
            payload: 잡의 입력 데이터
            status: 현재 잡의 상태
            started_at: 실행이 시작된 시각 (UTC)
            completed_at: 실행이 종료된 시각 (UTC, 선택사항)
            result: 실행 결과 (선택사항, 종료된 상태일 때만 있음)

        Raises:
            InvalidJobRunContextError: job_id가 비어있거나, completed_at이
                started_at보다 이전이거나, status가 종료 상태인데 result가
                없는 경우, 또는 status가 미완료 상태인데 result가 있는 경우
        """
        if not job_id or not job_id.strip():
            raise InvalidJobRunContextError("job_id는 비어있을 수 없습니다")

        if completed_at is not None and completed_at < started_at:
            raise InvalidJobRunContextError(
                "completed_at은 started_at보다 이전일 수 없습니다"
            )

        is_terminal = status in (JobStatus.SUCCEEDED, JobStatus.FAILED)
        if is_terminal and result is None:
            raise InvalidJobRunContextError(
                "종료 상태(SUCCEEDED, FAILED)에는 result가 반드시 있어야 합니다"
            )

        if not is_terminal and result is not None:
            raise InvalidJobRunContextError(
                "미완료 상태(PENDING, RUNNING, RETRYING)에는 result를 가질 수 없습니다"
            )

        self.job_id = job_id
        self.payload = payload
        self.job_type = payload.job_type
        self.status = status
        self.started_at = started_at
        self.completed_at = completed_at
        self.result = result

    def is_pending(self) -> bool:
        """실행이 대기 중인지 확인한다."""
        return self.status is JobStatus.PENDING

    def is_running(self) -> bool:
        """실행이 진행 중인지 확인한다."""
        return self.status is JobStatus.RUNNING

    def is_retrying(self) -> bool:
        """실행을 재시도 중인지 확인한다."""
        return self.status is JobStatus.RETRYING

    def is_succeeded(self) -> bool:
        """실행이 성공으로 종료되었는지 확인한다."""
        return self.status is JobStatus.SUCCEEDED

    def is_failed(self) -> bool:
        """실행이 실패로 종료되었는지 확인한다."""
        return self.status is JobStatus.FAILED

    def is_terminal(self) -> bool:
        """실행이 종료 상태(성공 또는 실패)인지 확인한다."""
        return self.status in (JobStatus.SUCCEEDED, JobStatus.FAILED)

    def is_active(self) -> bool:
        """실행이 활성 상태(PENDING, RUNNING, RETRYING)인지 확인한다."""
        return not self.is_terminal()


__all__ = ["InvalidJobRunContextError", "JobRunContext"]
