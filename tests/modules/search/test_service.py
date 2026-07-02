"""SearchService 골격 테스트."""
import pytest

from modules.search.document import SearchDocument
from modules.search.in_memory_adapter import InMemorySearchAdapter
from modules.search.query import SearchQuery
from modules.search.service import SearchService


class TestSearchServiceIndexDocument:
    """색인 위임 동작 테스트."""

    @pytest.mark.asyncio
    async def test_index_document_delegates_to_adapter(self):
        """index_document는 어댑터의 index를 호출해 문서를 색인한다."""
        adapter = InMemorySearchAdapter()
        service = SearchService(adapter)
        document = SearchDocument(document_id="doc1", title="Hello World")

        await service.index_document(document)

        assert adapter._documents["doc1"] is document

    @pytest.mark.asyncio
    async def test_index_document_overwrites_existing_document(self):
        """같은 id로 다시 색인하면 어댑터에 저장된 문서가 갱신된다."""
        adapter = InMemorySearchAdapter()
        service = SearchService(adapter)
        first = SearchDocument(document_id="doc1", title="First Title")
        second = SearchDocument(document_id="doc1", title="Second Title")

        await service.index_document(first)
        await service.index_document(second)

        assert adapter._documents["doc1"] is second


class TestSearchServiceSearch:
    """검색 위임 동작 테스트."""

    @pytest.mark.asyncio
    async def test_search_delegates_to_adapter(self):
        """search는 어댑터의 search를 호출해 결과를 반환한다."""
        adapter = InMemorySearchAdapter()
        service = SearchService(adapter)
        document = SearchDocument(document_id="doc1", title="Hello World")
        await service.index_document(document)

        results = await service.search(SearchQuery(term="Hello"))

        assert len(results) == 1
        assert results[0].document.document_id == "doc1"

    @pytest.mark.asyncio
    async def test_search_returns_empty_list_when_no_match(self):
        """일치하는 문서가 없으면 빈 목록을 반환한다."""
        adapter = InMemorySearchAdapter()
        service = SearchService(adapter)
        await service.index_document(
            SearchDocument(document_id="doc1", title="Hello World")
        )

        results = await service.search(SearchQuery(term="Nonexistent"))

        assert results == []

    @pytest.mark.asyncio
    async def test_search_on_empty_index_returns_empty_list(self):
        """색인된 문서가 없으면 빈 목록을 반환한다."""
        adapter = InMemorySearchAdapter()
        service = SearchService(adapter)

        results = await service.search(SearchQuery(term="Anything"))

        assert results == []
