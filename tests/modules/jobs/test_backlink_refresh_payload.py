"""백링크 갱신 잡 페이로드 테스트."""
import pytest

from modules.jobs import JobPayload
from modules.jobs.backlink_refresh_payload import (
    BACKLINK_REFRESH_JOB_TYPE,
    BacklinkRefreshJobPayload,
    InvalidBacklinkRefreshJobPayloadError,
)


class TestBacklinkRefreshJobPayloadConstruction:
    """백링크 갱신 잡 페이로드 생성 테스트."""

    def test_creates_payload_with_page_name(self):
        """page_name을 지정하면 해당 문서를 겨냥한 페이로드가 만들어진다."""
        payload = BacklinkRefreshJobPayload(page_name="Main Page")

        assert payload.page_name == "Main Page"

    def test_rejects_missing_page_name(self):
        """page_name이 None이면 생성할 수 없다."""
        with pytest.raises(InvalidBacklinkRefreshJobPayloadError):
            BacklinkRefreshJobPayload(page_name=None)

    def test_rejects_blank_page_name(self):
        """page_name이 공백만 있으면 생성할 수 없다."""
        with pytest.raises(InvalidBacklinkRefreshJobPayloadError):
            BacklinkRefreshJobPayload(page_name="   ")

    def test_rejects_empty_page_name(self):
        """page_name이 빈 문자열이면 생성할 수 없다."""
        with pytest.raises(InvalidBacklinkRefreshJobPayloadError):
            BacklinkRefreshJobPayload(page_name="")


class TestBacklinkRefreshJobPayloadJobType:
    """job_type 계약 테스트."""

    def test_exposes_backlink_refresh_job_type_constant(self):
        """job_type은 BACKLINK_REFRESH_JOB_TYPE 상수와 동일하다."""
        payload = BacklinkRefreshJobPayload(page_name="Main Page")

        assert payload.job_type == BACKLINK_REFRESH_JOB_TYPE
        assert payload.job_type == "backlink.refresh"

    def test_is_instance_of_job_payload(self):
        """BacklinkRefreshJobPayload는 jobs 모듈의 공통 JobPayload를 상속한다."""
        payload = BacklinkRefreshJobPayload(page_name="Main Page")

        assert isinstance(payload, JobPayload)
