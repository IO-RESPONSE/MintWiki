"""잡 실행 컨텍스트 테스트."""
from datetime import datetime, timedelta, timezone

import pytest

from modules.jobs import JobPayload, JobResult, JobRunContext, JobStatus
from modules.jobs.job_run_context import InvalidJobRunContextError


class SamplePayload(JobPayload):
    @property
    def job_type(self) -> str:
        return "sample.job"


class TestJobRunContextCreation:
    """정상적인 JobRunContext 생성을 검증한다."""

    def test_create_pending_context(self):
        """PENDING 상태의 컨텍스트를 생성할 수 있다."""
        now = datetime.now(timezone.utc)
        payload = SamplePayload()

        context = JobRunContext(
            job_id="test-123",
            payload=payload,
            status=JobStatus.PENDING,
            started_at=now,
        )

        assert context.job_id == "test-123"
        assert context.payload is payload
        assert context.job_type == "sample.job"
        assert context.status == JobStatus.PENDING
        assert context.started_at == now
        assert context.completed_at is None
        assert context.result is None

    def test_create_running_context(self):
        """RUNNING 상태의 컨텍스트를 생성할 수 있다."""
        now = datetime.now(timezone.utc)

        context = JobRunContext(
            job_id="test-456",
            payload=SamplePayload(),
            status=JobStatus.RUNNING,
            started_at=now,
        )

        assert context.status == JobStatus.RUNNING
        assert context.result is None

    def test_create_retrying_context(self):
        """RETRYING 상태의 컨텍스트를 생성할 수 있다."""
        now = datetime.now(timezone.utc)

        context = JobRunContext(
            job_id="test-789",
            payload=SamplePayload(),
            status=JobStatus.RETRYING,
            started_at=now,
        )

        assert context.status == JobStatus.RETRYING

    def test_create_succeeded_context(self):
        """성공한 컨텍스트를 생성할 수 있다."""
        now = datetime.now(timezone.utc)
        result = JobResult.ok(data={"key": "value"})

        context = JobRunContext(
            job_id="test-success",
            payload=SamplePayload(),
            status=JobStatus.SUCCEEDED,
            started_at=now,
            completed_at=now + timedelta(seconds=5),
            result=result,
        )

        assert context.status == JobStatus.SUCCEEDED
        assert context.result is result
        assert context.completed_at > context.started_at

    def test_create_failed_context(self):
        """실패한 컨텍스트를 생성할 수 있다."""
        now = datetime.now(timezone.utc)
        result = JobResult.fail("처리 실패")

        context = JobRunContext(
            job_id="test-failure",
            payload=SamplePayload(),
            status=JobStatus.FAILED,
            started_at=now,
            completed_at=now + timedelta(seconds=2),
            result=result,
        )

        assert context.status == JobStatus.FAILED
        assert context.result is result


