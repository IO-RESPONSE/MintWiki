"""한국어 텍스트 정규화 자리표시자 테스트."""
import unicodedata

from modules.search.normalization import normalize_korean_text


class TestNormalizeKoreanText:
    """normalize_korean_text 테스트."""

    def test_returns_unchanged_for_already_composed_text(self):
        """이미 완성형 음절로 구성된 문자열은 그대로 반환한다."""
        assert normalize_korean_text("위키 엔진") == "위키 엔진"

    def test_composes_decomposed_hangul_jamo(self):
        """자모가 분리된 한글을 완성형 음절로 합친다."""
        decomposed = unicodedata.normalize("NFD", "한달")
        assert normalize_korean_text(decomposed) == "한달"

    def test_leaves_non_korean_text_unchanged(self):
        """한국어가 아닌 텍스트는 그대로 반환한다."""
        assert normalize_korean_text("Hello World") == "Hello World"

    def test_empty_string_returns_empty_string(self):
        """빈 문자열은 빈 문자열을 반환한다."""
        assert normalize_korean_text("") == ""
