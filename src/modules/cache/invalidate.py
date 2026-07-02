"""렌더 캐시 무효화 경로 헬퍼."""
from modules.cache.backend import CacheBackend
from modules.cache.cache import Cache


async def invalidate_render_cache(
    backend: CacheBackend,
    source: str,
    parser_version: str = "1.0.0",
) -> None:
    """
    렌더 캐시를 무효화한다.

    주어진 소스와 파서 버전을 사용하여 캐시에서 렌더 결과를 삭제한다.

    Args:
        backend: 사용할 캐시 백엔드
        source: 무효화할 캐시의 소스 문본
        parser_version: 파서 버전 (기본값: "1.0.0")
    """
    cache = Cache(backend, parser_version)
    await cache.delete_render_cache(source)
