"""카테고리 갱신 잡 페이로드 테스트."""
import pytest

from modules.jobs import JobPayload
from modules.jobs.category_refresh_payload import (
    CATEGORY_REFRESH_JOB_TYPE,
    CategoryRefreshJobPayload,
    InvalidCategoryRefreshJobPayloadError,
)


class TestCategoryRefreshJobPayloadConstruction:
    """카테고리 갱신 잡 페이로드 생성 테스트."""

    def test_creates_payload_with_category_name(self):
        """category_name을 지정하면 해당 카테고리를 겨냥한 페이로드가 만들어진다."""
        payload = CategoryRefreshJobPayload(category_name="Programming")

        assert payload.category_name == "Programming"

    def test_rejects_missing_category_name(self):
        """category_name이 None이면 생성할 수 없다."""
        with pytest.raises(InvalidCategoryRefreshJobPayloadError):
            CategoryRefreshJobPayload(category_name=None)

    def test_rejects_blank_category_name(self):
        """category_name이 공백만 있으면 생성할 수 없다."""
        with pytest.raises(InvalidCategoryRefreshJobPayloadError):
            CategoryRefreshJobPayload(category_name="   ")

    def test_rejects_empty_category_name(self):
        """category_name이 빈 문자열이면 생성할 수 없다."""
        with pytest.raises(InvalidCategoryRefreshJobPayloadError):
            CategoryRefreshJobPayload(category_name="")


class TestCategoryRefreshJobPayloadJobType:
    """job_type 계약 테스트."""

    def test_exposes_category_refresh_job_type_constant(self):
        """job_type은 CATEGORY_REFRESH_JOB_TYPE 상수와 동일하다."""
        payload = CategoryRefreshJobPayload(category_name="Programming")

        assert payload.job_type == CATEGORY_REFRESH_JOB_TYPE
        assert payload.job_type == "category.refresh"

    def test_is_instance_of_job_payload(self):
        """CategoryRefreshJobPayload는 jobs 모듈의 공통 JobPayload를 상속한다."""
        payload = CategoryRefreshJobPayload(category_name="Programming")

        assert isinstance(payload, JobPayload)
