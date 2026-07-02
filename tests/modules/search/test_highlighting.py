"""검색 결과 하이라이팅 자리표시자 테스트."""
from modules.search.highlighting import highlight_search_term


class TestHighlightSearchTerm:
    """highlight_search_term 테스트."""

    def test_wraps_single_match_with_mark_tag(self):
        """일치하는 부분 하나를 <mark> 태그로 감싼다."""
        assert highlight_search_term("위키 엔진 소개", "엔진") == "위키 <mark>엔진</mark> 소개"

    def test_matches_case_insensitively_but_preserves_original_case(self):
        """대소문자를 구분하지 않고 일치시키되, 원문의 대소문자는 그대로 유지한다."""
        assert highlight_search_term("Wiki Engine", "engine") == "Wiki <mark>Engine</mark>"

    def test_wraps_every_occurrence(self):
        """일치하는 부분이 여러 번 나오면 모두 감싼다."""
        assert (
            highlight_search_term("엔진 엔진 엔진", "엔진")
            == "<mark>엔진</mark> <mark>엔진</mark> <mark>엔진</mark>"
        )

    def test_returns_unchanged_when_term_not_found(self):
        """질의어를 찾을 수 없으면 원본 텍스트를 그대로 반환한다."""
        assert highlight_search_term("위키 엔진", "존재하지않음") == "위키 엔진"

    def test_returns_unchanged_when_term_is_empty(self):
        """질의어가 빈 문자열이면 원본 텍스트를 그대로 반환한다."""
        assert highlight_search_term("위키 엔진", "") == "위키 엔진"

    def test_returns_empty_string_when_text_is_empty(self):
        """원본 텍스트가 빈 문자열이면 빈 문자열을 반환한다."""
        assert highlight_search_term("", "엔진") == ""
