"""검색 질의 모델 테스트."""
import pytest
from modules.search.query import (
    SearchQuery,
    EmptySearchQueryTermError,
    InvalidSearchQueryLimitError,
    InvalidSearchQueryOffsetError,
)


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


class TestSearchQueryPagination:
    """검색 질의 페이지네이션 파라미터 테스트."""

    def test_defaults_to_no_limit_and_zero_offset(self):
        """limit/offset을 지정하지 않으면 제한 없이 처음부터 조회한다."""
        query = SearchQuery(term="wiki")
        assert query.limit is None
        assert query.offset == 0

    def test_creates_search_query_with_limit_and_offset(self):
        """limit과 offset을 지정해 검색 질의를 생성한다."""
        query = SearchQuery(term="wiki", limit=10, offset=20)
        assert query.limit == 10
        assert query.offset == 20

    def test_rejects_limit_below_one(self):
        """limit이 1 미만이면 검색 질의를 생성할 수 없다."""
        with pytest.raises(InvalidSearchQueryLimitError):
            SearchQuery(term="wiki", limit=0)

    def test_rejects_negative_limit(self):
        """limit이 음수이면 검색 질의를 생성할 수 없다."""
        with pytest.raises(InvalidSearchQueryLimitError):
            SearchQuery(term="wiki", limit=-1)

    def test_rejects_negative_offset(self):
        """offset이 음수이면 검색 질의를 생성할 수 없다."""
        with pytest.raises(InvalidSearchQueryOffsetError):
            SearchQuery(term="wiki", offset=-1)
