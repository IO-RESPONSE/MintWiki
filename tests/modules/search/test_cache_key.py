"""검색 캐시 키 빌더 테스트."""
from modules.search import SEARCH_INDEX_VERSION, build_search_cache_key


class TestBuildSearchCacheKeyBasic:
    """기본 캐시 키 생성 테스트."""

    def test_generates_non_empty_key(self):
        """캐시 키를 생성한다."""
        key = build_search_cache_key("wiki")
        assert key
        assert isinstance(key, str)

    def test_key_format(self):
        """캐시 키가 올바른 형식이다."""
        key = build_search_cache_key("wiki")
        assert key.startswith("search:v")
        assert ":" in key

    def test_key_includes_index_version_by_default(self):
        """index_version을 지정하지 않으면 SEARCH_INDEX_VERSION이 포함된다."""
        key = build_search_cache_key("wiki")
        assert f"v{SEARCH_INDEX_VERSION}" in key

    def test_key_includes_explicit_index_version(self):
        """index_version을 지정하면 해당 값이 포함된다."""
        key = build_search_cache_key("wiki", index_version="2.0.0")
        assert "v2.0.0" in key


class TestBuildSearchCacheKeyDeterminism:
    """결정성 테스트."""

    def test_same_input_produces_same_key(self):
        """같은 입력은 같은 키를 생성한다."""
        key1 = build_search_cache_key("wiki", limit=10, offset=0)
        key2 = build_search_cache_key("wiki", limit=10, offset=0)
        assert key1 == key2

    def test_multiple_calls_consistent(self):
        """여러 번 호출해도 일관성 있는 키를 생성한다."""
        keys = [build_search_cache_key("한글 검색", limit=5, offset=10) for _ in range(5)]
        assert all(key == keys[0] for key in keys)


class TestBuildSearchCacheKeyDifference:
    """다른 입력 구분 테스트."""

    def test_different_terms_produce_different_keys(self):
        """다른 검색어는 다른 키를 생성한다."""
        key1 = build_search_cache_key("wiki")
        key2 = build_search_cache_key("engine")
        assert key1 != key2

    def test_different_limits_produce_different_keys(self):
        """다른 limit은 다른 키를 생성한다."""
        key1 = build_search_cache_key("wiki", limit=10)
        key2 = build_search_cache_key("wiki", limit=20)
        assert key1 != key2

    def test_different_offsets_produce_different_keys(self):
        """다른 offset은 다른 키를 생성한다."""
        key1 = build_search_cache_key("wiki", offset=0)
        key2 = build_search_cache_key("wiki", offset=10)
        assert key1 != key2

    def test_different_index_versions_produce_different_keys(self):
        """다른 색인 버전은 다른 키를 생성한다."""
        key1 = build_search_cache_key("wiki", index_version="1.0.0")
        key2 = build_search_cache_key("wiki", index_version="2.0.0")
        assert key1 != key2

    def test_no_limit_differs_from_explicit_limit(self):
        """limit을 생략한 경우와 명시적으로 지정한 경우를 구분한다."""
        key1 = build_search_cache_key("wiki")
        key2 = build_search_cache_key("wiki", limit=None)
        key3 = build_search_cache_key("wiki", limit=10)
        assert key1 == key2
        assert key1 != key3


class TestBuildSearchCacheKeyEdgeCases:
    """엣지 케이스 테스트."""

    def test_unicode_term(self):
        """유니코드 검색어도 처리한다."""
        key = build_search_cache_key("한글 문서 テキスト 🎉")
        assert key
        key2 = build_search_cache_key("한글 문서 テキスト 🎉")
        assert key == key2

    def test_case_sensitive(self):
        """대소문자 차이를 인식한다."""
        key1 = build_search_cache_key("Wiki")
        key2 = build_search_cache_key("wiki")
        assert key1 != key2

    def test_defaults_to_zero_offset(self):
        """offset을 지정하지 않으면 0으로 취급한다."""
        key1 = build_search_cache_key("wiki")
        key2 = build_search_cache_key("wiki", offset=0)
        assert key1 == key2
