"""캐시 퍼지 잡 핸들러 테스트."""
import asyncio

from modules.cache import InMemoryCacheBackend, read_render_cache, write_render_cache
from modules.jobs import (
    CACHE_PURGE_JOB_TYPE,
    CachePurgeJobHandler,
    CachePurgeJobPayload,
    JobHandler,
    JobPayload,
    JobResult,
)
from modules.render.model import RenderResult


def _run(coro):
    """비동기 캐시 헬퍼를 동기 테스트 코드에서 실행하기 위한 유틸리티.

    handler.handle()이 내부에서 asyncio.run을 사용하므로, 테스트 자체를
    async로 만들면 이미 실행 중인 이벤트 루프와 충돌한다. 테스트는 동기로
    유지하고, 캐시 상태를 준비/검증할 때만 이 헬퍼로 이벤트 루프를 연다.
    """
    return asyncio.run(coro)


class TestCachePurgeJobHandlerJobType:
    """job_type 계약 테스트."""

    def test_exposes_cache_purge_job_type_constant(self):
        """job_type은 CACHE_PURGE_JOB_TYPE 상수와 동일하다."""
        handler = CachePurgeJobHandler(InMemoryCacheBackend())

        assert handler.job_type == CACHE_PURGE_JOB_TYPE
        assert handler.job_type == "cache.purge"

    def test_is_instance_of_job_handler(self):
        """CachePurgeJobHandler는 jobs 모듈의 공통 JobHandler를 상속한다."""
        handler = CachePurgeJobHandler(InMemoryCacheBackend())

        assert isinstance(handler, JobHandler)


class TestCachePurgeJobHandlerScopedPurge:
    """source를 지정한 범위 한정 퍼지 테스트."""

    def test_handle_removes_only_matching_entry(self):
        """source/parser_version에 해당하는 캐시 항목만 지운다."""
        backend = InMemoryCacheBackend()
        source = "== 제목 =="
        other_source = "다른 소스"
        _run(write_render_cache(backend, source, RenderResult(html="<h2>제목</h2>", metadata={})))
        _run(write_render_cache(backend, other_source, RenderResult(html="<p>다른 결과</p>", metadata={})))

        handler = CachePurgeJobHandler(backend)
        job_result = handler.handle(CachePurgeJobPayload(source=source))

        assert isinstance(job_result, JobResult)
        assert job_result.success is True
        assert job_result.data == {"source": source, "parser_version": "1.0.0"}
        assert _run(read_render_cache(backend, source)) is None
        assert _run(read_render_cache(backend, other_source)) is not None

    def test_handle_uses_given_parser_version(self):
        """parser_version이 다르면 해당 버전의 항목만 지운다."""
        backend = InMemoryCacheBackend()
        source = "동일한 소스"
        _run(write_render_cache(backend, source, RenderResult(html="<p>v1</p>", metadata={}), "1.0.0"))
        _run(write_render_cache(backend, source, RenderResult(html="<p>v2</p>", metadata={}), "2.0.0"))

        handler = CachePurgeJobHandler(backend)
        handler.handle(CachePurgeJobPayload(source=source, parser_version="1.0.0"))

        assert _run(read_render_cache(backend, source, "1.0.0")) is None
        assert _run(read_render_cache(backend, source, "2.0.0")) is not None

    def test_handle_scoped_purge_on_missing_entry_does_not_error(self):
        """존재하지 않는 항목을 지워도 오류 없이 성공한다."""
        backend = InMemoryCacheBackend()

        handler = CachePurgeJobHandler(backend)
        job_result = handler.handle(CachePurgeJobPayload(source="없는 소스"))

        assert job_result.success is True


class TestCachePurgeJobHandlerPurgeAll:
    """purge_all=True 전체 퍼지 테스트."""

    def test_handle_clears_all_entries(self):
        """purge_all=True이면 캐시 전체를 비운다."""
        backend = InMemoryCacheBackend()
        source1 = "소스 1"
        source2 = "소스 2"
        _run(write_render_cache(backend, source1, RenderResult(html="<p>1</p>", metadata={})))
        _run(write_render_cache(backend, source2, RenderResult(html="<p>2</p>", metadata={})))

        handler = CachePurgeJobHandler(backend)
        job_result = handler.handle(CachePurgeJobPayload(purge_all=True))

        assert job_result.success is True
        assert job_result.data == {"purge_all": True}
        assert _run(read_render_cache(backend, source1)) is None
        assert _run(read_render_cache(backend, source2)) is None

    def test_handle_purge_all_on_empty_cache_does_not_error(self):
        """빈 캐시에 대해 전체 퍼지를 수행해도 오류가 발생하지 않는다."""
        backend = InMemoryCacheBackend()

        handler = CachePurgeJobHandler(backend)
        job_result = handler.handle(CachePurgeJobPayload(purge_all=True))

        assert job_result.success is True


class TestCachePurgeJobHandlerInvalidPayload:
    """잘못된 페이로드 타입 처리 테스트."""

    def test_handle_rejects_non_cache_purge_payload(self):
        """CachePurgeJobPayload가 아닌 페이로드는 실패 결과를 반환한다."""

        class OtherPayload(JobPayload):
            @property
            def job_type(self) -> str:
                return "other.job"

        handler = CachePurgeJobHandler(InMemoryCacheBackend())
        job_result = handler.handle(OtherPayload())

        assert job_result.success is False
        assert job_result.error is not None
