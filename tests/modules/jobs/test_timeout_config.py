"""타임아웃 설정 모델 테스트."""
import pytest

from modules.jobs import InvalidTimeoutConfigError, TimeoutConfig


class TestTimeoutConfigConstruction:
    """유효한 파라미터로 타임아웃 설정을 생성하는 경우를 검증한다."""

    def test_stores_given_parameters(self):
        """생성자에 전달한 값을 그대로 속성에 담는다."""
        config = TimeoutConfig(timeout_seconds=30.0)

        assert config.timeout_seconds == 30.0

    def test_allows_fractional_timeout(self):
        """timeout_seconds가 소수여도 생성할 수 있다."""
        config = TimeoutConfig(timeout_seconds=0.5)

        assert config.timeout_seconds == 0.5

    def test_allows_large_timeout(self):
        """timeout_seconds가 큰 값이어도 생성할 수 있다."""
        config = TimeoutConfig(timeout_seconds=3600.0)

        assert config.timeout_seconds == 3600.0


class TestTimeoutConfigInvariants:
    """생성 파라미터에 대한 불변식을 검증한다."""

    def test_zero_timeout_raises(self):
        """timeout_seconds가 0이면 예외가 발생한다."""
        with pytest.raises(InvalidTimeoutConfigError):
            TimeoutConfig(timeout_seconds=0)

    def test_negative_timeout_raises(self):
        """timeout_seconds가 음수면 예외가 발생한다."""
        with pytest.raises(InvalidTimeoutConfigError):
            TimeoutConfig(timeout_seconds=-1.0)

    def test_very_small_positive_timeout_is_allowed(self):
        """timeout_seconds가 아주 작은 양수여도 생성이 허용된다."""
        config = TimeoutConfig(timeout_seconds=0.001)

        assert config.timeout_seconds == 0.001
