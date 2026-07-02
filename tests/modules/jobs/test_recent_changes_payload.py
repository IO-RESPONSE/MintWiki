"""최근 변경 내역 잡 페이로드 테스트."""
from datetime import datetime, timezone

import pytest

from modules.jobs import JobPayload
from modules.jobs.recent_changes_payload import (
    RECENT_CHANGES_JOB_TYPE,
    InvalidRecentChangesJobPayloadError,
    RecentChangesJobPayload,
)


def _occurred_at() -> datetime:
    return datetime(2026, 7, 2, 9, 0, tzinfo=timezone.utc)


class TestRecentChangesJobPayloadConstruction:
    """최근 변경 내역 잡 페이로드 생성 테스트."""

    def test_creates_payload_with_required_fields(self):
        """page_name, author_id, occurred_at을 지정하면 페이로드가 만들어진다."""
        payload = RecentChangesJobPayload(
            page_name="Main Page",
            author_id="user-1",
            occurred_at=_occurred_at(),
        )

        assert payload.page_name == "Main Page"
        assert payload.author_id == "user-1"
        assert payload.occurred_at == _occurred_at()

    def test_defaults_summary_to_empty_string(self):
        """summary를 지정하지 않으면 빈 문자열이 기본값이다."""
        payload = RecentChangesJobPayload(
            page_name="Main Page",
            author_id="user-1",
            occurred_at=_occurred_at(),
        )

        assert payload.summary == ""

    def test_creates_payload_with_summary(self):
        """summary를 지정하면 해당 값이 그대로 저장된다."""
        payload = RecentChangesJobPayload(
            page_name="Main Page",
            author_id="user-1",
            occurred_at=_occurred_at(),
            summary="오타 수정",
        )

        assert payload.summary == "오타 수정"

    def test_rejects_missing_page_name(self):
        """page_name이 None이면 생성할 수 없다."""
        with pytest.raises(InvalidRecentChangesJobPayloadError):
            RecentChangesJobPayload(
                page_name=None,
                author_id="user-1",
                occurred_at=_occurred_at(),
            )

    def test_rejects_blank_page_name(self):
        """page_name이 공백만 있으면 생성할 수 없다."""
        with pytest.raises(InvalidRecentChangesJobPayloadError):
            RecentChangesJobPayload(
                page_name="   ",
                author_id="user-1",
                occurred_at=_occurred_at(),
            )

    def test_rejects_empty_page_name(self):
        """page_name이 빈 문자열이면 생성할 수 없다."""
        with pytest.raises(InvalidRecentChangesJobPayloadError):
            RecentChangesJobPayload(
                page_name="",
                author_id="user-1",
                occurred_at=_occurred_at(),
            )

    def test_rejects_missing_occurred_at(self):
        """occurred_at이 None이면 생성할 수 없다."""
        with pytest.raises(InvalidRecentChangesJobPayloadError):
            RecentChangesJobPayload(
                page_name="Main Page",
                author_id="user-1",
                occurred_at=None,
            )


class TestRecentChangesJobPayloadJobType:
    """job_type 계약 테스트."""

    def test_exposes_recent_changes_job_type_constant(self):
        """job_type은 RECENT_CHANGES_JOB_TYPE 상수와 동일하다."""
        payload = RecentChangesJobPayload(
            page_name="Main Page",
            author_id="user-1",
            occurred_at=_occurred_at(),
        )

        assert payload.job_type == RECENT_CHANGES_JOB_TYPE
        assert payload.job_type == "recent_changes.record"

    def test_is_instance_of_job_payload(self):
        """RecentChangesJobPayload는 jobs 모듈의 공통 JobPayload를 상속한다."""
        payload = RecentChangesJobPayload(
            page_name="Main Page",
            author_id="user-1",
            occurred_at=_occurred_at(),
        )

        assert isinstance(payload, JobPayload)
