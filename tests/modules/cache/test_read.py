"""렌더 캐시 읽기 경로 테스트."""
import pytest

from modules.cache import read_render_cache, InMemoryCacheBackend
from modules.render.model import RenderResult


class TestReadRenderCache:
    """렌더 캐시 읽기 경로 기본 기능 테스트."""

    @pytest.mark.asyncio
    async def test_read_cache_miss_returns_none(self):
        """캐시 미스 시 None을 반환한다."""
        backend = InMemoryCacheBackend()

        result = await read_render_cache(backend, "non-existent source")
        assert result is None

    @pytest.mark.asyncio
    async def test_read_cache_returns_stored_result(self):
        """캐시에 저장된 결과를 반환한다."""
        backend = InMemoryCacheBackend()
        source = "== 제목 ==\n내용"
        expected_result = RenderResult(
            html="<h2>제목</h2><p>내용</p>",
            metadata={"headings": [{"level": 2, "text": "제목", "id": "h-1"}]},
        )

        # 백엔드에 직접 데이터를 저장 (이 테스트는 write path 없이 read path만 테스트)
        key = "render:v1.0.0:abc123"  # 간단한 키 사용
        backend.data[key] = expected_result

        # read_render_cache는 기본 파서 버전을 사용하므로, 키 생성 방식에 맞춰야 한다
        # 대신 render_cache를 직접 테스트
        from modules.cache import Cache, build_render_cache_key

        cache = Cache(backend, "1.0.0")
        await cache.set_render_result(source, expected_result)

        result = await read_render_cache(backend, source, "1.0.0")

        assert result is not None
        assert result.html == expected_result.html
        assert result.metadata == expected_result.metadata

    @pytest.mark.asyncio
    async def test_read_cache_with_custom_parser_version(self):
        """사용자 정의 파서 버전을 사용할 수 있다."""
        backend = InMemoryCacheBackend()
        source = "테스트 소스"
        parser_version = "2.1.0"
        result_data = RenderResult(html="<p>결과</p>", metadata={})

        # 캐시에 저장
        from modules.cache import Cache

        cache = Cache(backend, parser_version)
        await cache.set_render_result(source, result_data)

        # read_render_cache로 읽기
        result = await read_render_cache(backend, source, parser_version)

        assert result is not None
        assert result.html == result_data.html

    @pytest.mark.asyncio
    async def test_read_cache_different_versions_isolated(self):
        """다른 파서 버전의 캐시는 독립적이다."""
        backend = InMemoryCacheBackend()
        source = "같은 소스"

        # v1에 저장
        result_v1 = RenderResult(html="<p>v1 결과</p>", metadata={"version": 1})
        from modules.cache import Cache

        cache_v1 = Cache(backend, "1.0.0")
        await cache_v1.set_render_result(source, result_v1)

        # v2에 저장
        result_v2 = RenderResult(html="<p>v2 결과</p>", metadata={"version": 2})
        cache_v2 = Cache(backend, "2.0.0")
        await cache_v2.set_render_result(source, result_v2)

        # 각각 읽기
        read_v1 = await read_render_cache(backend, source, "1.0.0")
        read_v2 = await read_render_cache(backend, source, "2.0.0")

        assert read_v1.metadata["version"] == 1
        assert read_v2.metadata["version"] == 2

    @pytest.mark.asyncio
    async def test_read_cache_with_default_parser_version(self):
        """기본 파서 버전을 사용할 수 있다."""
        backend = InMemoryCacheBackend()
        source = "기본 버전 테스트"
        result_data = RenderResult(html="<p>결과</p>", metadata={})

        # 캐시에 저장 (기본 버전)
        from modules.cache import Cache

        cache = Cache(backend)  # 기본 버전 "1.0.0"
        await cache.set_render_result(source, result_data)

        # read_render_cache로 읽기 (버전 지정 안 함 = 기본값 사용)
        result = await read_render_cache(backend, source)

        assert result is not None
        assert result.html == result_data.html

    @pytest.mark.asyncio
    async def test_read_cache_with_complex_metadata(self):
        """복잡한 메타데이터를 읽을 수 있다."""
        backend = InMemoryCacheBackend()
        source = "[[내부 링크]] '''굵은''' 텍스트"
        metadata = {
            "headings": [
                {"level": 1, "text": "제목", "id": "h-1"},
            ],
            "links": ["내부 링크"],
            "categories": ["분류1", "분류2"],
        }
        result_data = RenderResult(html="<h1>제목</h1>...", metadata=metadata)

        # 캐시에 저장
        from modules.cache import Cache

        cache = Cache(backend, "1.0.0")
        await cache.set_render_result(source, result_data)

        # 읽기
        result = await read_render_cache(backend, source, "1.0.0")

        assert result.metadata["links"] == ["내부 링크"]
        assert len(result.metadata["categories"]) == 2
