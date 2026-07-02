"""검색 질의 모델 테스트."""
import pytest
from modules.search.query import SearchQuery, EmptySearchQueryTermError


class TestSearchQueryConstruction:
    """검색 질의 생성 테스트."""

    def test_creates_search_query_with_term(self):
        """검색어로 검색 질의를 생성한다."""
        query = SearchQuery(term="wiki")
        assert query.term == "wiki"

    def test_rejects_empty_term(self):
        """빈 검색어로 검색 질의를 생성할 수 없다."""
        with pytest.raises(EmptySearchQueryTermError):
            SearchQuery(term="")

    def test_rejects_whitespace_only_term(self):
        """공백만 있는 검색어로 검색 질의를 생성할 수 없다."""
        with pytest.raises(EmptySearchQueryTermError):
            SearchQuery(term="   ")
