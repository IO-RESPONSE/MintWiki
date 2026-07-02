"""렌더 캐시 백엔드 인터페이스 및 구현."""
from abc import ABC, abstractmethod
from typing import Optional

from modules.render.model import RenderResult


class CacheBackend(ABC):
    """
    렌더 캐시 백엔드의 인터페이스.

    렌더 결과를 캐시에 저장하고 조회하는 메서드를 정의한다.
    구체적인 백엔드 구현(메모리, Redis 등)은
    이 인터페이스를 구현해야 한다.
    """

    @abstractmethod
    async def get(self, key: str) -> Optional[RenderResult]:
        """
        주어진 키로 캐시에서 렌더 결과를 조회한다.

        Args:
            key: 조회할 캐시 키

        Returns:
            캐시된 렌더 결과 또는 없으면 None
        """
        pass

    @abstractmethod
    async def set(self, key: str, value: RenderResult) -> None:
        """
        렌더 결과를 캐시에 저장한다.

        Args:
            key: 캐시 키
            value: 저장할 렌더 결과
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """
        캐시에서 주어진 키의 렌더 결과를 삭제한다.

        Args:
            key: 삭제할 캐시 키
        """
        pass

    @abstractmethod
    async def clear(self) -> None:
        """캐시의 모든 데이터를 삭제한다."""
        pass


class InMemoryCacheBackend(CacheBackend):
    """
    메모리에 렌더 결과를 캐시하는 백엔드 구현.

    초기 테스트 및 개발 단계에서 사용하기 위한 메모리 기반
    캐시 백엔드 구현이다.
    """

    def __init__(self):
        """캐시 백엔드를 초기화한다."""
        self.data: dict[str, RenderResult] = {}

    async def get(self, key: str) -> Optional[RenderResult]:
        """
        주어진 키로 캐시에서 렌더 결과를 조회한다.

        Args:
            key: 조회할 캐시 키

        Returns:
            캐시된 렌더 결과 또는 없으면 None
        """
        return self.data.get(key)

    async def set(self, key: str, value: RenderResult) -> None:
        """
        렌더 결과를 캐시에 저장한다.

        Args:
            key: 캐시 키
            value: 저장할 렌더 결과
        """
        self.data[key] = value

    async def delete(self, key: str) -> None:
        """
        캐시에서 주어진 키의 렌더 결과를 삭제한다.

        Args:
            key: 삭제할 캐시 키
        """
        self.data.pop(key, None)

    async def clear(self) -> None:
        """캐시의 모든 데이터를 삭제한다."""
        self.data.clear()
