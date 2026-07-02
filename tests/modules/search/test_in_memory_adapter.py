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


class TestInMemorySearchAdapterDelete:
    """삭제 기능 테스트."""

    @pytest.mark.asyncio
    async def test_delete_removes_document(self):
        """delete는 색인에서 문서를 제거한다."""
        adapter = InMemorySearchAdapter()
        document = SearchDocument(document_id="doc1", title="Hello World")
        await adapter.index(document)

        await adapter.delete("doc1")

        assert "doc1" not in adapter._documents

    @pytest.mark.asyncio
    async def test_delete_removes_document_from_search_results(self):
        """삭제된 문서는 더 이상 검색 결과에 포함되지 않는다."""
        adapter = InMemorySearchAdapter()
        document = SearchDocument(document_id="doc1", title="Hello World")
        await adapter.index(document)

        await adapter.delete("doc1")

        results = await adapter.search(SearchQuery(term="Hello"))
        assert results == []

    @pytest.mark.asyncio
    async def test_delete_only_removes_target_document(self):
        """다른 문서를 삭제해도 나머지 문서는 색인에 남아있다."""
        adapter = InMemorySearchAdapter()
        await adapter.index(SearchDocument(document_id="doc1", title="Apple Pie"))
        await adapter.index(SearchDocument(document_id="doc2", title="Apple Juice"))

        await adapter.delete("doc1")

        assert "doc1" not in adapter._documents
        assert adapter._documents["doc2"].title == "Apple Juice"

    @pytest.mark.asyncio
    async def test_delete_nonexistent_document_does_not_raise(self):
        """존재하지 않는 id를 삭제해도 오류를 내지 않는다."""
        adapter = InMemorySearchAdapter()

        await adapter.delete("nonexistent")

        assert adapter._documents == {}


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

    @pytest.mark.asyncio
    async def test_search_matches_redirect_target(self):
        """질의어가 리다이렉트 대상에만 있어도 검색 결과에 포함된다."""
        document = SearchDocument(
            document_id="doc1", title="Old Title", redirect_target="NewTitle"
        )
        adapter = InMemorySearchAdapter()
        await adapter.index(document)

        results = await adapter.search(SearchQuery(term="NewTitle"))

        assert len(results) == 1
        assert results[0].document.document_id == "doc1"

    @pytest.mark.asyncio
    async def test_search_does_not_match_when_redirect_target_is_none(self):
        """리다이렉트 대상이 없는 문서는 리다이렉트 대상으로 검색되지 않는다."""
        document = SearchDocument(document_id="doc1", title="Hello World")
        adapter = InMemorySearchAdapter()
        await adapter.index(document)

        results = await adapter.search(SearchQuery(term="NewTitle"))

        assert results == []

    @pytest.mark.asyncio
    async def test_search_matches_category(self):
        """질의어가 카테고리에만 있어도 검색 결과에 포함된다."""
        document = SearchDocument(
            document_id="doc1", title="Hello World", categories=["Wiki"]
        )
        adapter = InMemorySearchAdapter()
        await adapter.index(document)

        results = await adapter.search(SearchQuery(term="Wiki"))

        assert len(results) == 1
        assert results[0].document.document_id == "doc1"

    @pytest.mark.asyncio
    async def test_search_does_not_match_when_categories_is_empty(self):
        """카테고리가 없는 문서는 카테고리로 검색되지 않는다."""
        document = SearchDocument(document_id="doc1", title="Hello World")
        adapter = InMemorySearchAdapter()
        await adapter.index(document)

        results = await adapter.search(SearchQuery(term="Wiki"))

        assert results == []


