"""데드레터 모델 테스트."""
import pytest

from modules.jobs import DeadLetter, InvalidDeadLetterError, JobPayload


class SamplePayload(JobPayload):
    @property
    def job_type(self) -> str:
        return "sample.job"


class TestDeadLetterConstruction:
    """유효한 파라미터로 데드레터를 생성하는 경우를 검증한다."""

    def test_stores_given_parameters(self):
        """생성자에 전달한 값을 그대로 속성에 담는다."""
        payload = SamplePayload()
        dead_letter = DeadLetter(payload=payload, error="처리 실패", attempts=3)

        assert dead_letter.payload is payload
        assert dead_letter.error == "처리 실패"
        assert dead_letter.attempts == 3

    def test_job_type_is_derived_from_payload(self):
        """job_type은 페이로드의 job_type을 그대로 사용한다."""
        dead_letter = DeadLetter(
            payload=SamplePayload(), error="처리 실패", attempts=1
        )

        assert dead_letter.job_type == "sample.job"

    def test_allows_attempts_of_one(self):
        """attempts가 1이어도 생성할 수 있다."""
        dead_letter = DeadLetter(payload=SamplePayload(), error="실패", attempts=1)

        assert dead_letter.attempts == 1


class TestDeadLetterInvariants:
    """생성 파라미터에 대한 불변식을 검증한다."""

    def test_attempts_below_one_raises(self):
        """attempts가 1 미만이면 예외가 발생한다."""
        with pytest.raises(InvalidDeadLetterError):
            DeadLetter(payload=SamplePayload(), error="실패", attempts=0)
