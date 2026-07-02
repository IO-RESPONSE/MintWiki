"""메모리 기반 검색 어댑터 테스트."""
import pytest

from modules.search.in_memory_adapter import InMemorySearchAdapter
from modules.search.document import SearchDocument
from modules.search.query import SearchQuery


class TestInMemorySearchAdapterIndex:
    """색인 기능 테스트."""

    @pytest.mark.asyncio
    async def test_index_stores_document(self):
        """index는 검색 문서를 저장한다."""
        adapter = InMemorySearchAdapter()
        document = SearchDocument(document_id="doc1", title="Hello World")

        await adapter.index(document)

        assert adapter._documents["doc1"] is document

    @pytest.mark.asyncio
    async def test_index_overwrites_existing_document(self):
        """같은 id로 다시 색인하면 기존 문서가 갱신된다."""
        adapter = InMemorySearchAdapter()
        first = SearchDocument(document_id="doc1", title="First Title")
        second = SearchDocument(document_id="doc1", title="Second Title")

        await adapter.index(first)
        await adapter.index(second)

        assert adapter._documents["doc1"] is second

    @pytest.mark.asyncio
    async def test_reindexing_updates_searchable_title(self):
        """같은 id로 제목을 바꿔 다시 색인하면, 검색 결과에도 새 제목이 반영된다."""
        adapter = InMemorySearchAdapter()
        await adapter.index(SearchDocument(document_id="doc1", title="First Title"))
        await adapter.index(SearchDocument(document_id="doc1", title="Second Title"))

        old_title_results = await adapter.search(SearchQuery(term="First"))
        new_title_results = await adapter.search(SearchQuery(term="Second"))

        assert old_title_results == []
        assert len(new_title_results) == 1
        assert new_title_results[0].document.document_id == "doc1"


class TestInMemorySearchAdapterSearch:
    """검색 기능 테스트."""

    @pytest.mark.asyncio
    async def test_search_matches_title_exactly(self):
        """제목과 질의어가 완전히 일치하면 검색 결과에 포함된다."""
        adapter = InMemorySearchAdapter()
        document = SearchDocument(document_id="doc1", title="Hello World")
        await adapter.index(document)

        results = await adapter.search(SearchQuery(term="Hello World"))

        assert len(results) == 1
        assert results[0].document.document_id == "doc1"
        assert results[0].score == 1.0

    @pytest.mark.asyncio
    async def test_search_matches_partial_title(self):
        """질의어가 제목의 일부에 포함되면 검색 결과에 포함된다."""
        adapter = InMemorySearchAdapter()
        document = SearchDocument(document_id="doc1", title="Hello World")
        await adapter.index(document)

        results = await adapter.search(SearchQuery(term="World"))

        assert len(results) == 1
        assert results[0].document.document_id == "doc1"

    @pytest.mark.asyncio
    async def test_search_is_case_insensitive(self):
        """제목 검색은 대소문자를 구분하지 않는다."""
        adapter = InMemorySearchAdapter()
        document = SearchDocument(document_id="doc1", title="Hello World")
        await adapter.index(document)

        results = await adapter.search(SearchQuery(term="hello"))

        assert len(results) == 1
        assert results[0].document.document_id == "doc1"

    @pytest.mark.asyncio
    async def test_search_returns_empty_list_when_no_match(self):
        """일치하는 문서가 없으면 빈 목록을 반환한다."""
        adapter = InMemorySearchAdapter()
        document = SearchDocument(document_id="doc1", title="Hello World")
        await adapter.index(document)

        results = await adapter.search(SearchQuery(term="Nonexistent"))

        assert results == []

    @pytest.mark.asyncio
    async def test_search_returns_multiple_matching_documents(self):
        """질의어에 일치하는 여러 문서를 모두 반환한다."""
        adapter = InMemorySearchAdapter()
        await adapter.index(SearchDocument(document_id="doc1", title="Apple Pie"))
        await adapter.index(SearchDocument(document_id="doc2", title="Apple Juice"))
        await adapter.index(SearchDocument(document_id="doc3", title="Banana Bread"))

        results = await adapter.search(SearchQuery(term="Apple"))

        result_ids = {result.document.document_id for result in results}
        assert result_ids == {"doc1", "doc2"}

    @pytest.mark.asyncio
    async def test_search_on_empty_index_returns_empty_list(self):
        """색인된 문서가 없으면 빈 목록을 반환한다."""
        adapter = InMemorySearchAdapter()

        results = await adapter.search(SearchQuery(term="Anything"))

        assert results == []

    @pytest.mark.asyncio
    async def test_search_matches_body_only_content(self):
        """질의어가 본문에만 있고 제목에는 없어도 검색 결과에 포함된다."""
        adapter = InMemorySearchAdapter()
        document = SearchDocument(
            document_id="doc1", title="Hello World", body="Findable term here"
        )
        await adapter.index(document)

        results = await adapter.search(SearchQuery(term="Findable"))

        assert len(results) == 1
        assert results[0].document.document_id == "doc1"