class TestJobRunContextValidation:
    """JobRunContext의 유효성 검증을 검증한다."""

    def test_raises_on_empty_job_id(self):
        """job_id가 빈 문자열이면 예외를 발생시킨다."""
        with pytest.raises(InvalidJobRunContextError):
            JobRunContext(
                job_id="",
                payload=SamplePayload(),
                status=JobStatus.PENDING,
                started_at=datetime.now(timezone.utc),
            )

    def test_raises_on_whitespace_only_job_id(self):
        """job_id가 공백만 있으면 예외를 발생시킨다."""
        with pytest.raises(InvalidJobRunContextError):
            JobRunContext(
                job_id="   ",
                payload=SamplePayload(),
                status=JobStatus.PENDING,
                started_at=datetime.now(timezone.utc),
            )

    def test_raises_when_completed_at_before_started_at(self):
        """completed_at이 started_at보다 이전이면 예외를 발생시킨다."""
        now = datetime.now(timezone.utc)
        result = JobResult.ok()

        with pytest.raises(InvalidJobRunContextError):
            JobRunContext(
                job_id="test-123",
                payload=SamplePayload(),
                status=JobStatus.SUCCEEDED,
                started_at=now,
                completed_at=now - timedelta(seconds=1),
                result=result,
            )

    def test_raises_on_terminal_status_without_result(self):
        """SUCCEEDED 상태인데 result가 없으면 예외를 발생시킨다."""
        with pytest.raises(InvalidJobRunContextError):
            JobRunContext(
                job_id="test-123",
                payload=SamplePayload(),
                status=JobStatus.SUCCEEDED,
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
                result=None,
            )

    def test_raises_on_failed_status_without_result(self):
        """FAILED 상태인데 result가 없으면 예외를 발생시킨다."""
        with pytest.raises(InvalidJobRunContextError):
            JobRunContext(
                job_id="test-123",
                payload=SamplePayload(),
                status=JobStatus.FAILED,
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
                result=None,
            )

    def test_raises_on_active_status_with_result(self):
        """PENDING 상태인데 result가 있으면 예외를 발생시킨다."""
        with pytest.raises(InvalidJobRunContextError):
            JobRunContext(
                job_id="test-123",
                payload=SamplePayload(),
                status=JobStatus.PENDING,
                started_at=datetime.now(timezone.utc),
                result=JobResult.ok(),
            )

    def test_raises_on_running_status_with_result(self):
        """RUNNING 상태인데 result가 있으면 예외를 발생시킨다."""
        with pytest.raises(InvalidJobRunContextError):
            JobRunContext(
                job_id="test-123",
                payload=SamplePayload(),
                status=JobStatus.RUNNING,
                started_at=datetime.now(timezone.utc),
                result=JobResult.ok(),
            )

    def test_raises_on_retrying_status_with_result(self):
        """RETRYING 상태인데 result가 있으면 예외를 발생시킨다."""
        with pytest.raises(InvalidJobRunContextError):
            JobRunContext(
                job_id="test-123",
                payload=SamplePayload(),
                status=JobStatus.RETRYING,
                started_at=datetime.now(timezone.utc),
                result=JobResult.ok(),
            )


class TestJobRunContextStatusQueries:
    """JobRunContext의 상태 확인 메서드를 검증한다."""

    def test_is_pending(self):
        """is_pending()이 PENDING 상태를 올바르게 식별한다."""
        context = JobRunContext(
            job_id="test-123",
            payload=SamplePayload(),
            status=JobStatus.PENDING,
            started_at=datetime.now(timezone.utc),
        )

        assert context.is_pending() is True
        assert context.is_running() is False
        assert context.is_retrying() is False
        assert context.is_succeeded() is False
        assert context.is_failed() is False

    def test_is_running(self):
        """is_running()이 RUNNING 상태를 올바르게 식별한다."""
        context = JobRunContext(
            job_id="test-123",
            payload=SamplePayload(),
            status=JobStatus.RUNNING,
            started_at=datetime.now(timezone.utc),
        )

        assert context.is_pending() is False
        assert context.is_running() is True
        assert context.is_retrying() is False
        assert context.is_succeeded() is False
        assert context.is_failed() is False

    def test_is_retrying(self):
        """is_retrying()이 RETRYING 상태를 올바르게 식별한다."""
        context = JobRunContext(
            job_id="test-123",
            payload=SamplePayload(),
            status=JobStatus.RETRYING,
            started_at=datetime.now(timezone.utc),
        )

        assert context.is_pending() is False
        assert context.is_running() is False
        assert context.is_retrying() is True
        assert context.is_succeeded() is False
        assert context.is_failed() is False

    def test_is_succeeded(self):
        """is_succeeded()가 SUCCEEDED 상태를 올바르게 식별한다."""
        now = datetime.now(timezone.utc)
        context = JobRunContext(
            job_id="test-123",
            payload=SamplePayload(),
            status=JobStatus.SUCCEEDED,
            started_at=now,
            completed_at=now,
            result=JobResult.ok(),
        )

        assert context.is_pending() is False
        assert context.is_running() is False
        assert context.is_retrying() is False
        assert context.is_succeeded() is True
        assert context.is_failed() is False

    def test_is_failed(self):
        """is_failed()가 FAILED 상태를 올바르게 식별한다."""
        now = datetime.now(timezone.utc)
        context = JobRunContext(
            job_id="test-123",
            payload=SamplePayload(),
            status=JobStatus.FAILED,
            started_at=now,
            completed_at=now,
            result=JobResult.fail("오류"),
        )

        assert context.is_pending() is False
        assert context.is_running() is False
        assert context.is_retrying() is False
        assert context.is_succeeded() is False
        assert context.is_failed() is True


