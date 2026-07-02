"""잡 레지스트리."""
from typing import Dict

from modules.jobs.handler import JobHandler


class DuplicateJobTypeError(Exception):
    """이미 등록된 job_type으로 다시 등록을 시도할 때 발생."""

    pass


class UnknownJobTypeError(Exception):
    """등록되지 않은 job_type을 조회할 때 발생."""

    pass


class JobRegistry:
    """
    job_type 문자열과 이를 처리할 JobHandler를 매핑해 보관하는 레지스트리.

    잡 실행기가 페이로드의 job_type만으로 알맞은 핸들러를 찾아 실행할 수
    있도록 등록과 조회 계약을 제공한다. 큐 적재, 실행 자체(SyncJobRunner),
    재시도 판단은 다루지 않으며, 이 클래스는 핸들러 등록/조회만 담당한다.
    """

    def __init__(self):
        """빈 레지스트리를 생성한다."""
        self._handlers: Dict[str, JobHandler] = {}

    def register(self, handler: JobHandler) -> None:
        """
        핸들러를 그 job_type으로 등록한다.

        Args:
            handler: 등록할 잡 핸들러

        Raises:
            DuplicateJobTypeError: 동일한 job_type이 이미 등록된 경우
        """
        job_type = handler.job_type
        if job_type in self._handlers:
            raise DuplicateJobTypeError(
                f"이미 등록된 job_type입니다: {job_type}"
            )
        self._handlers[job_type] = handler

    def get(self, job_type: str) -> JobHandler:
        """
        job_type에 해당하는 핸들러를 조회한다.

        Args:
            job_type: 조회할 잡의 종류

        Returns:
            등록된 JobHandler

        Raises:
            UnknownJobTypeError: 등록되지 않은 job_type인 경우
        """
        try:
            return self._handlers[job_type]
        except KeyError:
            raise UnknownJobTypeError(
                f"등록되지 않은 job_type입니다: {job_type}"
            ) from None

    def is_registered(self, job_type: str) -> bool:
        """job_type이 등록되어 있는지 여부를 반환한다."""
        return job_type in self._handlers


__all__ = ["DuplicateJobTypeError", "UnknownJobTypeError", "JobRegistry"]
