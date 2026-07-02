"""렌더 캐시 키 빌더 테스트."""
import pytest
from modules.cache import build_render_cache_key


class TestBuildRenderCacheKeyBasic:
    """기본 캐시 키 생성 테스트."""

    def test_generates_non_empty_key(self):
        """캐시 키를 생성한다."""
        key = build_render_cache_key("test content", "1.0.0")
        assert key
        assert isinstance(key, str)

    def test_key_format(self):
        """캐시 키가 올바른 형식이다."""
        key = build_render_cache_key("test content", "1.0.0")
        assert key.startswith("render:v")
        assert ":" in key

    def test_key_includes_parser_version(self):
        """캐시 키에 파서 버전이 포함된다."""
        version = "1.2.3"
        key = build_render_cache_key("test content", version)
        assert f"v{version}" in key


class TestBuildRenderCacheKeyDeterminism:
    """결정성 테스트."""

    def test_same_input_produces_same_key(self):
        """같은 입력은 같은 키를 생성한다."""
        source = "== 제목 ==\n\n테스트 내용입니다."
        version = "1.0.0"
        key1 = build_render_cache_key(source, version)
        key2 = build_render_cache_key(source, version)
        assert key1 == key2

    def test_multiple_calls_consistent(self):
        """여러 번 호출해도 일관성 있는 키를 생성한다."""
        source = "[[링크]] 및 '''굵은''' 텍스트"
        version = "2.0.0"
        keys = [build_render_cache_key(source, version) for _ in range(5)]
        assert all(key == keys[0] for key in keys)


class TestBuildRenderCacheKeyDifference:
    """다른 입력 구분 테스트."""

    def test_different_sources_produce_different_keys(self):
        """다른 소스는 다른 키를 생성한다."""
        version = "1.0.0"
        key1 = build_render_cache_key("source 1", version)
        key2 = build_render_cache_key("source 2", version)
        assert key1 != key2

    def test_different_parser_versions_produce_different_keys(self):
        """다른 파서 버전은 다른 키를 생성한다."""
        source = "test content"
        key1 = build_render_cache_key(source, "1.0.0")
        key2 = build_render_cache_key(source, "2.0.0")
        assert key1 != key2

    def test_different_content_and_version(self):
        """다른 내용과 버전은 다른 키를 생성한다."""
        key1 = build_render_cache_key("content 1", "1.0.0")
        key2 = build_render_cache_key("content 2", "2.0.0")
        assert key1 != key2


class TestBuildRenderCacheKeyEdgeCases:
    """엣지 케이스 테스트."""

    def test_empty_source(self):
        """빈 소스도 처리한다."""
        key = build_render_cache_key("", "1.0.0")
        assert key
        assert key.startswith("render:v1.0.0:")

    def test_very_long_source(self):
        """매우 긴 소스도 처리한다."""
        long_source = "a" * 10000
        key = build_render_cache_key(long_source, "1.0.0")
        assert key
        assert key.startswith("render:v1.0.0:")

    def test_unicode_source(self):
        """유니코드 소스도 처리한다."""
        source = "한글 문서 テキスト 🎉"
        key = build_render_cache_key(source, "1.0.0")
        assert key
        # 같은 유니코드 입력은 같은 키를 생성해야 한다
        key2 = build_render_cache_key(source, "1.0.0")
        assert key == key2

    def test_special_characters_in_source(self):
        """특수 문자를 포함한 소스도 처리한다."""
        source = "!@#$%^&*()_+-=[]{}|;:',.<>?/\\"
        key = build_render_cache_key(source, "1.0.0")
        assert key
        assert key.startswith("render:v1.0.0:")

    def test_newlines_and_whitespace(self):
        """줄바꿈과 공백을 포함한 소스도 처리한다."""
        source = "line1\n  \nline2\n\tline3"
        key = build_render_cache_key(source, "1.0.0")
        assert key
        # 공백 차이도 다른 해시를 생성해야 한다
        source2 = "line1\nline2\nline3"
        key2 = build_render_cache_key(source2, "1.0.0")
        assert key != key2


class TestBuildRenderCacheKeySensitivity:
    """민감도 테스트."""

    def test_case_sensitive(self):
        """대소문자 차이를 인식한다."""
        key1 = build_render_cache_key("Test", "1.0.0")
        key2 = build_render_cache_key("test", "1.0.0")
        assert key1 != key2

    def test_single_character_difference(self):
        """한 글자 차이도 인식한다."""
        key1 = build_render_cache_key("abc", "1.0.0")
        key2 = build_render_cache_key("abd", "1.0.0")
        assert key1 != key2

    def test_version_string_format(self):
        """버전 문자열 형식도 영향을 미친다."""
        source = "content"
        key1 = build_render_cache_key(source, "1.0.0")
        key2 = build_render_cache_key(source, "1.0")
        key3 = build_render_cache_key(source, "1")
        # 모두 다른 키를 생성해야 한다
        assert key1 != key2
        assert key2 != key3
        assert key1 != key3
