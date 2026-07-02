"""잡 재시도 정책 모델 테스트."""
import pytest

from modules.jobs import InvalidRetryPolicyError, RetryPolicy


class TestRetryPolicyConstruction:
    """유효한 파라미터로 재시도 정책을 생성하는 경우를 검증한다."""

    def test_stores_given_parameters(self):
        """생성자에 전달한 값을 그대로 속성에 담는다."""
        policy = RetryPolicy(
            max_attempts=3, base_delay_seconds=1.0, backoff_multiplier=2.0
        )

        assert policy.max_attempts == 3
        assert policy.base_delay_seconds == 1.0
        assert policy.backoff_multiplier == 2.0

    def test_backoff_multiplier_defaults_to_two(self):
        """backoff_multiplier를 생략하면 기본값 2.0이 적용된다."""
        policy = RetryPolicy(max_attempts=3, base_delay_seconds=1.0)

        assert policy.backoff_multiplier == 2.0

    def test_allows_zero_base_delay(self):
        """base_delay_seconds가 0이어도 생성할 수 있다."""
        policy = RetryPolicy(max_attempts=1, base_delay_seconds=0)

        assert policy.base_delay_seconds == 0

    def test_allows_backoff_multiplier_of_one(self):
        """backoff_multiplier가 1이면 매번 동일한 간격을 의미하며 생성이 허용된다."""
        policy = RetryPolicy(
            max_attempts=2, base_delay_seconds=1.0, backoff_multiplier=1.0
        )

        assert policy.backoff_multiplier == 1.0


class TestRetryPolicyInvariants:
    """생성 파라미터에 대한 불변식을 검증한다."""

    def test_max_attempts_below_one_raises(self):
        """max_attempts가 1 미만이면 예외가 발생한다."""
        with pytest.raises(InvalidRetryPolicyError):
            RetryPolicy(max_attempts=0, base_delay_seconds=1.0)

    def test_negative_base_delay_raises(self):
        """base_delay_seconds가 음수면 예외가 발생한다."""
        with pytest.raises(InvalidRetryPolicyError):
            RetryPolicy(max_attempts=3, base_delay_seconds=-1.0)

    def test_backoff_multiplier_below_one_raises(self):
        """backoff_multiplier가 1 미만이면 예외가 발생한다."""
        with pytest.raises(InvalidRetryPolicyError):
            RetryPolicy(
                max_attempts=3, base_delay_seconds=1.0, backoff_multiplier=0.5
            )


class TestRetryPolicyShouldRetry:
    """should_retry()가 시도 횟수에 따라 재시도 가능 여부를 판단하는지 검증한다."""

    def test_returns_true_when_attempts_remain(self):
        """시도 횟수가 max_attempts 미만이면 재시도가 허용된다."""
        policy = RetryPolicy(max_attempts=3, base_delay_seconds=1.0)

        assert policy.should_retry(1) is True
        assert policy.should_retry(2) is True

    def test_returns_false_when_max_attempts_reached(self):
        """시도 횟수가 max_attempts에 도달하면 더 이상 재시도하지 않는다."""
        policy = RetryPolicy(max_attempts=3, base_delay_seconds=1.0)

        assert policy.should_retry(3) is False


class TestRetryPolicyNextDelay:
    """next_delay()의 지수 백오프 계산 결과를 검증한다."""

    def test_first_attempt_uses_base_delay(self):
        """첫 번째 시도(attempt=1) 이후에는 base_delay_seconds 그대로 반환한다."""
        policy = RetryPolicy(
            max_attempts=5, base_delay_seconds=2.0, backoff_multiplier=2.0
        )

        assert policy.next_delay(1) == 2.0

    def test_delay_grows_with_backoff_multiplier(self):
        """시도 횟수가 늘어날수록 backoff_multiplier만큼 간격이 커진다."""
        policy = RetryPolicy(
            max_attempts=5, base_delay_seconds=2.0, backoff_multiplier=2.0
        )

        assert policy.next_delay(2) == 4.0
        assert policy.next_delay(3) == 8.0

    def test_constant_delay_when_backoff_multiplier_is_one(self):
        """backoff_multiplier가 1이면 시도 횟수와 무관하게 간격이 일정하다."""
        policy = RetryPolicy(
            max_attempts=5, base_delay_seconds=3.0, backoff_multiplier=1.0
        )

        assert policy.next_delay(1) == 3.0
        assert policy.next_delay(2) == 3.0
        assert policy.next_delay(4) == 3.0

    def test_zero_base_delay_stays_zero_regardless_of_attempt(self):
        """base_delay_seconds가 0이면 시도 횟수와 무관하게 0을 반환한다."""
        policy = RetryPolicy(
            max_attempts=5, base_delay_seconds=0, backoff_multiplier=2.0
        )

        assert policy.next_delay(1) == 0
        assert policy.next_delay(3) == 0

    def test_delay_with_fractional_backoff_multiplier(self):
        """backoff_multiplier가 정수가 아니어도 지수 계산이 정확히 적용된다."""
        policy = RetryPolicy(
            max_attempts=5, base_delay_seconds=4.0, backoff_multiplier=1.5
        )

        assert policy.next_delay(1) == 4.0
        assert policy.next_delay(2) == 6.0
        assert policy.next_delay(3) == 9.0

    def test_delay_at_final_allowed_attempt(self):
        """max_attempts에 도달한 시도에 대해서도 간격 계산이 계속 동작한다."""
        policy = RetryPolicy(
            max_attempts=4, base_delay_seconds=1.0, backoff_multiplier=2.0
        )

        assert policy.next_delay(4) == 8.0
