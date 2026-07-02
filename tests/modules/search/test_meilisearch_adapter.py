"""Meilisearch 검색 어댑터 골격 테스트."""
import pytest

from modules.search.adapter import SearchAdapter
from modules.search.document import SearchDocument
from modules.search.meilisearch_adapter import MeilisearchSearchAdapter
from modules.search.query import SearchQuery


class TestMeilisearchSearchAdapterConstruction:
    """생성자 테스트."""

    def test_is_search_adapter_subclass(self):
        """MeilisearchSearchAdapter는 SearchAdapter를 구현한다."""
        assert issubclass(MeilisearchSearchAdapter, SearchAdapter)

    def test_stores_connection_settings(self):
        """생성자는 접속 정보를 보관한다."""
        adapter = MeilisearchSearchAdapter(
            host="http://localhost:7700", index_name="wiki_pages", api_key="secret"
        )

        assert adapter.host == "http://localhost:7700"
        assert adapter.index_name == "wiki_pages"
        assert adapter.api_key == "secret"

    def test_api_key_defaults_to_none(self):
        """api_key를 생략하면 None으로 저장된다."""
        adapter = MeilisearchSearchAdapter(
            host="http://localhost:7700", index_name="wiki_pages"
        )

        assert adapter.api_key is None


class TestMeilisearchSearchAdapterSkeletonBehavior:
    """아직 구현되지 않은 메서드 동작 테스트."""

    @pytest.mark.asyncio
    async def test_index_raises_not_implemented(self):
        """index는 아직 구현되지 않아 NotImplementedError를 발생시킨다."""
        adapter = MeilisearchSearchAdapter(
            host="http://localhost:7700", index_name="wiki_pages"
        )
        document = SearchDocument(document_id="doc1", title="Hello World")

        with pytest.raises(NotImplementedError):
            await adapter.index(document)

    @pytest.mark.asyncio
    async def test_search_raises_not_implemented(self):
        """search는 아직 구현되지 않아 NotImplementedError를 발생시킨다."""
        adapter = MeilisearchSearchAdapter(
            host="http://localhost:7700", index_name="wiki_pages"
        )

        with pytest.raises(NotImplementedError):
            await adapter.search(SearchQuery(term="Hello"))

    @pytest.mark.asyncio
    async def test_delete_raises_not_implemented(self):
        """delete는 아직 구현되지 않아 NotImplementedError를 발생시킨다."""
        adapter = MeilisearchSearchAdapter(
            host="http://localhost:7700", index_name="wiki_pages"
        )

        with pytest.raises(NotImplementedError):
            await adapter.delete("doc1")

    @pytest.mark.asyncio
    async def test_health_check_raises_not_implemented(self):
        """health_check는 아직 구현되지 않아 NotImplementedError를 발생시킨다."""
        adapter = MeilisearchSearchAdapter(
            host="http://localhost:7700", index_name="wiki_pages"
        )

        with pytest.raises(NotImplementedError):
            await adapter.health_check()
