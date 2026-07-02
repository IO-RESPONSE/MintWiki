"""캐시 퍼지 잡 핸들러."""
import asyncio

from modules.cache.backend import CacheBackend
from modules.cache.cache import Cache
from modules.cache.invalidate import invalidate_render_cache
from modules.jobs.cache_purge_payload import CACHE_PURGE_JOB_TYPE, CachePurgeJobPayload
from modules.jobs.handler import JobHandler
from modules.jobs.payload import JobPayload
from modules.jobs.result import JobResult


class CachePurgeJobHandler(JobHandler):
    """
    CachePurgeJobPayload를 받아 실제로 렌더 캐시를 비우는 핸들러.

    purge_all=True이면 Cache.clear_all()로 캐시 전체를, 아니면
    invalidate_render_cache로 source/parser_version에 해당하는 항목만
    비운다. handle()은 JobHandler 계약상 동기 메서드이므로, 캐시
    백엔드의 비동기 호출은 asyncio.run으로 감싸 실행한다.
    """

    def __init__(self, backend: CacheBackend):
        """
        핸들러를 생성한다.

        Args:
            backend: 퍼지를 수행할 캐시 백엔드
        """
        self._backend = backend

    @property
    def job_type(self) -> str:
        return CACHE_PURGE_JOB_TYPE

    def handle(self, payload: JobPayload) -> JobResult:
        """
        캐시 퍼지 페이로드를 실행해 캐시를 비운다.

        Args:
            payload: 실행할 CachePurgeJobPayload

        Returns:
            퍼지 성공 시 수행 내역을 담은 JobResult, 페이로드 타입이
            맞지 않으면 실패 JobResult
        """
        if not isinstance(payload, CachePurgeJobPayload):
            return JobResult.fail(
                "CachePurgeJobHandler는 CachePurgeJobPayload만 처리할 수 있습니다: "
                f"{type(payload).__name__}"
            )

        if payload.purge_all:
            asyncio.run(Cache(self._backend, payload.parser_version).clear_all())
            return JobResult.ok(data={"purge_all": True})

        asyncio.run(
            invalidate_render_cache(
                self._backend, payload.source, payload.parser_version
            )
        )
        return JobResult.ok(
            data={"source": payload.source, "parser_version": payload.parser_version}
        )


__all__ = ["CachePurgeJobHandler"]
