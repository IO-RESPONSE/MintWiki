"""재시도 정책이 최대 시도 횟수에 도달했을 때 데드레터로 전환되는 흐름을 검증한다."""
from modules.jobs import (
    DeadLetter,
    JobHandler,
    JobPayload,
    JobResult,
    JobStatus,
    RetryPolicy,
    SyncJobRunner,
)


class SamplePayload(JobPayload):
    @property
    def job_type(self) -> str:
        return "sample.job"


class AlwaysFailingHandler(JobHandler):
    """모든 시도에서 실패하는 핸들러. 최대 시도 소진 시나리오를 재현한다."""

    @property
    def job_type(self) -> str:
        return "sample.job"

    def handle(self, payload: JobPayload) -> JobResult:
        return JobResult.fail("처리 실패")


def _run_until_exhausted(runner, handler, payload, policy):
    """재시도 정책이 허용하는 한 계속 실행하고, 마지막 실행 결과와 시도 횟수를 반환한다."""
    attempt = 0
    outcome = None
    while True:
        attempt += 1
        outcome = runner.run(handler, payload)
        if outcome.status == JobStatus.SUCCEEDED or not policy.should_retry(attempt):
            return outcome, attempt


class TestDeadLetterOnMaxRetries:
    """SyncJobRunner와 RetryPolicy를 조합해 재시도 소진 시 데드레터로 전환하는 계약을 검증한다."""

    def test_dead_letter_created_after_retries_exhausted(self):
        """재시도 정책이 허용하는 시도를 모두 소진하면 데드레터를 생성할 수 있다."""
        policy = RetryPolicy(max_attempts=3, base_delay_seconds=0)
        payload = SamplePayload()
        outcome, attempt = _run_until_exhausted(
            SyncJobRunner(), AlwaysFailingHandler(), payload, policy
        )

        assert outcome.status == JobStatus.FAILED
        assert not policy.should_retry(attempt)

        dead_letter = DeadLetter(
            payload=payload, error=outcome.result.error, attempts=attempt
        )

        assert dead_letter.attempts == 3
        assert dead_letter.error == "처리 실패"
        assert dead_letter.job_type == "sample.job"
        assert dead_letter.payload is payload

    def test_no_dead_letter_needed_while_retries_remain(self):
        """재시도 여지가 남아 있는 동안에는 데드레터로 보낼 필요가 없다."""
        policy = RetryPolicy(max_attempts=3, base_delay_seconds=0)

        outcome = SyncJobRunner().run(AlwaysFailingHandler(), SamplePayload())
        attempt = 1

        assert outcome.status == JobStatus.FAILED
        assert policy.should_retry(attempt) is True

    def test_dead_letter_attempts_matches_configured_max_attempts(self):
        """소진 시점의 시도 횟수는 정책에 설정된 max_attempts와 일치한다."""
        policy = RetryPolicy(max_attempts=5, base_delay_seconds=0)
        payload = SamplePayload()
        outcome, attempt = _run_until_exhausted(
            SyncJobRunner(), AlwaysFailingHandler(), payload, policy
        )

        dead_letter = DeadLetter(
            payload=payload, error=outcome.result.error, attempts=attempt
        )

        assert attempt == policy.max_attempts
        assert dead_letter.attempts == policy.max_attempts
