"""JobAuditEvent 도메인 모델 테스트."""
from datetime import datetime

import pytest

from modules.jobs.audit_event import (
    EmptyJobAuditEventIdError,
    InvalidJobAuditEventError,
    JobAuditAction,
    JobAuditEvent,
    MissingJobTypeError,
)


class TestJobAuditEventCreation:
    """JobAuditEvent 생성 시 필드가 올바르게 설정되는지 확인한다."""

    def test_creates_succeeded_event(self):
        occurred_at = datetime(2026, 1, 1, 0, 0, 0)
        event = JobAuditEvent(
            id="event-1",
            action=JobAuditAction.JOB_SUCCEEDED,
            job_type="cache.purge",
            occurred_at=occurred_at,
        )

        assert event.id == "event-1"
        assert event.action is JobAuditAction.JOB_SUCCEEDED
        assert event.job_type == "cache.purge"
        assert event.occurred_at == occurred_at
        assert event.error is None

    def test_creates_failed_event_with_error(self):
        event = JobAuditEvent(
            id="event-2",
            action=JobAuditAction.JOB_FAILED,
            job_type="search.index",
            occurred_at=datetime(2026, 1, 1, 0, 0, 0),
            error="timeout",
        )

        assert event.action is JobAuditAction.JOB_FAILED
        assert event.error == "timeout"

    def test_raises_when_id_is_empty(self):
        with pytest.raises(EmptyJobAuditEventIdError):
            JobAuditEvent(
                id="",
                action=JobAuditAction.JOB_SUCCEEDED,
                job_type="cache.purge",
                occurred_at=datetime(2026, 1, 1, 0, 0, 0),
            )

    def test_raises_when_id_is_blank(self):
        with pytest.raises(EmptyJobAuditEventIdError):
            JobAuditEvent(
                id="   ",
                action=JobAuditAction.JOB_SUCCEEDED,
                job_type="cache.purge",
                occurred_at=datetime(2026, 1, 1, 0, 0, 0),
            )

    def test_raises_when_job_type_is_empty(self):
        with pytest.raises(MissingJobTypeError):
            JobAuditEvent(
                id="event-3",
                action=JobAuditAction.JOB_SUCCEEDED,
                job_type="",
                occurred_at=datetime(2026, 1, 1, 0, 0, 0),
            )

    def test_raises_when_job_type_is_blank(self):
        with pytest.raises(MissingJobTypeError):
            JobAuditEvent(
                id="event-4",
                action=JobAuditAction.JOB_SUCCEEDED,
                job_type="   ",
                occurred_at=datetime(2026, 1, 1, 0, 0, 0),
            )

    def test_raises_when_failed_event_has_no_error(self):
        with pytest.raises(InvalidJobAuditEventError):
            JobAuditEvent(
                id="event-5",
                action=JobAuditAction.JOB_FAILED,
                job_type="cache.purge",
                occurred_at=datetime(2026, 1, 1, 0, 0, 0),
            )

    def test_raises_when_succeeded_event_has_error(self):
        with pytest.raises(InvalidJobAuditEventError):
            JobAuditEvent(
                id="event-6",
                action=JobAuditAction.JOB_SUCCEEDED,
                job_type="cache.purge",
                occurred_at=datetime(2026, 1, 1, 0, 0, 0),
                error="should not be here",
            )


class TestJobAuditEventIsSucceeded:
    """is_succeeded 메서드가 결과 종류를 올바르게 판단하는지 확인한다."""

    def test_returns_true_for_succeeded_action(self):
        event = JobAuditEvent(
            id="event-7",
            action=JobAuditAction.JOB_SUCCEEDED,
            job_type="cache.purge",
            occurred_at=datetime(2026, 1, 1, 0, 0, 0),
        )

        assert event.is_succeeded() is True
        assert event.is_failed() is False

    def test_returns_false_for_failed_action(self):
        event = JobAuditEvent(
            id="event-8",
            action=JobAuditAction.JOB_FAILED,
            job_type="cache.purge",
            occurred_at=datetime(2026, 1, 1, 0, 0, 0),
            error="boom",
        )

        assert event.is_succeeded() is False


class TestJobAuditEventIsFailed:
    """is_failed 메서드가 결과 종류를 올바르게 판단하는지 확인한다."""

    def test_returns_true_for_failed_action(self):
        event = JobAuditEvent(
            id="event-9",
            action=JobAuditAction.JOB_FAILED,
            job_type="cache.purge",
            occurred_at=datetime(2026, 1, 1, 0, 0, 0),
            error="boom",
        )

        assert event.is_failed() is True
