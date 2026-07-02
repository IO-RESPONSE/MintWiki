"""렌더 캐시 서비스 테스트."""
import pytest

from modules.cache import Cache, InMemoryCacheBackend, build_render_cache_key
from modules.render.model import RenderResult


class TestCacheBasic:
    """캐시 서비스 기본 기능 테스트."""

    @pytest.mark.asyncio
    async def test_get_non_existent_returns_none(self):
        """없는 캐시를 조회하면 None을 반환한다."""
        backend = InMemoryCacheBackend()
        cache = Cache(backend)

        result = await cache.get_render_result("non existent source")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_and_get_render_result(self):
        """캐시에 저장한 렌더 결과를 조회할 수 있다."""
        backend = InMemoryCacheBackend()
        cache = Cache(backend)

        source = "== 제목 ==\n테스트 내용"
        render_result = RenderResult(html="<h2>제목</h2><p>테스트 내용</p>", metadata={"headings": []})

        await cache.set_render_result(source, render_result)
        retrieved = await cache.get_render_result(source)

        assert retrieved is not None
        assert retrieved.html == render_result.html
        assert retrieved.metadata == render_result.metadata

    @pytest.mark.asyncio
    async def test_same_source_returns_cached_result(self):
        """같은 소스에 대해 캐시된 결과를 반환한다."""
        backend = InMemoryCacheBackend()
        cache = Cache(backend)

        source = "테스트 소스"
        result1 = RenderResult(html="<p>렌더링 결과 1</p>", metadata={})

        await cache.set_render_result(source, result1)

        # 같은 소스로 다시 조회
        retrieved = await cache.get_render_result(source)
        assert retrieved is result1


class TestCacheKeyGeneration:
    """캐시 키 생성 및 격리 테스트."""

    @pytest.mark.asyncio
    async def test_different_sources_use_different_keys(self):
        """다른 소스는 서로 다른 캐시 키를 사용한다."""
        backend = InMemoryCacheBackend()
        cache = Cache(backend)

        source1 = "소스 1"
        source2 = "소스 2"

        result1 = RenderResult(html="<p>결과 1</p>", metadata={"id": "1"})
        result2 = RenderResult(html="<p>결과 2</p>", metadata={"id": "2"})

        await cache.set_render_result(source1, result1)
        await cache.set_render_result(source2, result2)

        retrieved1 = await cache.get_render_result(source1)
        retrieved2 = await cache.get_render_result(source2)

        assert retrieved1.metadata["id"] == "1"
        assert retrieved2.metadata["id"] == "2"

    @pytest.mark.asyncio
    async def test_parser_version_affects_cache_key(self):
        """파서 버전이 다르면 서로 다른 캐시를 사용한다."""
        backend1 = InMemoryCacheBackend()
        backend2 = InMemoryCacheBackend()

        cache_v1 = Cache(backend1, parser_version="1.0.0")
        cache_v2 = Cache(backend2, parser_version="2.0.0")

        source = "테스트"
        result1 = RenderResult(html="<p>v1 결과</p>", metadata={})
        result2 = RenderResult(html="<p>v2 결과</p>", metadata={})

        await cache_v1.set_render_result(source, result1)
        await cache_v2.set_render_result(source, result2)

        # 각 캐시에서 조회하면 저장된 결과를 반환해야 한다
        assert (await cache_v1.get_render_result(source)).html == "<p>v1 결과</p>"
        assert (await cache_v2.get_render_result(source)).html == "<p>v2 결과</p>"


class TestCacheDelete:
    """캐시 삭제 기능 테스트."""

    @pytest.mark.asyncio
    async def test_delete_removes_cached_result(self):
        """캐시된 결과를 삭제할 수 있다."""
        backend = InMemoryCacheBackend()
        cache = Cache(backend)

        source = "삭제할 소스"
        result = RenderResult(html="<p>삭제될 결과</p>", metadata={})

        await cache.set_render_result(source, result)
        assert await cache.get_render_result(source) is not None

        await cache.delete_render_cache(source)
        assert await cache.get_render_result(source) is None

    @pytest.mark.asyncio
    async def test_delete_non_existent_does_not_error(self):
        """없는 캐시를 삭제해도 에러가 발생하지 않는다."""
        backend = InMemoryCacheBackend()
        cache = Cache(backend)

        # 에러가 발생하지 않아야 한다
        await cache.delete_render_cache("non existent")


