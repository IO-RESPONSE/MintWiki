"""잡 페이로드 기반 모델."""
from abc import ABC, abstractmethod


class JobPayload(ABC):
    """
    모든 잡 페이로드가 상속해야 하는 기반 클래스.

    잡 레지스트리와 실행기는 job_type 값으로 페이로드에 맞는 핸들러를
    찾아 실행한다. 구체적인 필드와 유효성 검증은 각 하위 클래스(예:
    검색 색인 페이로드)에서 정의하며, 이 기반 클래스는 job_type 계약만
    강제한다.
    """

    @property
    @abstractmethod
    def job_type(self) -> str:
        """이 페이로드가 속한 잡의 종류를 식별하는 문자열."""
        raise NotImplementedError
