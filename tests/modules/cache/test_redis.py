"""Redis 캐시 백엔드 테스트."""
import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from modules.cache.redis import RedisCacheBackend
from modules.render.model import RenderResult


class TestRedisCacheBackendBasic:
    """Redis 캐시 백엔드 기본 기능 테스트."""

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis 클라이언트를 제공한다."""
        mock = MagicMock()
        mock.get = AsyncMock()
        mock.set = AsyncMock()
        mock.delete = AsyncMock()
        mock.scan = AsyncMock()
        return mock

    @pytest.mark.asyncio
    async def test_get_non_existent_key_returns_none(self, mock_redis):
        """없는 키를 조회하면 None을 반환한다."""
        mock_redis.get.return_value = None
        backend = RedisCacheBackend(mock_redis)

        result = await backend.get("non_existent_key")

        assert result is None
        mock_redis.get.assert_called_once_with("render_cache:non_existent_key")

    @pytest.mark.asyncio
    async def test_set_and_get(self, mock_redis):
        """캐시에 저장한 렌더 결과를 조회할 수 있다."""
        render_result = RenderResult(html="<p>test</p>", metadata={})
        key = "test_key"

        # set 호출
        backend = RedisCacheBackend(mock_redis)
        await backend.set(key, render_result)

        # set이 호출되었는지 확인
        mock_redis.set.assert_called_once()
        call_args = mock_redis.set.call_args
        assert call_args[0][0] == "render_cache:test_key"
        assert "<p>test</p>" in call_args[0][1]

        # get 호출
        stored_json = call_args[0][1]
        mock_redis.get.return_value = stored_json.encode("utf-8")

        retrieved = await backend.get(key)

        assert retrieved is not None
        assert retrieved.html == "<p>test</p>"
        assert retrieved.metadata == {}

    @pytest.mark.asyncio
    async def test_set_overwrites_existing_key(self, mock_redis):
        """같은 키로 다시 저장하면 기존 값이 덮어써진다."""
        backend = RedisCacheBackend(mock_redis)
        key = "test_key"

        result1 = RenderResult(html="<p>first</p>", metadata={})
        result2 = RenderResult(html="<p>second</p>", metadata={})

        await backend.set(key, result1)
        await backend.set(key, result2)

        # 두 번째 호출이 일어났는지 확인
        assert mock_redis.set.call_count == 2

        # 두 번째 호출의 인자를 확인
        second_call_args = mock_redis.set.call_args_list[1]
        assert "<p>second</p>" in second_call_args[0][1]


class TestRedisCacheBackendDelete:
    """Redis 캐시 삭제 기능 테스트."""

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis 클라이언트를 제공한다."""
        mock = MagicMock()
        mock.get = AsyncMock()
        mock.set = AsyncMock()
        mock.delete = AsyncMock()
        mock.scan = AsyncMock()
        return mock

    @pytest.mark.asyncio
    async def test_delete_existing_key(self, mock_redis):
        """캐시에서 저장된 데이터를 삭제할 수 있다."""
        backend = RedisCacheBackend(mock_redis)
        key = "test_key"

        await backend.delete(key)

        mock_redis.delete.assert_called_once_with("render_cache:test_key")

    @pytest.mark.asyncio
    async def test_delete_non_existent_key_does_not_error(self, mock_redis):
        """없는 키를 삭제해도 에러가 발생하지 않는다."""
        backend = RedisCacheBackend(mock_redis)
        # 에러가 발생하지 않아야 한다
        await backend.delete("non_existent_key")

        mock_redis.delete.assert_called_once_with("render_cache:non_existent_key")


class TestRedisCacheBackendClear:
    """Redis 캐시 전체 삭제 기능 테스트."""

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis 클라이언트를 제공한다."""
        mock = MagicMock()
        mock.scan = AsyncMock()
        mock.delete = AsyncMock()
        return mock

    @pytest.mark.asyncio
    async def test_clear_removes_all_data(self, mock_redis):
        """clear는 모든 캐시 데이터를 삭제한다."""
        # Redis SCAN 명령의 반환값을 모의한다
        # (cursor, keys) 형식
        keys_batch1 = [
            b"render_cache:key_0",
            b"render_cache:key_1",
        ]
        keys_batch2 = [
            b"render_cache:key_2",
            b"render_cache:key_3",
        ]

        mock_redis.scan.side_effect = [
            (1, keys_batch1),  # 첫 번째 스캔, cursor=1
            (0, keys_batch2),  # 두 번째 스캔, cursor=0 (끝)
        ]

        backend = RedisCacheBackend(mock_redis)
        await backend.clear()

        # scan이 두 번 호출되었는지 확인
        assert mock_redis.scan.call_count == 2

        # delete가 키들과 함께 호출되었는지 확인
        delete_calls = mock_redis.delete.call_args_list
        assert len(delete_calls) == 2

    @pytest.mark.asyncio
    async def test_clear_on_empty_cache(self, mock_redis):
        """비어있는 캐시를 clear해도 에러가 발생하지 않는다."""
        # 빈 결과를 반환하는 SCAN
        mock_redis.scan.return_value = (0, [])

        backend = RedisCacheBackend(mock_redis)
        # 에러가 발생하지 않아야 한다
        await backend.clear()

        mock_redis.scan.assert_called_once()


class TestRedisCacheBackendKeyPrefix:
    """Redis 캐시 키 접두사 테스트."""

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis 클라이언트를 제공한다."""
        mock = MagicMock()
        mock.get = AsyncMock()
        mock.set = AsyncMock()
        mock.delete = AsyncMock()
        return mock

    @pytest.mark.asyncio
    async def test_custom_key_prefix(self, mock_redis):
        """사용자 정의 키 접두사를 사용할 수 있다."""
        custom_prefix = "my_cache:"
        backend = RedisCacheBackend(mock_redis, key_prefix=custom_prefix)

        key = "test_key"
        render_result = RenderResult(html="<p>test</p>", metadata={})

        await backend.set(key, render_result)

        # 접두사가 사용되었는지 확인
        call_args = mock_redis.set.call_args
        assert call_args[0][0].startswith(custom_prefix)
        assert call_args[0][0] == "my_cache:test_key"

    @pytest.mark.asyncio
    async def test_default_key_prefix(self, mock_redis):
        """기본 키 접두사는 'render_cache:'이다."""
        backend = RedisCacheBackend(mock_redis)

        key = "test_key"
        render_result = RenderResult(html="<p>test</p>", metadata={})

        await backend.set(key, render_result)

        # 기본 접두사가 사용되었는지 확인
        call_args = mock_redis.set.call_args
        assert call_args[0][0] == "render_cache:test_key"