class TestJobRunContextTerminalAndActive:
    """JobRunContext의 is_terminal()과 is_active() 메서드를 검증한다."""

    def test_is_terminal_for_succeeded_status(self):
        """SUCCEEDED는 종료 상태다."""
        now = datetime.now(timezone.utc)
        context = JobRunContext(
            job_id="test-123",
            payload=SamplePayload(),
            status=JobStatus.SUCCEEDED,
            started_at=now,
            completed_at=now,
            result=JobResult.ok(),
        )

        assert context.is_terminal() is True

    def test_is_terminal_for_failed_status(self):
        """FAILED는 종료 상태다."""
        now = datetime.now(timezone.utc)
        context = JobRunContext(
            job_id="test-123",
            payload=SamplePayload(),
            status=JobStatus.FAILED,
            started_at=now,
            completed_at=now,
            result=JobResult.fail("오류"),
        )

        assert context.is_terminal() is True

    def test_is_not_terminal_for_pending_status(self):
        """PENDING은 미완료 상태다."""
        context = JobRunContext(
            job_id="test-123",
            payload=SamplePayload(),
            status=JobStatus.PENDING,
            started_at=datetime.now(timezone.utc),
        )

        assert context.is_terminal() is False

    def test_is_not_terminal_for_running_status(self):
        """RUNNING은 미완료 상태다."""
        context = JobRunContext(
            job_id="test-123",
            payload=SamplePayload(),
            status=JobStatus.RUNNING,
            started_at=datetime.now(timezone.utc),
        )

        assert context.is_terminal() is False

    def test_is_not_terminal_for_retrying_status(self):
        """RETRYING은 미완료 상태다."""
        context = JobRunContext(
            job_id="test-123",
            payload=SamplePayload(),
            status=JobStatus.RETRYING,
            started_at=datetime.now(timezone.utc),
        )

        assert context.is_terminal() is False

    def test_is_active_for_active_statuses(self):
        """PENDING, RUNNING, RETRYING은 활성 상태다."""
        now = datetime.now(timezone.utc)

        pending = JobRunContext(
            job_id="test-1",
            payload=SamplePayload(),
            status=JobStatus.PENDING,
            started_at=now,
        )
        assert pending.is_active() is True

        running = JobRunContext(
            job_id="test-2",
            payload=SamplePayload(),
            status=JobStatus.RUNNING,
            started_at=now,
        )
        assert running.is_active() is True

        retrying = JobRunContext(
            job_id="test-3",
            payload=SamplePayload(),
            status=JobStatus.RETRYING,
            started_at=now,
        )
        assert retrying.is_active() is True

    def test_is_not_active_for_terminal_statuses(self):
        """SUCCEEDED와 FAILED는 비활성 상태다."""
        now = datetime.now(timezone.utc)

        succeeded = JobRunContext(
            job_id="test-1",
            payload=SamplePayload(),
            status=JobStatus.SUCCEEDED,
            started_at=now,
            completed_at=now,
            result=JobResult.ok(),
        )
        assert succeeded.is_active() is False

        failed = JobRunContext(
            job_id="test-2",
            payload=SamplePayload(),
            status=JobStatus.FAILED,
            started_at=now,
            completed_at=now,
            result=JobResult.fail("오류"),
        )
        assert failed.is_active() is False