class TestInMemorySearchAdapterBodySearchFallback:
    """제목에 일치하는 내용이 없을 때 본문 검색으로 폴백하는 동작 테스트."""

    @pytest.mark.asyncio
    async def test_body_fallback_is_case_insensitive(self):
        """본문 폴백 검색은 대소문자를 구분하지 않는다."""
        adapter = InMemorySearchAdapter()
        document = SearchDocument(
            document_id="doc1", title="Hello World", body="Findable Term here"
        )
        await adapter.index(document)

        results = await adapter.search(SearchQuery(term="findable term"))

        assert len(results) == 1
        assert results[0].document.document_id == "doc1"

    @pytest.mark.asyncio
    async def test_body_fallback_matches_partial_term(self):
        """질의어가 본문 단어의 일부에 포함되면 검색 결과에 포함된다."""
        adapter = InMemorySearchAdapter()
        document = SearchDocument(
            document_id="doc1", title="Hello World", body="Unfindable content"
        )
        await adapter.index(document)

        results = await adapter.search(SearchQuery(term="findable"))

        assert len(results) == 1
        assert results[0].document.document_id == "doc1"

    @pytest.mark.asyncio
    async def test_body_fallback_returns_multiple_matching_documents(self):
        """본문 폴백 검색으로 여러 문서가 일치하면 모두 반환한다."""
        adapter = InMemorySearchAdapter()
        await adapter.index(
            SearchDocument(document_id="doc1", title="First", body="shared keyword")
        )
        await adapter.index(
            SearchDocument(document_id="doc2", title="Second", body="shared keyword")
        )
        await adapter.index(
            SearchDocument(document_id="doc3", title="Third", body="unrelated text")
        )

        results = await adapter.search(SearchQuery(term="shared keyword"))

        result_ids = {result.document.document_id for result in results}
        assert result_ids == {"doc1", "doc2"}

    @pytest.mark.asyncio
    async def test_body_fallback_does_not_duplicate_result_when_term_in_title_and_body(
        self,
    ):
        """질의어가 제목과 본문에 모두 있어도 결과는 한 번만 반환된다."""
        adapter = InMemorySearchAdapter()
        document = SearchDocument(
            document_id="doc1", title="Findable Title", body="Findable body text"
        )
        await adapter.index(document)

        results = await adapter.search(SearchQuery(term="Findable"))

        assert len(results) == 1
        assert results[0].document.document_id == "doc1"

    @pytest.mark.asyncio
    async def test_body_fallback_does_not_match_when_term_absent_from_title_and_body(
        self,
    ):
        """질의어가 제목과 본문 어디에도 없으면 본문 폴백으로도 결과가 없다."""
        adapter = InMemorySearchAdapter()
        document = SearchDocument(
            document_id="doc1", title="Hello World", body="Some other content"
        )
        await adapter.index(document)

        results = await adapter.search(SearchQuery(term="Nonexistent"))

        assert results == []

    @pytest.mark.asyncio
    async def test_body_fallback_does_not_match_when_body_is_default_empty(self):
        """본문을 지정하지 않은 문서는 빈 본문으로 취급되어 본문 폴백이 일치하지 않는다."""
        adapter = InMemorySearchAdapter()
        document = SearchDocument(document_id="doc1", title="Hello World")
        await adapter.index(document)

        results = await adapter.search(SearchQuery(term="Findable"))

        assert results == []

    @pytest.mark.asyncio
    async def test_reindexing_updates_searchable_body(self):
        """같은 id로 본문을 바꿔 다시 색인하면, 본문 폴백 검색 결과에도 새 본문이 반영된다."""
        adapter = InMemorySearchAdapter()
        await adapter.index(
            SearchDocument(document_id="doc1", title="Title", body="Old body term")
        )
        await adapter.index(
            SearchDocument(document_id="doc1", title="Title", body="New body term")
        )

        old_body_results = await adapter.search(SearchQuery(term="Old body"))
        new_body_results = await adapter.search(SearchQuery(term="New body"))

        assert old_body_results == []
        assert len(new_body_results) == 1
        assert new_body_results[0].document.document_id == "doc1"


