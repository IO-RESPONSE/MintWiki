"""잡 페이로드 기반 모델 테스트."""
import pytest

from modules.jobs import JobPayload


class TestJobPayloadIsAbstract:
    """JobPayload가 추상 기반 클래스로 동작하는지 검증한다."""

    def test_cannot_instantiate_directly(self):
        """job_type을 구현하지 않은 JobPayload는 직접 생성할 수 없다."""
        with pytest.raises(TypeError):
            JobPayload()

    def test_subclass_without_job_type_cannot_be_instantiated(self):
        """job_type을 구현하지 않은 하위 클래스도 생성할 수 없다."""

        class IncompletePayload(JobPayload):
            pass

        with pytest.raises(TypeError):
            IncompletePayload()


class TestJobPayloadSubclass:
    """job_type을 구현한 하위 클래스가 정상 동작하는지 검증한다."""

    def test_subclass_exposes_declared_job_type(self):
        """job_type을 구현한 하위 클래스는 해당 값을 그대로 노출한다."""

        class SamplePayload(JobPayload):
            @property
            def job_type(self) -> str:
                return "sample.job"

        payload = SamplePayload()

        assert payload.job_type == "sample.job"
        assert isinstance(payload, JobPayload)
