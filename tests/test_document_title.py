import pytest
from modules.document.title import EmptyTitleError, normalize_title


def test_normalize_title_trims_surrounding_whitespace():
    """주변 공백을 제거한다."""
    assert normalize_title("  hello  ") == "hello"
    assert normalize_title("\thello\t") == "hello"
    assert normalize_title("\n  hello\n") == "hello"


def test_normalize_title_collapses_internal_whitespace():
    """내부 공백을 단일 공백으로 축소한다."""
    assert normalize_title("hello  world") == "hello world"
    assert normalize_title("hello\t\tworld") == "hello world"
    assert normalize_title("hello  \t  world") == "hello world"


def test_normalize_title_with_multiple_internal_spaces():
    """여러 내부 공백을 축소한다."""
    assert normalize_title("a   b   c") == "a b c"
    assert normalize_title("  a   b   c  ") == "a b c"


def test_normalize_title_rejects_empty_string():
    """빈 문자열을 거부한다."""
    with pytest.raises(EmptyTitleError) as exc_info:
        normalize_title("")

    assert "제목은 비어있을 수 없습니다" in str(exc_info.value)


def test_normalize_title_rejects_whitespace_only():
    """공백만 있는 제목을 거부한다."""
    with pytest.raises(EmptyTitleError) as exc_info:
        normalize_title("   ")

    assert "제목은 비어있을 수 없습니다" in str(exc_info.value)


def test_normalize_title_rejects_tabs_and_newlines_only():
    """탭과 개행만 있는 제목을 거부한다."""
    with pytest.raises(EmptyTitleError):
        normalize_title("\t\n\t")


def test_normalize_title_preserves_normal_title():
    """정상적인 제목은 그대로 유지한다."""
    assert normalize_title("My Document Title") == "My Document Title"
    assert normalize_title("한글 제목") == "한글 제목"


def test_normalize_title_with_mixed_languages():
    """혼합된 언어 제목을 정규화한다."""
    assert normalize_title("  Document 한글 Title  ") == "Document 한글 Title"
