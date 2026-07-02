"""백링크 갱신 잡 핸들러(placeholder) 테스트."""
from modules.jobs import (
    BACKLINK_REFRESH_JOB_TYPE,
    BacklinkRefreshJobHandler,
    BacklinkRefreshJobPayload,
    JobHandler,
    JobPayload,
    JobResult,
)


class TestBacklinkRefreshJobHandlerJobType:
    """job_type 계약 테스트."""

    def test_exposes_backlink_refresh_job_type_constant(self):
        """job_type은 BACKLINK_REFRESH_JOB_TYPE 상수와 동일하다."""
        handler = BacklinkRefreshJobHandler()

        assert handler.job_type == BACKLINK_REFRESH_JOB_TYPE
        assert handler.job_type == "backlink.refresh"

    def test_is_instance_of_job_handler(self):
        """BacklinkRefreshJobHandler는 jobs 모듈의 공통 JobHandler를 상속한다."""
        handler = BacklinkRefreshJobHandler()

        assert isinstance(handler, JobHandler)


class TestBacklinkRefreshJobHandlerPlaceholder:
    """placeholder 동작(검증만 하고 성공을 반환) 테스트."""

    def test_handle_accepts_payload_and_returns_page_name(self):
        """유효한 페이로드는 page_name을 담은 성공 결과를 반환한다."""
        handler = BacklinkRefreshJobHandler()
        payload = BacklinkRefreshJobPayload(page_name="시작 페이지")

        job_result = handler.handle(payload)

        assert isinstance(job_result, JobResult)
        assert job_result.success is True
        assert job_result.data == {"page_name": "시작 페이지"}

    def test_handle_does_not_raise_for_repeated_calls(self):
        """동일 페이로드를 여러 번 처리해도 오류 없이 성공한다."""
        handler = BacklinkRefreshJobHandler()
        payload = BacklinkRefreshJobPayload(page_name="문서")

        first_result = handler.handle(payload)
        second_result = handler.handle(payload)

        assert first_result.success is True
        assert second_result.success is True


class TestBacklinkRefreshJobHandlerInvalidPayload:
    """잘못된 페이로드 타입 처리 테스트."""

    def test_handle_rejects_non_backlink_refresh_payload(self):
        """BacklinkRefreshJobPayload가 아닌 페이로드는 실패 결과를 반환한다."""

        class OtherPayload(JobPayload):
            @property
            def job_type(self) -> str:
                return "other.job"

        handler = BacklinkRefreshJobHandler()
        job_result = handler.handle(OtherPayload())

        assert job_result.success is False
        assert job_result.error is not None
