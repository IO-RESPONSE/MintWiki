"""렌더 캐시 서비스 인터페이스."""
from typing import Optional

from modules.cache.backend import CacheBackend
from modules.cache.key import build_render_cache_key
from modules.render.model import RenderResult


class Cache:
    """
    렌더 캐시 서비스.

    렌더링 결과를 캐시에 저장하고 조회하는 고수준의 인터페이스를 제공한다.
    캐시 백엔드에 대한 의존성을 주입받아 다양한 백엔드 구현을 지원한다.
    """

    def __init__(self, backend: CacheBackend, parser_version: str = "1.0.0"):
        """
        캐시 서비스를 초기화한다.

        Args:
            backend: 사용할 캐시 백엔드 구현
            parser_version: 파서 버전 (캐시 키 생성에 사용)
        """
        self.backend = backend
        self.parser_version = parser_version

    async def get_render_result(self, source: str) -> Optional[RenderResult]:
        """
        주어진 소스에 대한 캐시된 렌더 결과를 조회한다.

        Args:
            source: 렌더링할 위키마크업 소스 문본

        Returns:
            캐시된 렌더 결과 또는 없으면 None
        """
        key = build_render_cache_key(source, self.parser_version)
        return await self.backend.get(key)

    async def set_render_result(self, source: str, result: RenderResult) -> None:
        """
        렌더 결과를 캐시에 저장한다.

        Args:
            source: 렌더링한 위키마크업 소스 문본
            result: 저장할 렌더 결과
        """
        key = build_render_cache_key(source, self.parser_version)
        await self.backend.set(key, result)

    async def delete_render_cache(self, source: str) -> None:
        """
        주어진 소스에 대한 캐시된 렌더 결과를 삭제한다.

        Args:
            source: 삭제할 캐시의 소스 문본
        """
        key = build_render_cache_key(source, self.parser_version)
        await self.backend.delete(key)

    async def clear_all(self) -> None:
        """모든 캐시 데이터를 삭제한다."""
        await self.backend.clear()
