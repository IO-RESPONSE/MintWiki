"""잡 시스템 통합 테스트.

SyncJobRunner, JobRegistry, JobAuditRecorder, 잡 핸들러들을 함께 사용하면서
실제 시나리오를 끝까지 실행하는 통합 테스트.

개별 유닛 테스트(test_runner.py, test_registry.py 등)는 각 컴포넌트를
독립적으로 검증하지만, 이 파일은 여러 컴포넌트를 한 번에 구성해 실제로
잡이 등록되고, 실행되고, 감사 이벤트로 기록되는 전체 흐름을 확인한다.
"""
import pytest

from modules.jobs import (
    JobAuditAction,
    JobAuditRecorder,
    JobHandler,
    JobPayload,
    JobRegistry,
    JobResult,
    JobStatus,
    SyncJobRunner,
)


class SamplePayload(JobPayload):
    """테스트용 샘플 잡 페이로드."""

    @property
    def job_type(self) -> str:
        return "sample.job"


class OtherPayload(JobPayload):
    """다른 종류의 잡 페이로드."""

    @property
    def job_type(self) -> str:
        return "other.job"


class SampleHandler(JobHandler):
    """샘플 잡을 처리하는 핸들러."""

    @property
    def job_type(self) -> str:
        return "sample.job"

    def handle(self, payload: JobPayload) -> JobResult:
        return JobResult.ok(data={"handled": payload.job_type})


class OtherHandler(JobHandler):
    """다른 종류의 잡을 처리하는 핸들러."""

    @property
    def job_type(self) -> str:
        return "other.job"

    def handle(self, payload: JobPayload) -> JobResult:
        return JobResult.ok()


class FailingHandler(JobHandler):
    """항상 실패하는 핸들러."""

    @property
    def job_type(self) -> str:
        return "failing.job"

    def handle(self, payload: JobPayload) -> JobResult:
        return JobResult.fail("의도적인 실패")


class TestJobsIntegration:
    """여러 컴포넌트의 협력 관계를 검증하는 통합 테스트."""

    def test_runner_with_registry_and_audit_recorder_tracks_single_success(self):
        """핸들러를 레지스트리에 등록하고 실행기에서 실행하면
        감사 기록기가 성공 이벤트를 기록한다."""
        registry = JobRegistry()
        audit_recorder = JobAuditRecorder()
        runner = SyncJobRunner(audit_recorder=audit_recorder)

        handler = SampleHandler()
        registry.register(handler)

        registered_handler = registry.get("sample.job")
        outcome = runner.run(registered_handler, SamplePayload())

        assert outcome.status == JobStatus.SUCCEEDED
        assert outcome.result.success is True

        events = audit_recorder.events()
        assert len(events) == 1
        assert events[0].is_succeeded()
        assert events[0].job_type == "sample.job"

    def test_runner_with_registry_and_audit_recorder_tracks_single_failure(self):
        """핸들러가 실패하면 감사 기록기가 실패 이벤트를 기록한다."""
        registry = JobRegistry()
        audit_recorder = JobAuditRecorder()
        runner = SyncJobRunner(audit_recorder=audit_recorder)

        handler = FailingHandler()
        registry.register(handler)

        registered_handler = registry.get("failing.job")
        outcome = runner.run(registered_handler, OtherPayload())

        # OtherPayload를 FailingHandler로 실행하면 job_type이 일치하지 않는데,
        # handle() 메서드에서는 job_type을 확인하지 않으므로 실패한다.
        assert outcome.status == JobStatus.FAILED
        assert outcome.result.success is False

        events = audit_recorder.events()
        assert len(events) == 1
        assert events[0].is_failed()
        assert events[0].job_type == "other.job"
        assert events[0].error == "의도적인 실패"

    def test_multiple_handlers_registered_and_executed_independently(self):
        """여러 종류의 핸들러를 등록하고 각각 독립적으로 실행하면
        감사 기록기가 각각의 이벤트를 기록한다."""
        registry = JobRegistry()
        audit_recorder = JobAuditRecorder()
        runner = SyncJobRunner(audit_recorder=audit_recorder)

        sample_handler = SampleHandler()
        other_handler = OtherHandler()
        registry.register(sample_handler)
        registry.register(other_handler)

        # 첫 번째 잡 실행
        outcome1 = runner.run(registry.get("sample.job"), SamplePayload())
        # 두 번째 잡 실행
        outcome2 = runner.run(registry.get("other.job"), OtherPayload())

        assert outcome1.status == JobStatus.SUCCEEDED
        assert outcome2.status == JobStatus.SUCCEEDED

        events = audit_recorder.events()
        assert len(events) == 2
        assert events[0].job_type == "sample.job"
        assert events[0].is_succeeded()
        assert events[1].job_type == "other.job"
        assert events[1].is_succeeded()

    def test_audit_recorder_accumulates_events_across_multiple_executions(self):
        """같은 감사 기록기로 여러 잡을 실행하면 이벤트가 누적된다."""
        audit_recorder = JobAuditRecorder()
        runner = SyncJobRunner(audit_recorder=audit_recorder)
        handler = SampleHandler()

        for i in range(3):
            runner.run(handler, SamplePayload())

        events = audit_recorder.events()
        assert len(events) == 3
        assert all(e.is_succeeded() for e in events)
        assert all(e.job_type == "sample.job" for e in events)


__all__ = [
    "TestJobsIntegration",
    "SamplePayload",
    "OtherPayload",
    "SampleHandler",
    "OtherHandler",
    "FailingHandler",
]
