"""SearchService 골격 테스트."""
import pytest

from modules.search.adapter import SearchAdapter
from modules.search.document import SearchDocument
from modules.search.errors import SearchServiceError
from modules.search.in_memory_adapter import InMemorySearchAdapter
from modules.search.query import SearchQuery
from modules.search.service import SearchService


class FailingSearchAdapter(SearchAdapter):
    """모든 작업에서 지정된 예외를 던지는 어댑터. 오류 매핑 테스트용."""

    def __init__(self, error: Exception):
        self._error = error

    async def index(self, document: SearchDocument) -> None:
        raise self._error

    async def search(self, query: SearchQuery):
        raise self._error

    async def delete(self, document_id: str) -> None:
        raise self._error


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

    @pytest.mark.asyncio
    async def test_index_document_stores_multiple_documents_independently(self):
        """서로 다른 id의 문서를 색인하면 각각 독립적으로 저장된다."""
        adapter = InMemorySearchAdapter()
        service = SearchService(adapter)
        first = SearchDocument(document_id="doc1", title="First Title")
        second = SearchDocument(document_id="doc2", title="Second Title")

        await service.index_document(first)
        await service.index_document(second)

        assert adapter._documents["doc1"] is first
        assert adapter._documents["doc2"] is second


class TestSearchServiceDeleteDocument:
    """삭제 위임 동작 테스트."""

    @pytest.mark.asyncio
    async def test_delete_document_delegates_to_adapter(self):
        """delete_document는 어댑터의 delete를 호출해 문서를 삭제한다."""
        adapter = InMemorySearchAdapter()
        service = SearchService(adapter)
        document = SearchDocument(document_id="doc1", title="Hello World")
        await service.index_document(document)

        await service.delete_document("doc1")

        assert "doc1" not in adapter._documents

    @pytest.mark.asyncio
    async def test_delete_document_removes_document_from_search_results(self):
        """삭제된 문서는 더 이상 검색 결과에 포함되지 않는다."""
        adapter = InMemorySearchAdapter()
        service = SearchService(adapter)
        document = SearchDocument(document_id="doc1", title="Hello World")
        await service.index_document(document)

        await service.delete_document("doc1")

        results = await service.search(SearchQuery(term="Hello"))
        assert results == []

    @pytest.mark.asyncio
    async def test_delete_document_ignores_missing_document(self):
        """존재하지 않는 id를 삭제해도 오류를 내지 않는다."""
        adapter = InMemorySearchAdapter()
        service = SearchService(adapter)

        await service.delete_document("nonexistent")


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

    @pytest.mark.asyncio
    async def test_search_returns_all_matching_documents(self):
        """질의어에 일치하는 여러 문서를 모두 반환한다."""
        adapter = InMemorySearchAdapter()
        service = SearchService(adapter)
        await service.index_document(
            SearchDocument(document_id="doc1", title="Apple Pie")
        )
        await service.index_document(
            SearchDocument(document_id="doc2", title="Apple Juice")
        )
        await service.index_document(
            SearchDocument(document_id="doc3", title="Banana Bread")
        )

        results = await service.search(SearchQuery(term="Apple"))

        result_ids = {result.document.document_id for result in results}
        assert result_ids == {"doc1", "doc2"}

    @pytest.mark.asyncio
    async def test_search_applies_pagination_from_query(self):
        """search는 질의에 담긴 limit/offset을 어댑터에 그대로 전달해 페이지네이션한다."""
        adapter = InMemorySearchAdapter()
        service = SearchService(adapter)
        await service.index_document(
            SearchDocument(document_id="doc1", title="Apple Pie")
        )
        await service.index_document(
            SearchDocument(document_id="doc2", title="Apple Juice")
        )

        results = await service.search(SearchQuery(term="Apple", limit=1, offset=1))

        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_applies_limit_only_from_query(self):
        """offset 없이 limit만 지정해도 어댑터에 전달되어 결과 개수가 제한된다."""
        adapter = InMemorySearchAdapter()
        service = SearchService(adapter)
        await service.index_document(
            SearchDocument(document_id="doc1", title="Apple Pie")
        )
        await service.index_document(
            SearchDocument(document_id="doc2", title="Apple Juice")
        )

        results = await service.search(SearchQuery(term="Apple", limit=1))

        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_offset_beyond_result_count_returns_empty_list(self):
        """offset이 일치하는 결과 개수보다 크면 빈 목록을 반환한다."""
        adapter = InMemorySearchAdapter()
        service = SearchService(adapter)
        await service.index_document(
            SearchDocument(document_id="doc1", title="Apple Pie")
        )

        results = await service.search(SearchQuery(term="Apple", offset=5))

        assert results == []


