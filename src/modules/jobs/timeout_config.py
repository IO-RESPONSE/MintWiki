"""잡 타임아웃 설정 모델."""


class InvalidTimeoutConfigError(Exception):
    """타임아웃 설정 파라미터가 유효하지 않을 때 발생."""

    pass


class TimeoutConfig:
    """
    잡 실행의 최대 허용 시간을 정의하는 값 객체.

    타임아웃 설정을 저장하고 유효성을 검사한다. 실제로 타임아웃을 적용하는
    로직(시간 경과 모니터링, 강제 종료 등)은 후속 태스크에서 다루며, 이
    값 객체는 타임아웃 파라미터 보관과 유효성 검사만 담당한다.
    """

    def __init__(self, timeout_seconds: float):
        """
        타임아웃 설정을 생성한다.

        Args:
            timeout_seconds: 최대 허용 실행 시간(초, 0 초과)

        Raises:
            InvalidTimeoutConfigError: timeout_seconds가 0 이하인 경우
        """
        if timeout_seconds <= 0:
            raise InvalidTimeoutConfigError(
                "timeout_seconds는 0을 초과해야 합니다"
            )

        self.timeout_seconds = timeout_seconds


__all__ = ["InvalidTimeoutConfigError", "TimeoutConfig"]
