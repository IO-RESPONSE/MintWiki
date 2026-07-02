"""렌더 캐시 읽기 경로 헬퍼."""
from typing import Optional

from modules.cache.backend import CacheBackend
from modules.cache.cache import Cache
from modules.render.model import RenderResult


async def read_render_cache(
    backend: CacheBackend,
    source: str,
    parser_version: str = "1.0.0",
) -> Optional[RenderResult]:
    """
    렌더 캐시에서 결과를 읽는다.

    주어진 소스와 파서 버전을 사용하여 캐시에서 렌더 결과를 조회한다.
    캐시가 없으면 None을 반환한다.

    Args:
        backend: 사용할 캐시 백엔드
        source: 렌더링할 위키마크업 소스 문본
        parser_version: 파서 버전 (기본값: "1.0.0")

    Returns:
        캐시된 렌더 결과 또는 없으면 None
    """
    cache = Cache(backend, parser_version)
    return await cache.get_render_result(source)
