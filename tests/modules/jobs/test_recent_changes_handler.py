"""최근 변경 내역 잡 핸들러(placeholder) 테스트."""
from datetime import datetime

from modules.jobs import (
    JobHandler,
    JobPayload,
    JobResult,
    RECENT_CHANGES_JOB_TYPE,
    RecentChangesJobHandler,
    RecentChangesJobPayload,
)


class TestRecentChangesJobHandlerJobType:
    """job_type 계약 테스트."""

    def test_exposes_recent_changes_job_type_constant(self):
        """job_type은 RECENT_CHANGES_JOB_TYPE 상수와 동일하다."""
        handler = RecentChangesJobHandler()

        assert handler.job_type == RECENT_CHANGES_JOB_TYPE
        assert handler.job_type == "recent_changes.record"

    def test_is_instance_of_job_handler(self):
        """RecentChangesJobHandler는 jobs 모듈의 공통 JobHandler를 상속한다."""
        handler = RecentChangesJobHandler()

        assert isinstance(handler, JobHandler)


class TestRecentChangesJobHandlerPlaceholder:
    """placeholder 동작(검증만 하고 성공을 반환) 테스트."""

    def test_handle_accepts_payload_and_returns_fields(self):
        """유효한 페이로드는 필드값을 담은 성공 결과를 반환한다."""
        handler = RecentChangesJobHandler()
        occurred_at = datetime(2026, 7, 2, 9, 30)
        payload = RecentChangesJobPayload(
            page_name="위키엔진",
            author_id="user-1",
            occurred_at=occurred_at,
            summary="오탈자 수정",
        )

        job_result = handler.handle(payload)

        assert isinstance(job_result, JobResult)
        assert job_result.success is True
        assert job_result.data == {
            "page_name": "위키엔진",
            "author_id": "user-1",
            "occurred_at": occurred_at,
            "summary": "오탈자 수정",
        }

    def test_handle_does_not_raise_for_repeated_calls(self):
        """동일 페이로드를 여러 번 처리해도 오류 없이 성공한다."""
        handler = RecentChangesJobHandler()
        payload = RecentChangesJobPayload(
            page_name="문서",
            author_id="user-2",
            occurred_at=datetime(2026, 7, 1, 12, 0),
        )

        first_result = handler.handle(payload)
        second_result = handler.handle(payload)

        assert first_result.success is True
        assert second_result.success is True


class TestRecentChangesJobHandlerInvalidPayload:
    """잘못된 페이로드 타입 처리 테스트."""

    def test_handle_rejects_non_recent_changes_payload(self):
        """RecentChangesJobPayload가 아닌 페이로드는 실패 결과를 반환한다."""

        class OtherPayload(JobPayload):
            @property
            def job_type(self) -> str:
                return "other.job"

        handler = RecentChangesJobHandler()
        job_result = handler.handle(OtherPayload())

        assert job_result.success is False
        assert job_result.error is not None
