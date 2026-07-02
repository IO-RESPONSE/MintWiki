"""캐시 퍼지 잡 페이로드 테스트."""
import pytest

from modules.jobs import JobPayload
from modules.jobs.cache_purge_payload import (
    CACHE_PURGE_JOB_TYPE,
    CachePurgeJobPayload,
    InvalidCachePurgeJobPayloadError,
)


class TestCachePurgeJobPayloadConstruction:
    """캐시 퍼지 잡 페이로드 생성 테스트."""

    def test_creates_scoped_payload_with_source(self):
        """source만 지정하면 해당 항목만 겨냥한 페이로드가 만들어진다."""
        payload = CachePurgeJobPayload(source="== Title ==")

        assert payload.source == "== Title =="
        assert payload.parser_version == "1.0.0"
        assert payload.purge_all is False

    def test_creates_scoped_payload_with_explicit_parser_version(self):
        """parser_version을 명시하면 그 값을 그대로 사용한다."""
        payload = CachePurgeJobPayload(source="source text", parser_version="2.0.0")

        assert payload.parser_version == "2.0.0"

    def test_creates_purge_all_payload_without_source(self):
        """purge_all=True이면 source 없이도 페이로드를 생성할 수 있다."""
        payload = CachePurgeJobPayload(purge_all=True)

        assert payload.purge_all is True
        assert payload.source is None

    def test_purge_all_ignores_provided_source(self):
        """purge_all=True이면 source가 주어져도 무시된다."""
        payload = CachePurgeJobPayload(source="ignored", purge_all=True)

        assert payload.source is None

    def test_rejects_missing_source_when_not_purge_all(self):
        """purge_all=False인데 source가 없으면 생성할 수 없다."""
        with pytest.raises(InvalidCachePurgeJobPayloadError):
            CachePurgeJobPayload()

    def test_rejects_blank_source_when_not_purge_all(self):
        """purge_all=False인데 source가 공백만 있으면 생성할 수 없다."""
        with pytest.raises(InvalidCachePurgeJobPayloadError):
            CachePurgeJobPayload(source="   ")


class TestCachePurgeJobPayloadJobType:
    """job_type 계약 테스트."""

    def test_exposes_cache_purge_job_type_constant(self):
        """job_type은 CACHE_PURGE_JOB_TYPE 상수와 동일하다."""
        payload = CachePurgeJobPayload(source="doc")

        assert payload.job_type == CACHE_PURGE_JOB_TYPE
        assert payload.job_type == "cache.purge"

    def test_is_instance_of_job_payload(self):
        """CachePurgeJobPayload는 jobs 모듈의 공통 JobPayload를 상속한다."""
        payload = CachePurgeJobPayload(source="doc")

        assert isinstance(payload, JobPayload)