class TestRedisCacheBackendSerialization:
    """Redis 캐시 직렬화/역직렬화 테스트."""

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis 클라이언트를 제공한다."""
        mock = MagicMock()
        mock.get = AsyncMock()
        mock.set = AsyncMock()
        mock.delete = AsyncMock()
        return mock

    @pytest.mark.asyncio
    async def test_serialize_render_result_with_metadata(self, mock_redis):
        """메타데이터를 포함한 RenderResult를 직렬화할 수 있다."""
        backend = RedisCacheBackend(mock_redis)

        metadata = {
            "headings": [{"level": 1, "text": "Title", "id": "heading-1"}],
            "links": ["https://example.com"],
            "categories": ["Category1", "Category2"],
        }
        render_result = RenderResult(html="<p>test</p>", metadata=metadata)

        await backend.set("test_key", render_result)

        # 저장된 JSON을 확인
        call_args = mock_redis.set.call_args
        json_str = call_args[0][1]
        data = json.loads(json_str)

        assert data["html"] == "<p>test</p>"
        assert data["metadata"] == metadata

    @pytest.mark.asyncio
    async def test_deserialize_render_result_from_json(self, mock_redis):
        """JSON에서 RenderResult를 역직렬화할 수 있다."""
        backend = RedisCacheBackend(mock_redis)

        metadata = {
            "headings": [{"level": 1, "text": "Title", "id": "heading-1"}],
            "links": ["https://example.com"],
            "categories": ["Category1"],
        }
        render_result = RenderResult(html="<h1>Test</h1>", metadata=metadata)

        # 직렬화된 형태를 만든다
        json_str = backend._serialize_render_result(render_result)
        mock_redis.get.return_value = json_str.encode("utf-8")

        # 역직렬화
        retrieved = await backend.get("test_key")

        assert retrieved is not None
        assert retrieved.html == "<h1>Test</h1>"
        assert retrieved.metadata == metadata
        assert len(retrieved.metadata["headings"]) == 1
        assert retrieved.metadata["categories"] == ["Category1"]

    @pytest.mark.asyncio
    async def test_unicode_handling_in_serialization(self, mock_redis):
        """유니코드 문자가 포함된 메타데이터를 처리할 수 있다."""
        backend = RedisCacheBackend(mock_redis)

        metadata = {
            "headings": [{"level": 1, "text": "한글 제목", "id": "heading-1"}],
            "links": ["한글 링크"],
            "categories": ["분류1", "분류2"],
        }
        render_result = RenderResult(
            html="<h1>한글 테스트</h1>", metadata=metadata
        )

        await backend.set("test_key", render_result)

        call_args = mock_redis.set.call_args
        json_str = call_args[0][1]
        data = json.loads(json_str)

        # 유니코드가 제대로 보존되었는지 확인
        assert "한글 제목" in data["metadata"]["headings"][0]["text"]
        assert "한글 테스트" in data["html"]


class TestRedisCacheBackendMultipleKeys:
    """Redis 캐시 여러 키 관리 테스트."""

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis 클라이언트를 제공한다."""
        mock = MagicMock()
        mock.get = AsyncMock()
        mock.set = AsyncMock()
        mock.delete = AsyncMock()
        mock.scan = AsyncMock()
        return mock

    @pytest.mark.asyncio
    async def test_multiple_keys_are_independent(self, mock_redis):
        """각 키의 값은 독립적이다."""
        backend = RedisCacheBackend(mock_redis)

        result1 = RenderResult(html="<p>first</p>", metadata={"key1": "value1"})
        result2 = RenderResult(html="<p>second</p>", metadata={"key2": "value2"})

        await backend.set("key1", result1)
        await backend.set("key2", result2)

        # set이 두 번 호출되었는지 확인
        assert mock_redis.set.call_count == 2

        # 각 호출의 키를 확인
        calls = mock_redis.set.call_args_list
        assert calls[0][0][0] == "render_cache:key1"
        assert calls[1][0][0] == "render_cache:key2"

    @pytest.mark.asyncio
    async def test_delete_one_key_preserves_others(self, mock_redis):
        """한 키를 삭제해도 다른 키는 유지된다."""
        backend = RedisCacheBackend(mock_redis)

        await backend.delete("key1")
        await backend.delete("key2")

        # delete가 두 번 호출되었는지 확인
        assert mock_redis.delete.call_count == 2

        calls = mock_redis.delete.call_args_list
        assert calls[0][0][0] == "render_cache:key1"
        assert calls[1][0][0] == "render_cache:key2"
