"""렌더 캐시 쓰기 경로 헬퍼."""
from modules.cache.backend import CacheBackend
from modules.cache.cache import Cache
from modules.render.model import RenderResult


async def write_render_cache(
    backend: CacheBackend,
    source: str,
    result: RenderResult,
    parser_version: str = "1.0.0",
) -> None:
    """
    렌더 캐시에 결과를 저장한다.

    주어진 소스와 파서 버전을 사용하여 렌더 결과를 캐시에 저장한다.

    Args:
        backend: 사용할 캐시 백엔드
        source: 렌더링한 위키마크업 소스 문본
        result: 저장할 렌더 결과
        parser_version: 파서 버전 (기본값: "1.0.0")
    """
    cache = Cache(backend, parser_version)
    await cache.set_render_result(source, result)