class TestInMemorySearchAdapterPagination:
    """검색 결과 페이지네이션 테스트."""

    @pytest.mark.asyncio
    async def test_limit_truncates_results(self):
        """limit을 지정하면 결과가 그 개수만큼으로 잘린다."""
        adapter = InMemorySearchAdapter()
        await adapter.index(SearchDocument(document_id="doc1", title="Apple Pie"))
        await adapter.index(SearchDocument(document_id="doc2", title="Apple Juice"))
        await adapter.index(SearchDocument(document_id="doc3", title="Apple Sauce"))

        results = await adapter.search(SearchQuery(term="Apple", limit=2))

        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_offset_skips_leading_results(self):
        """offset을 지정하면 그 개수만큼 앞쪽 결과를 건너뛴다."""
        adapter = InMemorySearchAdapter()
        await adapter.index(SearchDocument(document_id="doc1", title="Apple Pie"))
        await adapter.index(SearchDocument(document_id="doc2", title="Apple Juice"))
        await adapter.index(SearchDocument(document_id="doc3", title="Apple Sauce"))

        all_results = await adapter.search(SearchQuery(term="Apple"))
        offset_results = await adapter.search(SearchQuery(term="Apple", offset=1))

        assert len(offset_results) == 2
        assert [r.document.document_id for r in offset_results] == [
            r.document.document_id for r in all_results[1:]
        ]

    @pytest.mark.asyncio
    async def test_limit_and_offset_combine_for_a_page(self):
        """limit과 offset을 함께 지정하면 그 범위에 해당하는 페이지만 반환한다."""
        adapter = InMemorySearchAdapter()
        await adapter.index(SearchDocument(document_id="doc1", title="Apple Pie"))
        await adapter.index(SearchDocument(document_id="doc2", title="Apple Juice"))
        await adapter.index(SearchDocument(document_id="doc3", title="Apple Sauce"))

        all_results = await adapter.search(SearchQuery(term="Apple"))
        page_results = await adapter.search(SearchQuery(term="Apple", limit=1, offset=1))

        assert len(page_results) == 1
        assert page_results[0].document.document_id == all_results[1].document.document_id

    @pytest.mark.asyncio
    async def test_offset_beyond_result_count_returns_empty_list(self):
        """offset이 일치하는 결과 개수보다 크면 빈 목록을 반환한다."""
        adapter = InMemorySearchAdapter()
        await adapter.index(SearchDocument(document_id="doc1", title="Apple Pie"))

        results = await adapter.search(SearchQuery(term="Apple", offset=5))

        assert results == []

    @pytest.mark.asyncio
    async def test_no_limit_returns_all_matching_results(self):
        """limit을 지정하지 않으면 일치하는 결과를 모두 반환한다."""
        adapter = InMemorySearchAdapter()
        await adapter.index(SearchDocument(document_id="doc1", title="Apple Pie"))
        await adapter.index(SearchDocument(document_id="doc2", title="Apple Juice"))

        results = await adapter.search(SearchQuery(term="Apple"))

        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_limit_larger_than_remaining_results_returns_only_remaining(self):
        """offset 이후 남은 결과보다 limit이 크면 남은 결과만 반환한다."""
        adapter = InMemorySearchAdapter()
        await adapter.index(SearchDocument(document_id="doc1", title="Apple Pie"))
        await adapter.index(SearchDocument(document_id="doc2", title="Apple Juice"))
        await adapter.index(SearchDocument(document_id="doc3", title="Apple Sauce"))

        results = await adapter.search(SearchQuery(term="Apple", limit=10, offset=2))

        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_paginating_through_all_pages_reconstructs_full_result_set(self):
        """limit으로 나눈 페이지를 모두 이어붙이면 전체 결과와 같아지고 중복/누락이 없다."""
        adapter = InMemorySearchAdapter()
        await adapter.index(SearchDocument(document_id="doc1", title="Apple Pie"))
        await adapter.index(SearchDocument(document_id="doc2", title="Apple Juice"))
        await adapter.index(SearchDocument(document_id="doc3", title="Apple Sauce"))

        all_results = await adapter.search(SearchQuery(term="Apple"))
        page1 = await adapter.search(SearchQuery(term="Apple", limit=2, offset=0))
        page2 = await adapter.search(SearchQuery(term="Apple", limit=2, offset=2))

        paginated_ids = [r.document.document_id for r in page1 + page2]
        assert paginated_ids == [r.document.document_id for r in all_results]
        assert len(set(paginated_ids)) == len(paginated_ids)


