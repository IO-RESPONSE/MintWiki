"""동기 잡 실행기 테스트."""
from modules.jobs import (
    JobHandler,
    JobPayload,
    JobResult,
    JobRunOutcome,
    JobStatus,
    SyncJobRunner,
)


class SamplePayload(JobPayload):
    @property
    def job_type(self) -> str:
        return "sample.job"


class SucceedingHandler(JobHandler):
    @property
    def job_type(self) -> str:
        return "sample.job"

    def handle(self, payload: JobPayload) -> JobResult:
        return JobResult.ok(data={"handled": payload.job_type})


class FailingHandler(JobHandler):
    @property
    def job_type(self) -> str:
        return "sample.job"

    def handle(self, payload: JobPayload) -> JobResult:
        return JobResult.fail("처리 실패")


class RaisingHandler(JobHandler):
    @property
    def job_type(self) -> str:
        return "sample.job"

    def handle(self, payload: JobPayload) -> JobResult:
        raise RuntimeError("예상치 못한 오류")


class TestSyncJobRunnerSuccess:
    """핸들러가 성공 결과를 반환하는 경우를 검증한다."""

    def test_run_returns_succeeded_status_and_result(self):
        """handle()이 성공한 JobResult를 반환하면 상태는 SUCCEEDED다."""
        outcome = SyncJobRunner().run(SucceedingHandler(), SamplePayload())

        assert isinstance(outcome, JobRunOutcome)
        assert outcome.status == JobStatus.SUCCEEDED
        assert outcome.result.success is True
        assert outcome.result.data == {"handled": "sample.job"}


class TestSyncJobRunnerFailure:
    """핸들러가 실패 결과를 반환하거나 예외를 던지는 경우를 검증한다."""

    def test_run_returns_failed_status_and_result(self):
        """handle()이 실패한 JobResult를 반환하면 상태는 FAILED다."""
        outcome = SyncJobRunner().run(FailingHandler(), SamplePayload())

        assert outcome.status == JobStatus.FAILED
        assert outcome.result.success is False
        assert outcome.result.error == "처리 실패"

    def test_run_converts_handler_exception_to_failed_result(self):
        """handle()이 예외를 던지면 run()은 이를 실패 결과로 변환해 반환한다."""
        outcome = SyncJobRunner().run(RaisingHandler(), SamplePayload())

        assert outcome.status == JobStatus.FAILED
        assert outcome.result.success is False
        assert outcome.result.error == "예상치 못한 오류"
