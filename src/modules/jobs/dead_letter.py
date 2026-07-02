"""데드레터 모델."""
from modules.jobs.payload import JobPayload


class InvalidDeadLetterError(Exception):
    """데드레터 파라미터가 유효하지 않을 때 발생."""

    pass


class DeadLetter:
    """
    재시도 정책이 허용하는 시도 횟수를 모두 소진한 잡을 보관하는 값 객체.

    실패한 페이로드와 마지막 실패 사유, 시도 횟수를 그대로 담아 후속
    처리(운영자 확인, 재처리 등)에서 원인을 추적할 수 있게 한다. 실제로
    잡 실행기가 재시도 소진을 판단해 데드레터를 생성하는 로직은 후속
    태스크(재시도 소진 시 데드레터 처리)에서 다루며, 이 값 객체는 보관
    계약만 담당한다.
    """

    def __init__(self, payload: JobPayload, error: str, attempts: int):
        """
        데드레터 항목을 생성한다.

        Args:
            payload: 재시도를 모두 소진한 잡의 페이로드
            error: 마지막 시도의 실패 사유
            attempts: 데드레터로 보내지기까지 수행한 시도 횟수 (1 이상)

        Raises:
            InvalidDeadLetterError: attempts가 1 미만인 경우
        """
        if attempts < 1:
            raise InvalidDeadLetterError("attempts는 1 이상이어야 합니다")

        self.payload = payload
        self.job_type = payload.job_type
        self.error = error
        self.attempts = attempts


__all__ = ["InvalidDeadLetterError", "DeadLetter"]
