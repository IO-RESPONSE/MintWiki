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


class TestNormalizeKoreanTextNoOpBaseline:
    """NFC 정규화 외에는 아무 것도 하지 않는 현재 자리표시자 동작을 고정한다.

    조사 제거, 초성 검색, 대소문자 처리 등 실질적인 한국어 형태소 분석은
    아직 구현되지 않았다. 이 테스트들은 그런 기능이 아직 없다는 기준선
    (baseline)을 명시적으로 검증하여, 이후 실제 정규화 로직이 추가될 때
    의도한 동작 변화인지 회귀인지 구분할 수 있게 한다.
    """

    def test_is_idempotent(self):
        """이미 정규화된 텍스트를 다시 정규화해도 결과가 같다."""
        once = normalize_korean_text("한글 자모 결합 테스트")
        twice = normalize_korean_text(once)
        assert once == twice

    def test_does_not_strip_particles(self):
        """조사(을/를/이/가 등)를 제거하지 않는다."""
        assert normalize_korean_text("위키를") == "위키를"
        assert normalize_korean_text("엔진이") == "엔진이"

    def test_does_not_trim_surrounding_whitespace(self):
        """앞뒤 공백을 제거하지 않는다."""
        assert normalize_korean_text("  위키 엔진  ") == "  위키 엔진  "

    def test_does_not_change_case_of_latin_text(self):
        """영문 대소문자를 변경하지 않는다."""
        assert normalize_korean_text("Wiki Engine") == "Wiki Engine"

    def test_preserves_punctuation_and_digits(self):
        """구두점과 숫자를 그대로 유지한다."""
        assert normalize_korean_text("문서 3번, 확인!") == "문서 3번, 확인!"
