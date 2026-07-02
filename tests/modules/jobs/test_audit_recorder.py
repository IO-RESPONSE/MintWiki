"""JobAuditRecorder 서비스 테스트."""
from modules.jobs.audit_event import JobAuditAction
from modules.jobs.audit_recorder import JobAuditRecorder


class TestJobAuditRecorderRecordJobSucceeded:
    """record_job_succeeded가 감사 이벤트를 남기는지 확인한다."""

    def test_records_job_succeeded_event(self):
        recorder = JobAuditRecorder()

        event = recorder.record_job_succeeded(job_type="sample.job")

        assert event.action is JobAuditAction.JOB_SUCCEEDED
        assert event.job_type == "sample.job"
        assert event.error is None
        assert recorder.events() == [event]

    def test_accumulates_events_across_multiple_successes(self):
        recorder = JobAuditRecorder()

        event1 = recorder.record_job_succeeded(job_type="sample.job")
        event2 = recorder.record_job_succeeded(job_type="other.job")

        assert recorder.events() == [event1, event2]


class TestJobAuditRecorderRecordJobFailed:
    """record_job_failed가 감사 이벤트를 남기는지 확인한다."""

    def test_records_job_failed_event(self):
        recorder = JobAuditRecorder()

        event = recorder.record_job_failed(job_type="sample.job", error="처리 실패")

        assert event.action is JobAuditAction.JOB_FAILED
        assert event.job_type == "sample.job"
        assert event.error == "처리 실패"
        assert recorder.events() == [event]

    def test_accumulates_events_across_multiple_failures(self):
        recorder = JobAuditRecorder()

        event1 = recorder.record_job_failed(job_type="sample.job", error="첫번째 실패")
        event2 = recorder.record_job_failed(job_type="other.job", error="두번째 실패")

        assert recorder.events() == [event1, event2]

    def test_events_returns_copy_not_internal_list(self):
        recorder = JobAuditRecorder()
        recorder.record_job_failed(job_type="sample.job", error="처리 실패")

        result = recorder.events()
        result.clear()

        assert len(recorder.events()) == 1
