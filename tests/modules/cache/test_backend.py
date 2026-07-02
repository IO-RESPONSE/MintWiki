"""렌더 캐시 백엔드 테스트."""
import pytest

from modules.cache import InMemoryCacheBackend
from modules.render.model import RenderResult


class TestInMemoryCacheBackendBasic:
    """인메모리 캐시 백엔드 기본 기능 테스트."""

    @pytest.mark.asyncio
    async def test_get_non_existent_key_returns_none(self):
        """없는 키를 조회하면 None을 반환한다."""
        backend = InMemoryCacheBackend()
        result = await backend.get("non_existent_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_and_get(self):
        """캐시에 저장한 렌더 결과를 조회할 수 있다."""
        backend = InMemoryCacheBackend()
        render_result = RenderResult(html="<p>test</p>", metadata={})
        key = "test_key"

        await backend.set(key, render_result)
        retrieved = await backend.get(key)

        assert retrieved is not None
        assert retrieved.html == "<p>test</p>"
        assert retrieved.metadata == {}

    @pytest.mark.asyncio
    async def test_set_overwrites_existing_key(self):
        """같은 키로 다시 저장하면 기존 값이 덮어써진다."""
        backend = InMemoryCacheBackend()
        key = "test_key"

        result1 = RenderResult(html="<p>first</p>", metadata={})
        result2 = RenderResult(html="<p>second</p>", metadata={})

        await backend.set(key, result1)
        await backend.set(key, result2)

        retrieved = await backend.get(key)
        assert retrieved.html == "<p>second</p>"


class TestInMemoryCacheBackendDelete:
    """캐시 삭제 기능 테스트."""

    @pytest.mark.asyncio
    async def test_delete_existing_key(self):
        """캐시에서 저장된 데이터를 삭제할 수 있다."""
        backend = InMemoryCacheBackend()
        key = "test_key"
        render_result = RenderResult(html="<p>test</p>", metadata={})

        await backend.set(key, render_result)
        await backend.delete(key)

        result = await backend.get(key)
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_non_existent_key_does_not_error(self):
        """없는 키를 삭제해도 에러가 발생하지 않는다."""
        backend = InMemoryCacheBackend()
        # 에러가 발생하지 않아야 한다
        await backend.delete("non_existent_key")


class TestInMemoryCacheBackendClear:
    """캐시 전체 삭제 기능 테스트."""

    @pytest.mark.asyncio
    async def test_clear_removes_all_data(self):
        """clear는 모든 캐시 데이터를 삭제한다."""
        backend = InMemoryCacheBackend()

        # 여러 개의 항목을 저장
        for i in range(5):
            result = RenderResult(html=f"<p>{i}</p>", metadata={})
            await backend.set(f"key_{i}", result)

        # 모두 저장되었는지 확인
        for i in range(5):
            result = await backend.get(f"key_{i}")
            assert result is not None

        # clear 실행
        await backend.clear()

        # 모두 삭제되었는지 확인
        for i in range(5):
            result = await backend.get(f"key_{i}")
            assert result is None

    @pytest.mark.asyncio
    async def test_clear_on_empty_cache(self):
        """비어있는 캐시를 clear해도 에러가 발생하지 않는다."""
        backend = InMemoryCacheBackend()
        # 에러가 발생하지 않아야 한다
        await backend.clear()


class TestInMemoryCacheBackendMultipleKeys:
    """여러 키 관리 테스트."""

    @pytest.mark.asyncio
    async def test_multiple_keys_are_independent(self):
        """각 키의 값은 독립적이다."""
        backend = InMemoryCacheBackend()

        result1 = RenderResult(html="<p>first</p>", metadata={"key1": "value1"})
        result2 = RenderResult(html="<p>second</p>", metadata={"key2": "value2"})

        await backend.set("key1", result1)
        await backend.set("key2", result2)

        retrieved1 = await backend.get("key1")
        retrieved2 = await backend.get("key2")

        assert retrieved1.html == "<p>first</p>"
        assert retrieved2.html == "<p>second</p>"
        assert retrieved1.metadata == {"key1": "value1"}
        assert retrieved2.metadata == {"key2": "value2"}

    @pytest.mark.asyncio
    async def test_delete_one_key_preserves_others(self):
        """한 키를 삭제해도 다른 키는 유지된다."""
        backend = InMemoryCacheBackend()

        result1 = RenderResult(html="<p>first</p>", metadata={})
        result2 = RenderResult(html="<p>second</p>", metadata={})

        await backend.set("key1", result1)
        await backend.set("key2", result2)

        await backend.delete("key1")

        assert await backend.get("key1") is None
        assert await backend.get("key2") is not None


class TestInMemoryCacheBackendMetadata:
    """메타데이터 저장 테스트."""

    @pytest.mark.asyncio
    async def test_stores_metadata_correctly(self):
        """메타데이터가 정확하게 저장되고 조회된다."""
        backend = InMemoryCacheBackend()

        metadata = {
            "headings": [{"level": 1, "text": "Title", "id": "heading-1"}],
            "links": ["https://example.com"],
            "categories": ["Category1", "Category2"],
        }
        render_result = RenderResult(html="<p>test</p>", metadata=metadata)

        await backend.set("test_key", render_result)
        retrieved = await backend.get("test_key")

        assert retrieved.metadata == metadata
        assert retrieved.metadata["headings"] == metadata["headings"]
        assert retrieved.metadata["links"] == metadata["links"]
        assert retrieved.metadata["categories"] == metadata["categories"]
