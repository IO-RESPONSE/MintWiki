"""SearchReindexCommand 골격 테스트."""
import pytest

from modules.search.document import SearchDocument
from modules.search.errors import SearchServiceError
from modules.search.in_memory_adapter import InMemorySearchAdapter
from modules.search.query import SearchQuery
from modules.search.reindex import SearchReindexCommand
from modules.search.service import SearchService


class TestSearchReindexCommandRun:
    """document_source 순회 및 색인 위임 동작 테스트."""

    @pytest.mark.asyncio
    async def test_indexes_every_document_from_source(self):
        """document_source의 모든 문서를 서비스에 위임해 색인한다."""
        adapter = InMemorySearchAdapter()
        service = SearchService(adapter)
        documents = [
            SearchDocument(document_id="doc1", title="Apple Pie"),
            SearchDocument(document_id="doc2", title="Banana Bread"),
        ]
        command = SearchReindexCommand(service, documents)

        await command.run()

        assert adapter._documents["doc1"] is documents[0]
        assert adapter._documents["doc2"] is documents[1]

    @pytest.mark.asyncio
    async def test_returns_count_of_indexed_documents(self):
        """색인을 완료한 문서 개수를 반환한다."""
        adapter = InMemorySearchAdapter()
        service = SearchService(adapter)
        documents = [
            SearchDocument(document_id="doc1", title="Apple Pie"),
            SearchDocument(document_id="doc2", title="Banana Bread"),
            SearchDocument(document_id="doc3", title="Cherry Tart"),
        ]
        command = SearchReindexCommand(service, documents)

        count = await command.run()

        assert count == 3

    @pytest.mark.asyncio
    async def test_empty_document_source_indexes_nothing(self):
        """document_source가 비어있으면 아무것도 색인하지 않고 0을 반환한다."""
        adapter = InMemorySearchAdapter()
        service = SearchService(adapter)
        command = SearchReindexCommand(service, [])

        count = await command.run()

        assert count == 0
        assert adapter._documents == {}

    @pytest.mark.asyncio
    async def test_reindexed_documents_are_searchable(self):
        """재색인된 문서는 검색으로 찾을 수 있다."""
        adapter = InMemorySearchAdapter()
        service = SearchService(adapter)
        documents = [SearchDocument(document_id="doc1", title="Apple Pie")]
        command = SearchReindexCommand(service, documents)

        await command.run()
        results = await service.search(SearchQuery(term="Apple"))

        assert len(results) == 1
        assert results[0].document.document_id == "doc1"

    @pytest.mark.asyncio
    async def test_propagates_search_service_error(self):
        """서비스가 색인 중 오류를 던지면 그대로 전파된다."""

        class FailingSearchAdapter(InMemorySearchAdapter):
            async def index(self, document: SearchDocument) -> None:
                raise ConnectionError("색인 서버에 연결할 수 없음")

        service = SearchService(FailingSearchAdapter())
        documents = [SearchDocument(document_id="doc1", title="Apple Pie")]
        command = SearchReindexCommand(service, documents)

        with pytest.raises(SearchServiceError) as exc_info:
            await command.run()

        assert exc_info.value.operation == "index"
