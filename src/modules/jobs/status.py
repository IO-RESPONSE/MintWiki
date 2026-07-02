"""잡 상태를 나타내는 열거형."""
from enum import Enum


class JobStatus(Enum):
    """
    잡이 생성부터 종료까지 거칠 수 있는 상태.

    재시도 정책, 데드레터 처리 등 상태 전이 규칙 자체는 후속 태스크
    (잡 실행기, 재시도 정책 모델 등)에서 다루며, 이 열거형은 잡이 가질
    수 있는 상태 값만 정의한다.
    """

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    RETRYING = "retrying"
