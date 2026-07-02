"""잡 레지스트리 테스트."""
import pytest

from modules.jobs import (
    DuplicateJobTypeError,
    JobHandler,
    JobPayload,
    JobRegistry,
    JobResult,
    UnknownJobTypeError,
)


class SamplePayload(JobPayload):
    @property
    def job_type(self) -> str:
        return "sample.job"


class SampleHandler(JobHandler):
    @property
    def job_type(self) -> str:
        return "sample.job"

    def handle(self, payload: JobPayload) -> JobResult:
        return JobResult.ok(data={"handled": payload.job_type})


class OtherHandler(JobHandler):
    @property
    def job_type(self) -> str:
        return "other.job"

    def handle(self, payload: JobPayload) -> JobResult:
        return JobResult.ok()


class TestJobRegistryRegister:
    """핸들러 등록 동작을 검증한다."""

    def test_register_makes_handler_retrievable(self):
        """등록한 핸들러는 같은 job_type으로 조회할 수 있다."""
        registry = JobRegistry()
        handler = SampleHandler()

        registry.register(handler)

        assert registry.get("sample.job") is handler

    def test_register_multiple_distinct_job_types(self):
        """서로 다른 job_type의 핸들러는 모두 등록할 수 있다."""
        registry = JobRegistry()
        sample_handler = SampleHandler()
        other_handler = OtherHandler()

        registry.register(sample_handler)
        registry.register(other_handler)

        assert registry.get("sample.job") is sample_handler
        assert registry.get("other.job") is other_handler

    def test_register_duplicate_job_type_raises(self):
        """이미 등록된 job_type을 다시 등록하면 예외가 발생한다."""
        registry = JobRegistry()
        registry.register(SampleHandler())

        with pytest.raises(DuplicateJobTypeError):
            registry.register(SampleHandler())


class TestJobRegistryGet:
    """핸들러 조회 동작을 검증한다."""

    def test_get_unknown_job_type_raises(self):
        """등록되지 않은 job_type을 조회하면 예외가 발생한다."""
        registry = JobRegistry()

        with pytest.raises(UnknownJobTypeError):
            registry.get("unknown.job")


class TestJobRegistryIsRegistered:
    """등록 여부 조회 동작을 검증한다."""

    def test_is_registered_true_after_register(self):
        """등록한 job_type은 is_registered가 True를 반환한다."""
        registry = JobRegistry()
        registry.register(SampleHandler())

        assert registry.is_registered("sample.job") is True

    def test_is_registered_false_when_absent(self):
        """등록하지 않은 job_type은 is_registered가 False를 반환한다."""
        registry = JobRegistry()

        assert registry.is_registered("sample.job") is False
