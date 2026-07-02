"""검색 결과 모델 테스트."""
import pytest
from modules.search.document import SearchDocument
from modules.search.result import SearchResult, InvalidSearchResultScoreError


class TestSearchResultConstruction:
    """검색 결과 생성 테스트."""

    def test_creates_search_result_with_document_and_score(self):
        """문서와 점수로 검색 결과를 생성한다."""
        doc = SearchDocument(document_id="doc1", title="My Document")
        result = SearchResult(document=doc, score=1.5)
        assert result.document is doc
        assert result.score == 1.5

    def test_accepts_zero_score(self):
        """점수가 0인 검색 결과를 생성할 수 있다."""
        doc = SearchDocument(document_id="doc1", title="Title")
        result = SearchResult(document=doc, score=0)
        assert result.score == 0

    def test_rejects_negative_score(self):
        """음수 점수로 검색 결과를 생성할 수 없다."""
        doc = SearchDocument(document_id="doc1", title="Title")
        with pytest.raises(InvalidSearchResultScoreError):
            SearchResult(document=doc, score=-1)
