"""렌더 캐시 히트 경로 통합 테스트."""
import asyncio
import pytest

from modules.cache import (
    Cache,
    InMemoryCacheBackend,
    read_render_cache,
    write_render_cache,
)
from modules.render.model import RenderResult


class TestRenderCacheHitPath:
    """렌더 캐시 히트 시나리오 테스트."""

    @pytest.mark.asyncio
    async def test_direct_cache_hit_after_populate(self):
        """캐시에 데이터가 있을 때 직접 히트하는 경우를 테스트한다."""
        backend = InMemoryCacheBackend()
        source = "== 제목 ==\n내용"
        rendered_result = RenderResult(
            html="<h2>제목</h2><p>내용</p>",
            metadata={"headings": [{"level": 2, "text": "제목", "id": "h-1"}]},
        )

        # 1. 캐시에 먼저 데이터 저장
        cache = Cache(backend)
        await cache.set_render_result(source, rendered_result)

        # 2. 캐시 히트: 저장된 결과를 반환한다
        cached_result = await cache.get_render_result(source)
        assert cached_result is not None
        assert cached_result.html == rendered_result.html
        assert cached_result.metadata == rendered_result.metadata

    @pytest.mark.asyncio
    async def test_cache_hit_with_read_write_helpers(self):
        """read/write 헬퍼 함수를 사용한 캐시 히트를 테스트한다."""
        backend = InMemoryCacheBackend()
        source = "테스트 소스"
        rendered = RenderResult(html="<p>렌더링된 결과</p>", metadata={})

        # 1. 캐시에 저장
        await write_render_cache(backend, source, rendered)

        # 2. 캐시 히트
        cached = await read_render_cache(backend, source)
        assert cached is not None
        assert cached.html == rendered.html
        assert cached.metadata == rendered.metadata

    @pytest.mark.asyncio
    async def test_multiple_cache_hits_same_source(self):
        """같은 소스에 대해 여러 번 히트하는 경우를 테스트한다."""
        backend = InMemoryCacheBackend()
        source = "반복 조회"
        result = RenderResult(html="<p>결과</p>", metadata={"id": "test-1"})

        # 1. 캐시에 저장
        await write_render_cache(backend, source, result)

        # 2. 같은 소스로 반복 조회
        for i in range(10):
            cached = await read_render_cache(backend, source)
            assert cached is not None, f"반복 {i}에서 히트해야 한다"
            assert cached.html == result.html
            assert cached.metadata["id"] == "test-1"

    @pytest.mark.asyncio
    async def test_cache_hit_different_sources_independent(self):
        """서로 다른 소스의 캐시 히트는 독립적이다."""
        backend = InMemoryCacheBackend()
        source1 = "소스 1"
        source2 = "소스 2"

        # 1. 두 소스 모두 렌더링하고 저장
        result1 = RenderResult(html="<p>결과 1</p>", metadata={"id": 1})
        result2 = RenderResult(html="<p>결과 2</p>", metadata={"id": 2})
        await write_render_cache(backend, source1, result1)
        await write_render_cache(backend, source2, result2)

        # 2. 각각 히트하고 올바른 데이터를 반환한다
        cached1 = await read_render_cache(backend, source1)
        cached2 = await read_render_cache(backend, source2)

        assert cached1 is not None
        assert cached1.metadata["id"] == 1
        assert cached2 is not None
        assert cached2.metadata["id"] == 2

    @pytest.mark.asyncio
    async def test_cache_hit_with_parser_versions(self):
        """다른 파서 버전의 캐시는 독립적으로 히트한다."""
        backend = InMemoryCacheBackend()
        source = "같은 소스"

        # 1. v1.0.0과 v2.0.0의 렌더링 결과를 각각 저장
        v1_result = RenderResult(html="<p>v1 결과</p>", metadata={"version": "1.0.0"})
        v2_result = RenderResult(html="<p>v2 결과</p>", metadata={"version": "2.0.0"})
        await write_render_cache(backend, source, v1_result, "1.0.0")
        await write_render_cache(backend, source, v2_result, "2.0.0")

        # 2. 각 버전별로 히트하고 올바른 데이터를 반환한다
        v1_cached = await read_render_cache(backend, source, "1.0.0")
        v2_cached = await read_render_cache(backend, source, "2.0.0")

        assert v1_cached is not None
        assert v1_cached.metadata["version"] == "1.0.0"
        assert v2_cached is not None
        assert v2_cached.metadata["version"] == "2.0.0"

    @pytest.mark.asyncio
    async def test_cache_hit_with_complex_metadata(self):
        """복잡한 메타데이터를 포함한 캐시 히트를 테스트한다."""
        backend = InMemoryCacheBackend()
        source = "[[내부 링크]] '''굵은''' 텍스트 <ref>각주</ref>"

        # 1. 복잡한 메타데이터와 함께 저장
        complex_metadata = {
            "headings": [
                {"level": 1, "text": "제목 1", "id": "h-1"},
                {"level": 2, "text": "부제목", "id": "h-2"},
            ],
            "links": [
                {"text": "내부 링크", "target": "내부_링크", "type": "internal"}
            ],
            "categories": ["분류1", "분류2"],
            "footnotes": [
                {"id": "fn-1", "text": "각주 내용"}
            ],
        }
        result = RenderResult(html="<h1>...</h1>", metadata=complex_metadata)
        await write_render_cache(backend, source, result)

        # 2. 캐시 히트: 복잡한 메타데이터가 올바르게 반환된다
        cached = await read_render_cache(backend, source)
        assert cached is not None
        assert len(cached.metadata["headings"]) == 2
        assert cached.metadata["links"][0]["text"] == "내부 링크"
        assert len(cached.metadata["categories"]) == 2
        assert len(cached.metadata["footnotes"]) == 1

    @pytest.mark.asyncio
    async def test_cache_hit_empty_source(self):
        """빈 소스에 대한 캐시 히트를 처리한다."""
        backend = InMemoryCacheBackend()
        empty_source = ""

        # 1. 빈 소스도 렌더링할 수 있다 (빈 문서)
        result = RenderResult(html="", metadata={})
        await write_render_cache(backend, empty_source, result)

        # 2. 빈 소스도 캐시에서 조회될 수 있다
        cached = await read_render_cache(backend, empty_source)
        assert cached is not None
        assert cached.html == ""

    @pytest.mark.asyncio
    async def test_cache_hit_with_cache_class(self):
        """Cache 클래스를 사용한 완전한 히트 경로를 테스트한다."""
        backend = InMemoryCacheBackend()
        cache = Cache(backend, parser_version="1.0.0")
        source = "캐시 클래스 테스트"

        # 1. 여러 단계의 렌더링 결과 저장
        results = []
        for i in range(3):
            result = RenderResult(
                html=f"<p>결과 {i}</p>",
                metadata={"index": i}
            )
            results.append(result)
            await cache.set_render_result(f"{source}-{i}", result)

        # 2. 각각 히트하고 올바른 값을 반환한다
        for i in range(3):
            cached = await cache.get_render_result(f"{source}-{i}")
            assert cached is not None
            assert cached.metadata["index"] == i

    @pytest.mark.asyncio
    async def test_cache_hit_unicode_content(self):
        """유니코드 콘텐츠를 포함한 캐시 히트를 테스트한다."""
        backend = InMemoryCacheBackend()

        # 다양한 유니코드 텍스트
        unicode_sources = [
            "한글 테스트",
            "日本語のテスト",
            "العربية اختبار",
            "😀🎉🚀",
            "ñoño español",
        ]

        # 1. 모든 유니코드 소스를 렌더링하고 저장
        for source in unicode_sources:
            result = RenderResult(
                html=f"<p>{source}</p>",
                metadata={"text": source}
            )
            await write_render_cache(backend, source, result)

        # 2. 히트: 유니코드가 올바르게 저장되고 반환된다
        for source in unicode_sources:
            cached = await read_render_cache(backend, source)
            assert cached is not None
            assert cached.metadata["text"] == source

    @pytest.mark.asyncio
    async def test_concurrent_cache_hits(self):
        """동시에 여러 캐시 히트가 발생하는 경우를 테스트한다."""
        backend = InMemoryCacheBackend()
        cache = Cache(backend)

        # 1. 캐시에 데이터 저장
        sources = [f"source-{i}" for i in range(5)]
        for i, source in enumerate(sources):
            result = RenderResult(
                html=f"<p>결과 {i}</p>",
                metadata={"index": i}
            )
            await cache.set_render_result(source, result)

        # 2. 동시에 여러 히트 수행
        async def fetch_result(source, index):
            cached = await cache.get_render_result(source)
            assert cached is not None
            assert cached.metadata["index"] == index
            return cached

        results = await asyncio.gather(*[
            fetch_result(source, i)
            for i, source in enumerate(sources)
        ])

        assert len(results) == 5
        for i, result in enumerate(results):
            assert result.metadata["index"] == i

    @pytest.mark.asyncio
    async def test_cache_hit_after_invalidation_and_repopulate(self):
        """캐시 무효화 후 재저장한 데이터에 대한 히트를 테스트한다."""
        backend = InMemoryCacheBackend()
        source = "재저장 테스트"
        cache = Cache(backend)

        # 1. 첫 번째 데이터 저장
        result1 = RenderResult(html="<p>버전 1</p>", metadata={"version": 1})
        await cache.set_render_result(source, result1)

        # 2. 히트 확인
        cached1 = await cache.get_render_result(source)
        assert cached1 is not None
        assert cached1.metadata["version"] == 1

        # 3. 캐시 삭제
        await cache.delete_render_cache(source)

        # 4. 새 데이터 저장
        result2 = RenderResult(html="<p>버전 2</p>", metadata={"version": 2})
        await cache.set_render_result(source, result2)

        # 5. 새 데이터에 대한 히트 확인
        cached2 = await cache.get_render_result(source)
        assert cached2 is not None
        assert cached2.metadata["version"] == 2

    @pytest.mark.asyncio
    async def test_cache_hit_large_metadata(self):
        """큰 메타데이터를 포함한 캐시 히트를 테스트한다."""
        backend = InMemoryCacheBackend()
        source = "큰 메타데이터 테스트"

        # 1. 많은 제목과 링크가 있는 큰 메타데이터 준비
        large_metadata = {
            "headings": [
                {"level": i % 6 + 1, "text": f"제목 {i}", "id": f"h-{i}"}
                for i in range(100)
            ],
            "links": [
                {"text": f"링크 {i}", "target": f"page-{i}", "type": "internal"}
                for i in range(50)
            ],
            "categories": [f"분류-{i}" for i in range(30)],
        }
        result = RenderResult(html="<h1>...</h1>" * 100, metadata=large_metadata)

        # 2. 캐시에 저장
        await write_render_cache(backend, source, result)

        # 3. 히트: 큰 메타데이터가 올바르게 저장되고 반환된다
        cached = await read_render_cache(backend, source)
        assert cached is not None
        assert len(cached.metadata["headings"]) == 100
        assert len(cached.metadata["links"]) == 50
        assert len(cached.metadata["categories"]) == 30

    @pytest.mark.asyncio
    async def test_cache_hit_preserves_data_structure(self):
        """캐시 히트가 원본 데이터 구조를 보존하는지 테스트한다."""
        backend = InMemoryCacheBackend()
        source = "구조 보존 테스트"

        # 1. 다양한 타입의 메타데이터 준비
        metadata = {
            "string": "텍스트",
            "number": 42,
            "float": 3.14,
            "bool": True,
            "list": [1, 2, 3],
            "nested": {
                "a": "value",
                "b": [{"x": 1}, {"x": 2}],
            },
        }
        result = RenderResult(html="<p>테스트</p>", metadata=metadata)

        # 2. 캐시에 저장
        await write_render_cache(backend, source, result)

        # 3. 히트 후 구조 확인
        cached = await read_render_cache(backend, source)
        assert cached is not None
        assert cached.metadata["string"] == "텍스트"
        assert cached.metadata["number"] == 42
        assert cached.metadata["float"] == 3.14
        assert cached.metadata["bool"] is True
        assert cached.metadata["list"] == [1, 2, 3]
        assert cached.metadata["nested"]["a"] == "value"
        assert len(cached.metadata["nested"]["b"]) == 2

    @pytest.mark.asyncio
    async def test_cache_hit_html_integrity(self):
        """캐시 히트가 HTML 콘텐츠의 무결성을 보존하는지 테스트한다."""
        backend = InMemoryCacheBackend()
        source = "HTML 무결성 테스트"

        # 1. 복잡한 HTML 준비
        complex_html = """
        <div class="content">
            <h1 id="title">제목</h1>
            <p>첫 번째 문단</p>
            <ul>
                <li>항목 1</li>
                <li>항목 2</li>
            </ul>
            <table>
                <tr><td>셀 1</td><td>셀 2</td></tr>
            </table>
            <code class="lang-python">print("Hello")</code>
        </div>
        """
        result = RenderResult(html=complex_html, metadata={})

        # 2. 캐시에 저장
        await write_render_cache(backend, source, result)

        # 3. 히트 후 HTML이 완전히 보존되는지 확인
        cached = await read_render_cache(backend, source)
        assert cached is not None
        assert cached.html == complex_html
