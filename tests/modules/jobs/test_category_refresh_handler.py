"""카테고리 갱신 잡 핸들러(placeholder) 테스트."""
from modules.jobs import (
    CATEGORY_REFRESH_JOB_TYPE,
    CategoryRefreshJobHandler,
    CategoryRefreshJobPayload,
    JobHandler,
    JobPayload,
    JobResult,
)


class TestCategoryRefreshJobHandlerJobType:
    """job_type 계약 테스트."""

    def test_exposes_category_refresh_job_type_constant(self):
        """job_type은 CATEGORY_REFRESH_JOB_TYPE 상수와 동일하다."""
        handler = CategoryRefreshJobHandler()

        assert handler.job_type == CATEGORY_REFRESH_JOB_TYPE
        assert handler.job_type == "category.refresh"

    def test_is_instance_of_job_handler(self):
        """CategoryRefreshJobHandler는 jobs 모듈의 공통 JobHandler를 상속한다."""
        handler = CategoryRefreshJobHandler()

        assert isinstance(handler, JobHandler)


class TestCategoryRefreshJobHandlerPlaceholder:
    """placeholder 동작(검증만 하고 성공을 반환) 테스트."""

    def test_handle_accepts_payload_and_returns_category_name(self):
        """유효한 페이로드는 category_name을 담은 성공 결과를 반환한다."""
        handler = CategoryRefreshJobHandler()
        payload = CategoryRefreshJobPayload(category_name="문학")

        job_result = handler.handle(payload)

        assert isinstance(job_result, JobResult)
        assert job_result.success is True
        assert job_result.data == {"category_name": "문학"}

    def test_handle_does_not_raise_for_repeated_calls(self):
        """동일 페이로드를 여러 번 처리해도 오류 없이 성공한다."""
        handler = CategoryRefreshJobHandler()
        payload = CategoryRefreshJobPayload(category_name="역사")

        first_result = handler.handle(payload)
        second_result = handler.handle(payload)

        assert first_result.success is True
        assert second_result.success is True


class TestCategoryRefreshJobHandlerInvalidPayload:
    """잘못된 페이로드 타입 처리 테스트."""

    def test_handle_rejects_non_category_refresh_payload(self):
        """CategoryRefreshJobPayload가 아닌 페이로드는 실패 결과를 반환한다."""

        class OtherPayload(JobPayload):
            @property
            def job_type(self) -> str:
                return "other.job"

        handler = CategoryRefreshJobHandler()
        job_result = handler.handle(OtherPayload())

        assert job_result.success is False
        assert job_result.error is not None
