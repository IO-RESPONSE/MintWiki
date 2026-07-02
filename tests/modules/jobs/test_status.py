"""잡 상태 열거형 테스트."""
from modules.jobs.status import JobStatus


class TestJobStatus:
    """JobStatus 열거형 값 테스트."""

    def test_has_pending_member(self):
        """PENDING 멤버는 pending 문자열 값과 일치한다."""
        assert JobStatus.PENDING.value == "pending"

    def test_has_running_member(self):
        """RUNNING 멤버는 running 문자열 값과 일치한다."""
        assert JobStatus.RUNNING.value == "running"

    def test_has_succeeded_member(self):
        """SUCCEEDED 멤버는 succeeded 문자열 값과 일치한다."""
        assert JobStatus.SUCCEEDED.value == "succeeded"

    def test_has_failed_member(self):
        """FAILED 멤버는 failed 문자열 값과 일치한다."""
        assert JobStatus.FAILED.value == "failed"

    def test_has_retrying_member(self):
        """RETRYING 멤버는 retrying 문자열 값과 일치한다."""
        assert JobStatus.RETRYING.value == "retrying"

    def test_members_are_distinct(self):
        """모든 상태 멤버는 서로 다른 값을 가진다."""
        values = [member.value for member in JobStatus]
        assert len(values) == len(set(values))
