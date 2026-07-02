"""렌더 캐시 무효화 경로 테스트."""
import pytest

from modules.cache import (
    invalidate_render_cache,
    InMemoryCacheBackend,
    read_render_cache,
    write_render_cache,
)
from modules.render.model import RenderResult


class TestInvalidateRenderCache:
    """렌더 캐시 무효화 경로 기본 기능 테스트."""

    @pytest.mark.asyncio
    async def test_invalidate_cache_removes_entry(self):
        """캐시 항목을 삭제한다."""
        backend = InMemoryCacheBackend()
        source = "== 제목 ==\n내용"
        result = RenderResult(
            html="<h2>제목</h2><p>내용</p>",
            metadata={"headings": [{"level": 2, "text": "제목", "id": "h-1"}]},
        )

        # 먼저 캐시에 저장
        await write_render_cache(backend, source, result)

        # 캐시가 존재하는지 확인
        cached = await read_render_cache(backend, source)
        assert cached is not None

        # 무효화
        await invalidate_render_cache(backend, source)

        # 무효화 후 캐시가 없는지 확인
        cached = await read_render_cache(backend, source)
        assert cached is None

    @pytest.mark.asyncio
    async def test_invalidate_cache_with_custom_parser_version(self):
        """사용자 정의 파서 버전의 캐시를 무효화할 수 있다."""
        backend = InMemoryCacheBackend()
        source = "테스트 소스"
        parser_version = "2.1.0"
        result = RenderResult(html="<p>결과</p>", metadata={"version": "2.1.0"})

        # 캐시에 저장
        await write_render_cache(backend, source, result, parser_version)

        # 캐시가 존재하는지 확인
        cached = await read_render_cache(backend, source, parser_version)
        assert cached is not None

        # 무효화
        await invalidate_render_cache(backend, source, parser_version)

        # 무효화 후 캐시가 없는지 확인
        cached = await read_render_cache(backend, source, parser_version)
        assert cached is None

    @pytest.mark.asyncio
    async def test_invalidate_cache_only_affects_specified_version(self):
        """특정 파서 버전의 캐시만 무효화한다."""
        backend = InMemoryCacheBackend()
        source = "같은 소스"

        # v1에 저장
        result_v1 = RenderResult(html="<p>v1 결과</p>", metadata={"version": 1})
        await write_render_cache(backend, source, result_v1, "1.0.0")

        # v2에 저장
        result_v2 = RenderResult(html="<p>v2 결과</p>", metadata={"version": 2})
        await write_render_cache(backend, source, result_v2, "2.0.0")

        # v1만 무효화
        await invalidate_render_cache(backend, source, "1.0.0")

        # v1은 삭제, v2는 존재
        read_v1 = await read_render_cache(backend, source, "1.0.0")
        read_v2 = await read_render_cache(backend, source, "2.0.0")

        assert read_v1 is None
        assert read_v2 is not None
        assert read_v2.metadata["version"] == 2

    @pytest.mark.asyncio
    async def test_invalidate_cache_with_default_parser_version(self):
        """기본 파서 버전의 캐시를 무효화할 수 있다."""
        backend = InMemoryCacheBackend()
        source = "기본 버전 테스트"
        result = RenderResult(html="<p>결과</p>", metadata={})

        # 기본 버전으로 저장
        await write_render_cache(backend, source, result)

        # 캐시가 존재하는지 확인
        cached = await read_render_cache(backend, source)
        assert cached is not None

        # 버전을 지정하지 않고 무효화 (기본값: 1.0.0)
        await invalidate_render_cache(backend, source)

        # 무효화 후 캐시가 없는지 확인
        cached = await read_render_cache(backend, source)
        assert cached is None

    @pytest.mark.asyncio
    async def test_invalidate_nonexistent_cache_does_not_error(self):
        """존재하지 않는 캐시를 무효화해도 오류가 발생하지 않는다."""
        backend = InMemoryCacheBackend()
        source = "존재하지 않는 소스"

        # 무효화를 시도해도 오류가 발생하지 않아야 함
        await invalidate_render_cache(backend, source)

        # 캐시가 없는지 확인
        cached = await read_render_cache(backend, source)
        assert cached is None

    @pytest.mark.asyncio
    async def test_invalidate_cache_with_complex_metadata(self):
        """복잡한 메타데이터를 가진 캐시를 무효화할 수 있다."""
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

        # 캐시에 저장
        await write_render_cache(backend, source, result)

        # 캐시가 존재하는지 확인
        cached = await read_render_cache(backend, source)
        assert cached is not None
        assert len(cached.metadata["categories"]) == 2

        # 무효화
        await invalidate_render_cache(backend, source)

        # 무효화 후 캐시가 없는지 확인
        cached = await read_render_cache(backend, source)
        assert cached is None

    @pytest.mark.asyncio
    async def test_invalidate_cache_idempotent(self):
        """캐시 무효화는 멱등성을 가진다."""
        backend = InMemoryCacheBackend()
        source = "멱등성 테스트"
        result = RenderResult(html="<p>결과</p>", metadata={})

        # 캐시에 저장
        await write_render_cache(backend, source, result)

        # 첫 번째 무효화
        await invalidate_render_cache(backend, source)

        # 두 번째 무효화 (캐시가 없는 상태에서)
        await invalidate_render_cache(backend, source)

        # 캐시가 없는지 확인
        cached = await read_render_cache(backend, source)
        assert cached is None

    @pytest.mark.asyncio
    async def test_invalidate_cache_does_not_affect_other_sources(self):
        """특정 소스의 캐시 무효화가 다른 소스에 영향을 주지 않는다."""
        backend = InMemoryCacheBackend()
        source1 = "소스 1"
        source2 = "소스 2"
        result1 = RenderResult(html="<p>결과 1</p>", metadata={"order": 1})
        result2 = RenderResult(html="<p>결과 2</p>", metadata={"order": 2})

        # 두 개의 캐시 항목 저장
        await write_render_cache(backend, source1, result1)
        await write_render_cache(backend, source2, result2)

        # 첫 번째 캐시만 무효화
        await invalidate_render_cache(backend, source1)

        # 첫 번째는 삭제, 두 번째는 존재
        cached1 = await read_render_cache(backend, source1)
        cached2 = await read_render_cache(backend, source2)

        assert cached1 is None
        assert cached2 is not None
        assert cached2.metadata["order"] == 2