class TestSearchServiceRankingPlaceholder:
    """관련도 순위가 아직 구현되지 않은 placeholder 점수 동작 테스트."""

    @pytest.mark.asyncio
    async def test_search_result_has_placeholder_score(self):
        """검색 결과의 점수는 실제 관련도 계산 없이 고정된 placeholder 값을 가진다."""
        adapter = InMemorySearchAdapter()
        service = SearchService(adapter)
        await service.index_document(
            SearchDocument(document_id="doc1", title="Hello World")
        )

        results = await service.search(SearchQuery(term="Hello"))

        assert results[0].score == 1.0

    @pytest.mark.asyncio
    async def test_search_results_share_equal_placeholder_score_regardless_of_match_location(
        self,
    ):
        """제목/본문 등 일치 위치가 다른 문서들도 관련도 순위 없이 동일한 점수를 받는다."""
        adapter = InMemorySearchAdapter()
        service = SearchService(adapter)
        await service.index_document(
            SearchDocument(document_id="doc1", title="Apple Pie")
        )
        await service.index_document(
            SearchDocument(document_id="doc2", title="Fruit", body="Apple mentioned once in body")
        )

        results = await service.search(SearchQuery(term="Apple"))

        scores = {result.document.document_id: result.score for result in results}
        assert scores == {"doc1": 1.0, "doc2": 1.0}


class TestSearchServiceAdapterFailureMapping:
    """어댑터 예외가 SearchServiceError로 매핑되는 동작 테스트."""

    @pytest.mark.asyncio
    async def test_index_document_wraps_adapter_error(self):
        """색인 중 어댑터가 던진 예외는 SearchServiceError로 감싸진다."""
        original = ConnectionError("색인 서버에 연결할 수 없음")
        adapter = FailingSearchAdapter(original)
        service = SearchService(adapter)

        with pytest.raises(SearchServiceError) as exc_info:
            await service.index_document(SearchDocument(document_id="doc1", title="Hello"))

        assert exc_info.value.operation == "index"
        assert exc_info.value.original_error is original

    @pytest.mark.asyncio
    async def test_search_wraps_adapter_error(self):
        """검색 중 어댑터가 던진 예외는 SearchServiceError로 감싸진다."""
        original = RuntimeError("검색 서버 오류")
        adapter = FailingSearchAdapter(original)
        service = SearchService(adapter)

        with pytest.raises(SearchServiceError) as exc_info:
            await service.search(SearchQuery(term="Hello"))

        assert exc_info.value.operation == "search"
        assert exc_info.value.original_error is original

    @pytest.mark.asyncio
    async def test_delete_document_wraps_adapter_error(self):
        """삭제 중 어댑터가 던진 예외는 SearchServiceError로 감싸진다."""
        original = TimeoutError("삭제 요청 시간 초과")
        adapter = FailingSearchAdapter(original)
        service = SearchService(adapter)

        with pytest.raises(SearchServiceError) as exc_info:
            await service.delete_document("doc1")

        assert exc_info.value.operation == "delete"
        assert exc_info.value.original_error is original

    @pytest.mark.asyncio
    async def test_wrapped_error_chains_original_as_cause(self):
        """감싸진 오류는 원본 예외를 __cause__로 보존해 원인을 추적할 수 있다."""
        original = ValueError("잘못된 색인 데이터")
        adapter = FailingSearchAdapter(original)
        service = SearchService(adapter)

        with pytest.raises(SearchServiceError) as exc_info:
            await service.index_document(SearchDocument(document_id="doc1", title="Hello"))

        assert exc_info.value.__cause__ is original
