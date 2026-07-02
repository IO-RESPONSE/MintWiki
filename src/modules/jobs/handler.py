"""잡 핸들러 인터페이스."""
from abc import ABC, abstractmethod

from modules.jobs.payload import JobPayload
from modules.jobs.result import JobResult


class JobHandler(ABC):
    """
    모든 잡 핸들러가 상속해야 하는 기반 클래스.

    잡 레지스트리는 job_type 값으로 이 핸들러들을 찾아 handle()을 호출한다.
    실제 실행 로직과 재시도 판단은 각 하위 클래스(예: 검색 색인 핸들러)와
    잡 실행기(후속 태스크)에서 다루며, 이 기반 클래스는 job_type과 handle()
    계약만 강제한다.
    """

    @property
    @abstractmethod
    def job_type(self) -> str:
        """이 핸들러가 처리할 수 있는 잡의 종류를 식별하는 문자열."""
        raise NotImplementedError

    @abstractmethod
    def handle(self, payload: JobPayload) -> JobResult:
        """
        주어진 페이로드를 한 번 실행하고 결과를 반환한다.

        Args:
            payload: 실행할 잡의 페이로드

        Returns:
            실행 결과를 담은 JobResult
        """
        raise NotImplementedError
