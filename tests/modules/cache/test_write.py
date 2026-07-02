"""렌더 캐시 쓰기 경로 테스트."""
import pytest

from modules.cache import write_render_cache, InMemoryCacheBackend, read_render_cache
from modules.render.model import RenderResult


class TestWriteRenderCache:
    """렌더 캐시 쓰기 경로 기본 기능 테스트."""

    @pytest.mark.asyncio
    async def test_write_cache_stores_result(self):
        """결과를 캐시에 저장한다."""
        backend = InMemoryCacheBackend()
        source = "== 제목 ==\n내용"
        result = RenderResult(
            html="<h2>제목</h2><p>내용</p>",
            metadata={"headings": [{"level": 2, "text": "제목", "id": "h-1"}]},
        )

        await write_render_cache(backend, source, result)

        # 저장된 결과를 읽기로 확인
        read_result = await read_render_cache(backend, source, "1.0.0")
        assert read_result is not None
        assert read_result.html == result.html
        assert read_result.metadata == result.metadata

    @pytest.mark.asyncio
    async def test_write_cache_with_custom_parser_version(self):
        """사용자 정의 파서 버전으로 저장할 수 있다."""
        backend = InMemoryCacheBackend()
        source = "테스트 소스"
        parser_version = "2.1.0"
        result = RenderResult(html="<p>결과</p>", metadata={"version": "2.1.0"})

        await write_render_cache(backend, source, result, parser_version)

        # 저장된 결과를 읽기로 확인
        read_result = await read_render_cache(backend, source, parser_version)
        assert read_result is not None
        assert read_result.html == result.html

    @pytest.mark.asyncio
    async def test_write_cache_different_versions_isolated(self):
        """다른 파서 버전으로 저장한 캐시는 독립적이다."""
        backend = InMemoryCacheBackend()
        source = "같은 소스"

        # v1에 저장
        result_v1 = RenderResult(html="<p>v1 결과</p>", metadata={"version": 1})
        await write_render_cache(backend, source, result_v1, "1.0.0")

        # v2에 저장
        result_v2 = RenderResult(html="<p>v2 결과</p>", metadata={"version": 2})
        await write_render_cache(backend, source, result_v2, "2.0.0")

        # 각각 읽기로 확인
        read_v1 = await read_render_cache(backend, source, "1.0.0")
        read_v2 = await read_render_cache(backend, source, "2.0.0")

        assert read_v1.metadata["version"] == 1
        assert read_v2.metadata["version"] == 2

    @pytest.mark.asyncio
    async def test_write_cache_with_default_parser_version(self):
        """기본 파서 버전으로 저장할 수 있다."""
        backend = InMemoryCacheBackend()
        source = "기본 버전 테스트"
        result = RenderResult(html="<p>결과</p>", metadata={})

        # 파서 버전을 지정하지 않고 저장 (기본값: 1.0.0)
        await write_render_cache(backend, source, result)

        # 기본 버전으로 읽기로 확인
        read_result = await read_render_cache(backend, source)
        assert read_result is not None
        assert read_result.html == result.html

    @pytest.mark.asyncio
    async def test_write_cache_with_complex_metadata(self):
        """복잡한 메타데이터를 저장할 수 있다."""
        backend = InMemoryCacheBackend()
        source = "[[내부 링크]] '''굵은''' 텍스트"
        metadata = {
            "headings": [
                {"level": 1, "text": "제목", "id": "h-1"},
            ],
            "links": ["내부 링크"],
            "categories": ["분류1", "분류2"],
        }
        result = RenderResult(html="<h1>제목</h1>...", metadata=metadata)

        await write_render_cache(backend, source, result, "1.0.0")

        # 저장된 결과를 읽기로 확인
        read_result = await read_render_cache(backend, source, "1.0.0")
        assert read_result.metadata["links"] == ["내부 링크"]
        assert len(read_result.metadata["categories"]) == 2

    @pytest.mark.asyncio
    async def test_write_cache_overwrites_existing(self):
        """기존 캐시를 덮어쓸 수 있다."""
        backend = InMemoryCacheBackend()
        source = "업데이트 테스트"

        # 첫 번째 저장
        result_v1 = RenderResult(html="<p>첫 번째</p>", metadata={"order": 1})
        await write_render_cache(backend, source, result_v1, "1.0.0")

        # 두 번째 저장 (덮어쓰기)
        result_v2 = RenderResult(html="<p>두 번째</p>", metadata={"order": 2})
        await write_render_cache(backend, source, result_v2, "1.0.0")

        # 두 번째 결과만 존재하는지 확인
        read_result = await read_render_cache(backend, source, "1.0.0")
        assert read_result.metadata["order"] == 2
        assert read_result.html == "<p>두 번째</p>"
