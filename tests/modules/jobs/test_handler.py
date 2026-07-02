"""잡 핸들러 인터페이스 테스트."""
import pytest

from modules.jobs import JobHandler, JobPayload, JobResult


class TestJobHandlerIsAbstract:
    """JobHandler가 추상 기반 클래스로 동작하는지 검증한다."""

    def test_cannot_instantiate_directly(self):
        """job_type/handle을 구현하지 않은 JobHandler는 직접 생성할 수 없다."""
        with pytest.raises(TypeError):
            JobHandler()

    def test_subclass_missing_handle_cannot_be_instantiated(self):
        """handle()을 구현하지 않은 하위 클래스는 생성할 수 없다."""

        class IncompleteHandler(JobHandler):
            @property
            def job_type(self) -> str:
                return "sample.job"

        with pytest.raises(TypeError):
            IncompleteHandler()

    def test_subclass_missing_job_type_cannot_be_instantiated(self):
        """job_type을 구현하지 않은 하위 클래스는 생성할 수 없다."""

        class IncompleteHandler(JobHandler):
            def handle(self, payload: JobPayload) -> JobResult:
                return JobResult.ok()

        with pytest.raises(TypeError):
            IncompleteHandler()


class TestJobHandlerSubclass:
    """job_type과 handle()을 구현한 하위 클래스가 정상 동작하는지 검증한다."""

    def test_subclass_exposes_declared_job_type(self):
        """job_type을 구현한 하위 클래스는 해당 값을 그대로 노출한다."""

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

        handler = SampleHandler()

        assert handler.job_type == "sample.job"
        assert isinstance(handler, JobHandler)

    def test_handle_returns_job_result(self):
        """handle()은 JobResult를 반환한다."""

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

        result = SampleHandler().handle(SamplePayload())

        assert isinstance(result, JobResult)
        assert result.success is True
        assert result.data == {"handled": "sample.job"}
