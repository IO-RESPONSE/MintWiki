"""search-quality-baseline.md에 기록된 현재 검색 품질 기준선을 고정하는 테스트.

InMemorySearchAdapter의 매칭 동작이나 SearchFixtureLoader의 픽스처가 바뀌어
이 결과가 달라지면, 그것이 의도한 변경인지 확인하고 문서의 표도 함께
갱신해야 한다.
"""
import pytest

from modules.search.fixtures import SearchFixtureLoader
from modules.search.in_memory_adapter import InMemorySearchAdapter
from modules.search.query import SearchQuery


@pytest.fixture
async def indexed_adapter():
    """모든 픽스처 문서를 색인한 InMemorySearchAdapter를 반환한다."""
    adapter = InMemorySearchAdapter()
    for document in SearchFixtureLoader.load_all():
        await adapter.index(document)
    return adapter


class TestSearchQualityBaseline:
    """search-quality-baseline.md의 질의별 기대 결과표를 검증한다."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "term, expected_document_ids",
        [
            ("hello", {"fixture-title-only"}),
            ("apple", {"fixture-title-and-body"}),
            ("recipe", {"fixture-title-and-body"}),
            ("old title", {"fixture-redirect"}),
            ("new title", {"fixture-redirect"}),
            ("documentation", {"fixture-categorized", "fixture-full"}),
            ("wiki", {"fixture-categorized"}),
            ("search", {"fixture-full"}),
            ("nonexistent", set()),
        ],
    )
    async def test_query_matches_documented_baseline(
        self, indexed_adapter, term, expected_document_ids
    ):
        results = await indexed_adapter.search(SearchQuery(term=term))

        result_ids = {result.document.document_id for result in results}
        assert result_ids == expected_document_ids

    @pytest.mark.asyncio
    async def test_every_match_has_baseline_score_of_one(self, indexed_adapter):
        """현재는 순위 매기기가 없어 모든 일치 결과의 점수가 1.0으로 동일하다."""
        results = await indexed_adapter.search(SearchQuery(term="documentation"))

        assert len(results) > 0
        assert all(result.score == 1.0 for result in results)