class TestCacheClear:
    """캐시 전체 삭제 기능 테스트."""

    @pytest.mark.asyncio
    async def test_clear_all_removes_all_data(self):
        """전체 캐시를 삭제한다."""
        backend = InMemoryCacheBackend()
        cache = Cache(backend)

        # 여러 항목 저장
        sources = ["소스 1", "소스 2", "소스 3"]
        for i, source in enumerate(sources):
            result = RenderResult(html=f"<p>결과 {i}</p>", metadata={})
            await cache.set_render_result(source, result)

        # 모두 저장되었는지 확인
        for source in sources:
            assert await cache.get_render_result(source) is not None

        # 전체 삭제
        await cache.clear_all()

        # 모두 삭제되었는지 확인
        for source in sources:
            assert await cache.get_render_result(source) is None

    @pytest.mark.asyncio
    async def test_clear_all_on_empty_cache(self):
        """비어있는 캐시를 전체 삭제해도 에러가 발생하지 않는다."""
        backend = InMemoryCacheBackend()
        cache = Cache(backend)

        # 에러가 발생하지 않아야 한다
        await cache.clear_all()


class TestCacheIntegration:
    """캐시 통합 기능 테스트."""

    @pytest.mark.asyncio
    async def test_cache_with_complex_metadata(self):
        """복잡한 메타데이터를 저장하고 조회할 수 있다."""
        backend = InMemoryCacheBackend()
        cache = Cache(backend)

        source = "[[내부 링크]] '''굵은''' 텍스트"
        metadata = {
            "headings": [
                {"level": 1, "text": "제목 1", "id": "heading-1"},
                {"level": 2, "text": "제목 2", "id": "heading-2"},
            ],
            "links": ["내부 링크"],
            "categories": ["분류1", "분류2"],
            "footnotes": [
                {"id": "fn-1", "text": "각주 내용"}
            ],
        }
        result = RenderResult(html="<h1>제목 1</h1>...", metadata=metadata)

        await cache.set_render_result(source, result)
        retrieved = await cache.get_render_result(source)

        assert retrieved.metadata == metadata
        assert len(retrieved.metadata["headings"]) == 2
        assert len(retrieved.metadata["links"]) == 1

    @pytest.mark.asyncio
    async def test_cache_overwrites_existing_result(self):
        """같은 소스에 대해 캐시를 덮어쓸 수 있다."""
        backend = InMemoryCacheBackend()
        cache = Cache(backend)

        source = "업데이트될 소스"

        result1 = RenderResult(html="<p>초기 결과</p>", metadata={"version": 1})
        result2 = RenderResult(html="<p>업데이트된 결과</p>", metadata={"version": 2})

        await cache.set_render_result(source, result1)
        assert (await cache.get_render_result(source)).metadata["version"] == 1

        await cache.set_render_result(source, result2)
        assert (await cache.get_render_result(source)).metadata["version"] == 2

    @pytest.mark.asyncio
    async def test_cache_with_default_parser_version(self):
        """기본 파서 버전을 사용한다."""
        backend = InMemoryCacheBackend()
        cache = Cache(backend)  # 기본 버전 "1.0.0"

        source = "테스트"
        result = RenderResult(html="<p>결과</p>", metadata={})

        await cache.set_render_result(source, result)
        retrieved = await cache.get_render_result(source)

        # 같은 버전으로 조회되어야 한다
        assert retrieved is not None
        assert retrieved.html == result.html

    @pytest.mark.asyncio
    async def test_cache_with_custom_parser_version(self):
        """사용자 정의 파서 버전을 사용할 수 있다."""
        backend = InMemoryCacheBackend()
        cache = Cache(backend, parser_version="3.2.1")

        source = "테스트"
        result = RenderResult(html="<p>결과</p>", metadata={})

        await cache.set_render_result(source, result)

        # 백엔드에 실제로 저장된 키를 확인
        expected_key = build_render_cache_key(source, "3.2.1")
        backend_result = await backend.get(expected_key)

        assert backend_result is not None
        assert backend_result.html == result.html