class TestInMemorySearchAdapterRedirectSearch:
    """리다이렉트 대상으로 검색되는 동작 테스트."""

    @pytest.mark.asyncio
    async def test_redirect_search_is_case_insensitive(self):
        """리다이렉트 대상 검색은 대소문자를 구분하지 않는다."""
        adapter = InMemorySearchAdapter()
        document = SearchDocument(
            document_id="doc1", title="Old Title", redirect_target="New Title"
        )
        await adapter.index(document)

        results = await adapter.search(SearchQuery(term="new title"))

        assert len(results) == 1
        assert results[0].document.document_id == "doc1"

    @pytest.mark.asyncio
    async def test_redirect_search_matches_partial_target(self):
        """질의어가 리다이렉트 대상의 일부에 포함되면 검색 결과에 포함된다."""
        adapter = InMemorySearchAdapter()
        document = SearchDocument(
            document_id="doc1", title="Old Title", redirect_target="New Title"
        )
        await adapter.index(document)

        results = await adapter.search(SearchQuery(term="Title"))

        assert len(results) == 1
        assert results[0].document.document_id == "doc1"

    @pytest.mark.asyncio
    async def test_redirect_search_returns_multiple_matching_documents(self):
        """리다이렉트 대상 검색으로 여러 문서가 일치하면 모두 반환한다."""
        adapter = InMemorySearchAdapter()
        await adapter.index(
            SearchDocument(
                document_id="doc1", title="First", redirect_target="Shared Target"
            )
        )
        await adapter.index(
            SearchDocument(
                document_id="doc2", title="Second", redirect_target="Shared Target"
            )
        )
        await adapter.index(
            SearchDocument(
                document_id="doc3", title="Third", redirect_target="Unrelated Target"
            )
        )

        results = await adapter.search(SearchQuery(term="Shared Target"))

        result_ids = {result.document.document_id for result in results}
        assert result_ids == {"doc1", "doc2"}

    @pytest.mark.asyncio
    async def test_redirect_search_does_not_duplicate_result_when_term_in_title_and_redirect_target(
        self,
    ):
        """질의어가 제목과 리다이렉트 대상에 모두 있어도 결과는 한 번만 반환된다."""
        adapter = InMemorySearchAdapter()
        document = SearchDocument(
            document_id="doc1",
            title="Findable Title",
            redirect_target="Findable Redirect",
        )
        await adapter.index(document)

        results = await adapter.search(SearchQuery(term="Findable"))

        assert len(results) == 1
        assert results[0].document.document_id == "doc1"

    @pytest.mark.asyncio
    async def test_redirect_search_does_not_match_when_term_absent_from_redirect_target(
        self,
    ):
        """질의어가 리다이렉트 대상에 없으면 리다이렉트 검색으로도 결과가 없다."""
        adapter = InMemorySearchAdapter()
        document = SearchDocument(
            document_id="doc1", title="Old Title", redirect_target="New Title"
        )
        await adapter.index(document)

        results = await adapter.search(SearchQuery(term="Nonexistent"))

        assert results == []

    @pytest.mark.asyncio
    async def test_reindexing_updates_searchable_redirect_target(self):
        """같은 id로 리다이렉트 대상을 바꿔 다시 색인하면, 검색 결과에도 새 리다이렉트 대상이 반영된다."""
        adapter = InMemorySearchAdapter()
        await adapter.index(
            SearchDocument(
                document_id="doc1", title="Title", redirect_target="Old Target"
            )
        )
        await adapter.index(
            SearchDocument(
                document_id="doc1", title="Title", redirect_target="New Target"
            )
        )

        old_target_results = await adapter.search(SearchQuery(term="Old Target"))
        new_target_results = await adapter.search(SearchQuery(term="New Target"))

        assert old_target_results == []
        assert len(new_target_results) == 1
        assert new_target_results[0].document.document_id == "doc1"
