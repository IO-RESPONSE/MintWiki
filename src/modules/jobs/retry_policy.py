"""잡 재시도 정책 모델."""


class InvalidRetryPolicyError(Exception):
    """재시도 정책 파라미터가 유효하지 않을 때 발생."""

    pass


class RetryPolicy:
    """
    실패한 잡을 몇 번, 얼마의 간격으로 재시도할지 정의하는 값 객체.

    지수 백오프(exponential backoff) 방식으로 재시도 간격을 계산한다.
    실제로 재시도 여부를 판단해 상태를 전이시키거나 데드레터로 보내는
    로직은 후속 태스크(잡 실행기 통합, 데드레터 모델 등)에서 다루며, 이
    값 객체는 정책 파라미터 보관과 간격 계산 계약만 담당한다.
    """

    def __init__(
        self,
        max_attempts: int,
        base_delay_seconds: float,
        backoff_multiplier: float = 2.0,
    ):
        """
        재시도 정책을 생성한다.

        Args:
            max_attempts: 허용되는 최대 시도 횟수 (최초 시도 포함, 1 이상)
            base_delay_seconds: 첫 번째 재시도 전 대기 시간(초, 0 이상)
            backoff_multiplier: 재시도마다 대기 시간에 곱해지는 배수 (1 이상)

        Raises:
            InvalidRetryPolicyError: 파라미터가 유효 범위를 벗어난 경우
        """
        if max_attempts < 1:
            raise InvalidRetryPolicyError(
                "max_attempts는 1 이상이어야 합니다"
            )
        if base_delay_seconds < 0:
            raise InvalidRetryPolicyError(
                "base_delay_seconds는 0 이상이어야 합니다"
            )
        if backoff_multiplier < 1:
            raise InvalidRetryPolicyError(
                "backoff_multiplier는 1 이상이어야 합니다"
            )

        self.max_attempts = max_attempts
        self.base_delay_seconds = base_delay_seconds
        self.backoff_multiplier = backoff_multiplier

    def should_retry(self, attempt: int) -> bool:
        """
        주어진 시도 횟수 이후에도 재시도가 허용되는지 판단한다.

        Args:
            attempt: 지금까지 수행한 시도 횟수 (최초 시도는 1)

        Returns:
            attempt가 max_attempts 미만이면 True
        """
        return attempt < self.max_attempts

    def next_delay(self, attempt: int) -> float:
        """
        다음 재시도 전 대기해야 할 시간(초)을 계산한다.

        base_delay_seconds에 backoff_multiplier를 (attempt - 1)번 곱해
        지수 백오프 간격을 만든다. 예를 들어 attempt=1이면 base_delay_seconds
        그대로, attempt=2이면 backoff_multiplier배가 적용된다.

        Args:
            attempt: 지금까지 수행한 시도 횟수 (최초 시도는 1)

        Returns:
            다음 재시도 전 대기 시간(초)
        """
        return self.base_delay_seconds * (self.backoff_multiplier ** (attempt - 1))


__all__ = ["InvalidRetryPolicyError", "RetryPolicy"]
