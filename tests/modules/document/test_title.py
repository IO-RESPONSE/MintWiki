"""제목 정규화 테스트."""
import pytest
from modules.document.title import EmptyTitleError, normalize_title


class TestNormalizeTitleTrimming:
    """제목 공백 제거 테스트."""

    def test_trims_leading_spaces(self):
        """앞쪽 공백을 제거한다."""
        assert normalize_title("  hello") == "hello"

    def test_trims_trailing_spaces(self):
        """뒤쪽 공백을 제거한다."""
        assert normalize_title("hello  ") == "hello"

    def test_trims_both_sides(self):
        """양쪽 공백을 모두 제거한다."""
        assert normalize_title("  hello  ") == "hello"

    def test_trims_tabs(self):
        """탭을 제거한다."""
        assert normalize_title("\thello\t") == "hello"

    def test_trims_newlines(self):
        """개행을 제거한다."""
        assert normalize_title("\nhello\n") == "hello"

    def test_trims_mixed_whitespace(self):
        """다양한 공백 문자를 제거한다."""
        assert normalize_title("\n  \thello\t  \n") == "hello"


class TestNormalizeTitleWhitespaceCollapsing:
    """제목 공백 축소 테스트."""

    def test_collapses_double_spaces(self):
        """연속된 공백을 단일 공백으로 축소한다."""
        assert normalize_title("hello  world") == "hello world"

    def test_collapses_triple_spaces(self):
        """3개 이상의 공백을 단일 공백으로 축소한다."""
        assert normalize_title("hello   world") == "hello world"

    def test_collapses_multiple_spaces(self):
        """여러 개의 공백을 단일 공백으로 축소한다."""
        assert normalize_title("a   b   c") == "a b c"

    def test_collapses_tabs(self):
        """탭을 단일 공백으로 축소한다."""
        assert normalize_title("hello\t\tworld") == "hello world"

    def test_collapses_mixed_whitespace_internal(self):
        """다양한 공백 문자를 단일 공백으로 축소한다."""
        assert normalize_title("hello  \t  world") == "hello world"

    def test_collapses_with_trimming(self):
        """공백 축소와 양 끝 제거를 동시에 수행한다."""
        assert normalize_title("  a   b   c  ") == "a b c"


class TestNormalizeTitleEmptyRejection:
    """제목 비어있음 거부 테스트."""

    def test_rejects_empty_string(self):
        """빈 문자열을 거부한다."""
        with pytest.raises(EmptyTitleError) as exc_info:
            normalize_title("")
        assert "제목은 비어있을 수 없습니다" in str(exc_info.value)

    def test_rejects_only_spaces(self):
        """공백만 있는 제목을 거부한다."""
        with pytest.raises(EmptyTitleError) as exc_info:
            normalize_title("   ")
        assert "제목은 비어있을 수 없습니다" in str(exc_info.value)

    def test_rejects_only_tabs(self):
        """탭만 있는 제목을 거부한다."""
        with pytest.raises(EmptyTitleError):
            normalize_title("\t\t\t")

    def test_rejects_only_newlines(self):
        """개행만 있는 제목을 거부한다."""
        with pytest.raises(EmptyTitleError):
            normalize_title("\n\n\n")

    def test_rejects_mixed_whitespace_only(self):
        """공백, 탭, 개행만 있는 제목을 거부한다."""
        with pytest.raises(EmptyTitleError):
            normalize_title("\t\n\t")


class TestNormalizeTitleGeneral:
    """일반적인 제목 정규화 테스트."""

    def test_preserves_normal_title(self):
        """정상적인 제목은 그대로 유지한다."""
        assert normalize_title("My Document Title") == "My Document Title"

    def test_preserves_korean_title(self):
        """한글 제목은 그대로 유지한다."""
        assert normalize_title("한글 제목") == "한글 제목"

    def test_handles_mixed_languages(self):
        """혼합된 언어 제목을 정규화한다."""
        assert normalize_title("  Document 한글 Title  ") == "Document 한글 Title"

    def test_handles_special_characters(self):
        """특수 문자가 있는 제목을 정규화한다."""
        assert normalize_title("  Title: Section  ") == "Title: Section"

    def test_handles_numbers(self):
        """숫자가 있는 제목을 정규화한다."""
        assert normalize_title("  Chapter 3: Introduction  ") == "Chapter 3: Introduction"

    def test_single_character(self):
        """한 글자 제목을 정규화한다."""
        assert normalize_title("  A  ") == "A"
