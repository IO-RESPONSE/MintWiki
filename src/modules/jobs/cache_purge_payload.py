"""캐시 퍼지 잡 페이로드."""
from typing import Optional

from modules.jobs.payload import JobPayload

CACHE_PURGE_JOB_TYPE = "cache.purge"


class InvalidCachePurgeJobPayloadError(Exception):
    """캐시 퍼지 페이로드 파라미터가 유효하지 않을 때 발생."""

    pass


class CachePurgeJobPayload(JobPayload):
    """
    렌더 캐시 퍼지 작업 큐에 전달되는 페이로드.

    특정 소스/파서 버전 조합의 캐시 항목만 지울지(scoped), 아니면 캐시
    전체를 비울지(purge_all)를 이 페이로드가 담아 잡 러너에 전달한다.
    실제로 modules.cache의 invalidate_render_cache/Cache.clear_all을
    호출해 퍼지를 수행하는 핸들러는 후속 태스크에서 추가되므로, 이
    페이로드는 데이터 계약만 정의한다.
    """

    def __init__(
        self,
        source: Optional[str] = None,
        parser_version: str = "1.0.0",
        purge_all: bool = False,
    ):
        """
        캐시 퍼지 잡 페이로드를 생성한다.

        Args:
            source: 퍼지할 캐시 항목의 원본 소스 문본. purge_all=True인
                경우에는 사용되지 않으므로 생략할 수 있다.
            parser_version: 퍼지할 캐시 항목의 파서 버전 (기본값 "1.0.0")
            purge_all: True이면 source를 무시하고 캐시 전체를 비우도록
                지시한다 (기본값 False)

        Raises:
            InvalidCachePurgeJobPayloadError: purge_all이 False인데
                source가 비어있거나 공백만 있는 경우
        """
        if not purge_all and (source is None or not source.strip()):
            raise InvalidCachePurgeJobPayloadError(
                "purge_all이 False이면 source가 비어있을 수 없습니다"
            )

        self._source = None if purge_all else source
        self._parser_version = parser_version
        self._purge_all = purge_all

    @property
    def job_type(self) -> str:
        return CACHE_PURGE_JOB_TYPE

    @property
    def source(self) -> Optional[str]:
        return self._source

    @property
    def parser_version(self) -> str:
        return self._parser_version

    @property
    def purge_all(self) -> bool:
        return self._purge_all


__all__ = [
    "CACHE_PURGE_JOB_TYPE",
    "InvalidCachePurgeJobPayloadError",
    "CachePurgeJobPayload",
]
