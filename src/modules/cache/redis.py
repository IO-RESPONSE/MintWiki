"""Redis 기반 렌더 캐시 백엔드 구현."""
import json
from typing import Optional

from modules.cache.backend import CacheBackend
from modules.render.model import RenderResult


class RedisCacheBackend(CacheBackend):
    """
    Redis를 사용하는 렌더 캐시 백엔드 구현.

    렌더 결과를 Redis 서버에 JSON 형식으로 저장하고 조회한다.
    분산 캐시 환경에서 여러 프로세스/서버가 캐시를 공유할 수 있다.
    """

    def __init__(self, redis_client, key_prefix: str = "render_cache:"):
        """
        Redis 캐시 백엔드를 초기화한다.

        Args:
            redis_client: redis.Redis 클라이언트 인스턴스 (async 지원)
            key_prefix: 캐시 키에 붙일 접두사 (기본값: "render_cache:")
        """
        self.redis = redis_client
        self.key_prefix = key_prefix

    def _make_redis_key(self, key: str) -> str:
        """
        캐시 키에 접두사를 붙여 Redis 키를 생성한다.

        Args:
            key: 캐시 키

        Returns:
            접두사가 붙은 Redis 키
        """
        return f"{self.key_prefix}{key}"

    def _serialize_render_result(self, result: RenderResult) -> str:
        """
        RenderResult를 JSON 문자열로 직렬화한다.

        Args:
            result: 직렬화할 RenderResult

        Returns:
            JSON 형식의 문자열
        """
        data = {
            "html": result.html,
            "metadata": result.metadata,
        }
        return json.dumps(data, ensure_ascii=False)

    def _deserialize_render_result(self, json_str: str) -> RenderResult:
        """
        JSON 문자열을 RenderResult로 역직렬화한다.

        Args:
            json_str: JSON 형식의 문자열

        Returns:
            역직렬화된 RenderResult
        """
        data = json.loads(json_str)
        return RenderResult(
            html=data["html"],
            metadata=data["metadata"],
        )

    async def get(self, key: str) -> Optional[RenderResult]:
        """
        주어진 키로 Redis에서 렌더 결과를 조회한다.

        Args:
            key: 조회할 캐시 키

        Returns:
            캐시된 렌더 결과 또는 없으면 None
        """
        redis_key = self._make_redis_key(key)
        cached_data = await self.redis.get(redis_key)

        if cached_data is None:
            return None

        # Redis에서 반환하는 바이트를 문자열로 변환
        json_str = (
            cached_data.decode("utf-8")
            if isinstance(cached_data, bytes)
            else cached_data
        )
        return self._deserialize_render_result(json_str)

    async def set(self, key: str, value: RenderResult) -> None:
        """
        렌더 결과를 Redis에 저장한다.

        Args:
            key: 캐시 키
            value: 저장할 렌더 결과
        """
        redis_key = self._make_redis_key(key)
        json_str = self._serialize_render_result(value)
        await self.redis.set(redis_key, json_str)

    async def delete(self, key: str) -> None:
        """
        Redis에서 주어진 키의 렌더 결과를 삭제한다.

        Args:
            key: 삭제할 캐시 키
        """
        redis_key = self._make_redis_key(key)
        await self.redis.delete(redis_key)

    async def clear(self) -> None:
        """
        Redis에서 캐시 접두사에 해당하는 모든 데이터를 삭제한다.

        이 메서드는 키 패턴을 사용하여 같은 접두사의 모든 키를 찾고 삭제한다.
        """
        pattern = f"{self.key_prefix}*"
        # Redis의 SCAN 명령을 사용하여 매우 큰 데이터셋에서도 안전하게 삭제할 수 있다
        cursor = 0
        while True:
            cursor, keys = await self.redis.scan(cursor, match=pattern)
            if keys:
                await self.redis.delete(*keys)
            if cursor == 0:
                break
