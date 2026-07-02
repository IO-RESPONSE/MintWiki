"""검색 어댑터 인터페이스 테스트."""
import pytest

from modules.search.adapter import SearchAdapter
from modules.search.document import SearchDocument
from modules.search.query import SearchQuery
from modules.search.result import SearchResult


class ConcreteSearchAdapter(SearchAdapter):
    """테스트용 구체적인 검색 어댑터 구현."""

    def __init__(self):
        """어댑터를 초기화한다."""
        self.indexed_documents: dict[str, SearchDocument] = {}

    async def index(self, document: SearchDocument) -> None:
        """검색 문서를 색인에 추가하거나 갱신한다."""
        self.indexed_documents[document.document_id] = document

    async def search(self, query: SearchQuery) -> list[SearchResult]:
        """제목에 질의어가 포함된 문서를 검색 결과로 반환한다."""
        return [
            SearchResult(document=doc, score=1.0)
            for doc in self.indexed_documents.values()
            if query.term in doc.title
        ]

    async def delete(self, document_id: str) -> None:
        """주어진 id의 문서를 색인에서 삭제한다."""
        self.indexed_documents.pop(document_id, None)


class TestSearchAdapterInterface:
    """검색 어댑터 인터페이스 테스트."""

    def test_adapter_is_abstract(self):
        """검색 어댑터는 추상 클래스이다."""
        with pytest.raises(TypeError):
            SearchAdapter()

    def test_index_method_exists(self):
        """검색 어댑터는 index 메서드를 정의한다."""
        assert hasattr(SearchAdapter, "index")

    def test_search_method_exists(self):
        """검색 어댑터는 search 메서드를 정의한다."""
        assert hasattr(SearchAdapter, "search")

    def test_delete_method_exists(self):
        """검색 어댑터는 delete 메서드를 정의한다."""
        assert hasattr(SearchAdapter, "delete")

    @pytest.mark.asyncio
    async def test_concrete_implementation_can_index_document(self):
        """구체적인 구현은 문서를 색인할 수 있다."""
        adapter = ConcreteSearchAdapter()
        document = SearchDocument(document_id="doc1", title="Test Document")

        await adapter.index(document)

        assert adapter.indexed_documents["doc1"] is document

    @pytest.mark.asyncio
    async def test_concrete_implementation_can_search_indexed_documents(self):
        """구체적인 구현은 색인된 문서를 검색할 수 있다."""
        adapter = ConcreteSearchAdapter()
        document = SearchDocument(document_id="doc1", title="Test Document")
        await adapter.index(document)

        results = await adapter.search(SearchQuery(term="Test"))

        assert len(results) == 1
        assert results[0].document.document_id == "doc1"
        assert results[0].score == 1.0

    @pytest.mark.asyncio
    async def test_concrete_implementation_matches_title_exactly(self):
        """질의어가 제목과 완전히 일치해도 검색 결과에 포함된다."""
        adapter = ConcreteSearchAdapter()
        document = SearchDocument(document_id="doc1", title="Test Document")
        await adapter.index(document)

        results = await adapter.search(SearchQuery(term="Test Document"))

        assert len(results) == 1
        assert results[0].document.document_id == "doc1"
        assert results[0].score == 1.0

    @pytest.mark.asyncio
    async def test_concrete_implementation_matches_title_partially(self):
        """질의어가 제목의 일부에 포함되어도 검색 결과에 포함된다."""
        adapter = ConcreteSearchAdapter()
        document = SearchDocument(document_id="doc1", title="Test Document")
        await adapter.index(document)

        results = await adapter.search(SearchQuery(term="Document"))

        assert len(results) == 1
        assert results[0].document.document_id == "doc1"
        assert results[0].score == 1.0

    @pytest.mark.asyncio
    async def test_concrete_implementation_returns_empty_list_when_no_match(self):
        """구체적인 구현은 일치하는 문서가 없으면 빈 목록을 반환한다."""
        adapter = ConcreteSearchAdapter()
        document = SearchDocument(document_id="doc1", title="Test Document")
        await adapter.index(document)

        results = await adapter.search(SearchQuery(term="Nonexistent"))

        assert results == []

    @pytest.mark.asyncio
    async def test_concrete_implementation_returns_empty_list_when_index_is_empty(self):
        """구체적인 구현은 색인된 문서가 없으면 빈 목록을 반환한다."""
        adapter = ConcreteSearchAdapter()

        results = await adapter.search(SearchQuery(term="Anything"))

        assert results == []

    @pytest.mark.asyncio
    async def test_concrete_implementation_can_delete_indexed_document(self):
        """구체적인 구현은 색인된 문서를 삭제할 수 있다."""
        adapter = ConcreteSearchAdapter()
        document = SearchDocument(document_id="doc1", title="Test Document")
        await adapter.index(document)

        await adapter.delete("doc1")

        assert "doc1" not in adapter.indexed_documents

    @pytest.mark.asyncio
    async def test_concrete_implementation_delete_ignores_missing_document(self):
        """구체적인 구현은 존재하지 않는 id를 삭제해도 오류를 내지 않는다."""
        adapter = ConcreteSearchAdapter()

        await adapter.delete("nonexistent")
