"""렌더 캐시 미스 경로 통합 테스트."""
import pytest

from modules.cache import (
    Cache,
    InMemoryCacheBackend,
    read_render_cache,
    write_render_cache,
)
from modules.render.model import RenderResult


class TestRenderCacheMissPath:
    """렌더 캐시 미스 시나리오 테스트."""

    @pytest.mark.asyncio
    async def test_cache_miss_then_render_and_store(self):
        """캐시 미스 후 렌더링하고 저장하는 흐름을 테스트한다."""
        backend = InMemoryCacheBackend()
        source = "== 제목 ==\n내용"

        # 1. 캐시 미스: 캐시에서 조회하면 None을 반환한다
        cache = Cache(backend)
        result = await cache.get_render_result(source)
        assert result is None, "캐시가 없을 때 None을 반환해야 한다"

        # 2. 렌더링: 결과를 생성한다 (실제로는 렌더러가 하지만 여기선 시뮬레이션)
        rendered_result = RenderResult(
            html="<h2>제목</h2><p>내용</p>",
            metadata={"headings": [{"level": 2, "text": "제목", "id": "h-1"}]},
        )

        # 3. 캐시에 저장
        await cache.set_render_result(source, rendered_result)

        # 4. 캐시 히트: 같은 소스로 조회하면 캐시된 결과를 반환한다
        cached_result = await cache.get_render_result(source)
        assert cached_result is not None, "캐시된 결과를 반환해야 한다"
        assert cached_result.html == rendered_result.html
        assert cached_result.metadata == rendered_result.metadata

    @pytest.mark.asyncio
    async def test_cache_miss_with_read_write_helpers(self):
        """read/write 헬퍼 함수를 사용한 캐시 미스 경로를 테스트한다."""
        backend = InMemoryCacheBackend()
        source = "테스트 소스"

        # 1. 캐시 미스
        miss_result = await read_render_cache(backend, source)
        assert miss_result is None

        # 2. 렌더링 및 캐시 저장
        rendered = RenderResult(html="<p>렌더링된 결과</p>", metadata={})
        await write_render_cache(backend, source, rendered)

        # 3. 캐시 히트
        cached = await read_render_cache(backend, source)
        assert cached is not None
        assert cached.html == rendered.html

    @pytest.mark.asyncio
    async def test_multiple_cache_misses_independent(self):
        """서로 다른 소스의 캐시 미스는 독립적이다."""
        backend = InMemoryCacheBackend()
        source1 = "소스 1"
        source2 = "소스 2"

        # 1. 두 소스 모두 캐시 미스
        assert await read_render_cache(backend, source1) is None
        assert await read_render_cache(backend, source2) is None

        # 2. 첫 번째 소스만 렌더링하고 캐시에 저장
        result1 = RenderResult(html="<p>결과 1</p>", metadata={"id": 1})
        await write_render_cache(backend, source1, result1)

        # 3. 첫 번째는 히트, 두 번째는 여전히 미스
        cached1 = await read_render_cache(backend, source1)
        cached2 = await read_render_cache(backend, source2)

        assert cached1 is not None
        assert cached1.metadata["id"] == 1
        assert cached2 is None

        # 4. 두 번째 소스도 렌더링하고 저장
        result2 = RenderResult(html="<p>결과 2</p>", metadata={"id": 2})
        await write_render_cache(backend, source2, result2)

        # 5. 이제 둘 다 히트
        cached1_again = await read_render_cache(backend, source1)
        cached2_again = await read_render_cache(backend, source2)

        assert cached1_again.metadata["id"] == 1
        assert cached2_again.metadata["id"] == 2

    @pytest.mark.asyncio
    async def test_cache_miss_with_different_parser_versions(self):
        """다른 파서 버전의 캐시 미스는 독립적이다."""
        backend = InMemoryCacheBackend()
        source = "같은 소스"

        # 1. v1.0.0에서 캐시 미스
        v1_miss = await read_render_cache(backend, source, "1.0.0")
        assert v1_miss is None

        # 2. v2.0.0에서도 캐시 미스
        v2_miss = await read_render_cache(backend, source, "2.0.0")
        assert v2_miss is None

        # 3. v1.0.0으로 렌더링하고 저장
        v1_result = RenderResult(html="<p>v1 결과</p>", metadata={"version": "1.0.0"})
        await write_render_cache(backend, source, v1_result, "1.0.0")

        # 4. v1.0.0은 히트, v2.0.0은 여전히 미스
        v1_cached = await read_render_cache(backend, source, "1.0.0")
        v2_still_miss = await read_render_cache(backend, source, "2.0.0")

        assert v1_cached is not None
        assert v1_cached.metadata["version"] == "1.0.0"
        assert v2_still_miss is None

        # 5. v2.0.0으로 렌더링하고 저장
        v2_result = RenderResult(html="<p>v2 결과</p>", metadata={"version": "2.0.0"})
        await write_render_cache(backend, source, v2_result, "2.0.0")

        # 6. 이제 둘 다 히트
        v1_final = await read_render_cache(backend, source, "1.0.0")
        v2_final = await read_render_cache(backend, source, "2.0.0")

        assert v1_final.metadata["version"] == "1.0.0"
        assert v2_final.metadata["version"] == "2.0.0"

    @pytest.mark.asyncio
    async def test_cache_miss_repeated_requests(self):
        """캐시 미스 후 반복되는 요청은 캐시를 사용한다."""
        backend = InMemoryCacheBackend()
        source = "반복 테스트"
        cache = Cache(backend)

        # 1. 첫 번째 미스
        assert await cache.get_render_result(source) is None

        # 2. 렌더링하고 저장
        result = RenderResult(html="<p>결과</p>", metadata={"count": 1})
        await cache.set_render_result(source, result)

        # 3. 반복된 요청들은 모두 같은 캐시된 결과를 반환한다
        for _ in range(5):
            cached = await cache.get_render_result(source)
            assert cached is not None
            assert cached.metadata["count"] == 1

    @pytest.mark.asyncio
    async def test_cache_miss_with_complex_metadata(self):
        """복잡한 메타데이터가 있는 캐시 미스 경로를 테스트한다."""
        backend = InMemoryCacheBackend()
        source = "[[내부 링크]] '''굵은''' 텍스트 <ref>각주</ref>"

        # 1. 캐시 미스
        assert await read_render_cache(backend, source) is None

        # 2. 렌더링하고 복잡한 메타데이터와 함께 저장
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

        # 3. 캐시 히트: 복잡한 메타데이터가 올바르게 저장되고 반환된다
        cached = await read_render_cache(backend, source)
        assert cached is not None
        assert len(cached.metadata["headings"]) == 2
        assert cached.metadata["links"][0]["text"] == "내부 링크"
        assert len(cached.metadata["categories"]) == 2
        assert len(cached.metadata["footnotes"]) == 1

    @pytest.mark.asyncio
    async def test_cache_miss_empty_source(self):
        """빈 소스에 대한 캐시 미스를 처리한다."""
        backend = InMemoryCacheBackend()
        empty_source = ""

        # 1. 빈 소스는 캐시 미스
        assert await read_render_cache(backend, empty_source) is None

        # 2. 빈 소스도 렌더링할 수 있다 (빈 문서)
        result = RenderResult(html="", metadata={})
        await write_render_cache(backend, empty_source, result)

        # 3. 빈 소스도 캐시에 저장되고 조회될 수 있다
        cached = await read_render_cache(backend, empty_source)
        assert cached is not None
        assert cached.html == ""

    @pytest.mark.asyncio
    async def test_cache_miss_then_invalidate(self):
        """캐시 미스 후 데이터를 저장했다가 무효화하는 흐름을 테스트한다."""
        backend = InMemoryCacheBackend()
        source = "무효화 테스트"

        # 1. 초기 미스
        assert await read_render_cache(backend, source) is None

        # 2. 렌더링하고 저장
        result = RenderResult(html="<p>원본</p>", metadata={"version": 1})
        await write_render_cache(backend, source, result)

        # 3. 캐시 히트 확인
        cached = await read_render_cache(backend, source)
        assert cached is not None

        # 4. 캐시 무효화
        from modules.cache import invalidate_render_cache
        await invalidate_render_cache(backend, source)

        # 5. 다시 미스가 된다
        assert await read_render_cache(backend, source) is None

        # 6. 새로운 버전으로 렌더링하고 저장
        new_result = RenderResult(html="<p>업데이트됨</p>", metadata={"version": 2})
        await write_render_cache(backend, source, new_result)

        # 7. 새로운 버전이 캐시된다
        cached = await read_render_cache(backend, source)
        assert cached is not None
        assert cached.metadata["version"] == 2

    @pytest.mark.asyncio
    async def test_cache_miss_path_with_cache_class(self):
        """Cache 클래스를 사용한 완전한 미스 경로를 테스트한다."""
        backend = InMemoryCacheBackend()
        cache = Cache(backend, parser_version="1.0.0")
        source = "캐시 클래스 테스트"

        # 1. 미스
        assert await cache.get_render_result(source) is None

        # 2. 여러 단계의 렌더링 결과 저장
        results = []
        for i in range(3):
            result = RenderResult(
                html=f"<p>결과 {i}</p>",
                metadata={"index": i}
            )
            results.append(result)
            await cache.set_render_result(f"{source}-{i}", result)

        # 3. 각각 히트하고 올바른 값을 반환한다
        for i in range(3):
            cached = await cache.get_render_result(f"{source}-{i}")
            assert cached is not None
            assert cached.metadata["index"] == i

    @pytest.mark.asyncio
    async def test_cache_miss_path_unicode_content(self):
        """유니코드 콘텐츠가 있는 캐시 미스 경로를 테스트한다."""
        backend = InMemoryCacheBackend()

        # 다양한 유니코드 텍스트
        unicode_sources = [
            "한글 테스트",
            "日本語のテスト",
            "العربية اختبار",
            "😀🎉🚀",
            "ñoño español",
        ]

        for source in unicode_sources:
            # 1. 미스
            assert await read_render_cache(backend, source) is None

            # 2. 렌더링 결과 저장
            result = RenderResult(
                html=f"<p>{source}</p>",
                metadata={"text": source}
            )
            await write_render_cache(backend, source, result)

            # 3. 히트: 유니코드가 올바르게 저장되고 반환된다
            cached = await read_render_cache(backend, source)
            assert cached is not None
            assert cached.metadata["text"] == source
