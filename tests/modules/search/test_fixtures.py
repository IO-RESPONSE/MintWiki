"""검색 픽스처 로더와 픽스처 문서 형식을 검증한다."""
import pytest

from modules.search.document import SearchDocument
from modules.search.fixtures import SearchFixtureLoader


class TestSearchFixtureLoaderLoadAll:
    """load_all이 반환하는 픽스처 문서 목록의 형식을 검증한다."""

    def test_loads_all_fixtures(self):
        documents = SearchFixtureLoader.load_all()
        assert len(documents) > 0

    def test_returns_list_of_search_documents(self):
        documents = SearchFixtureLoader.load_all()
        assert all(isinstance(doc, SearchDocument) for doc in documents)

    def test_fixture_document_ids_are_unique(self):
        documents = SearchFixtureLoader.load_all()
        ids = [doc.document_id for doc in documents]
        assert len(ids) == len(set(ids))


class TestSearchFixtureLoaderLoadById:
    """load_by_id가 id로 픽스처 문서를 조회하는 동작을 검증한다."""

    def test_loads_known_fixture(self):
        document = SearchFixtureLoader.load_by_id("fixture-title-only")
        assert document.document_id == "fixture-title-only"

    def test_raises_error_for_unknown_fixture(self):
        with pytest.raises(ValueError, match="Unknown fixture document"):
            SearchFixtureLoader.load_by_id("nonexistent-fixture")


class TestSearchFixtureScenarios:
    """개별 시나리오 픽스처 문서의 세부 내용을 검증한다."""

    def test_title_only_document_has_no_body(self):
        document = SearchFixtureLoader.load_by_id("fixture-title-only")
        assert document.body == ""
        assert not document.is_redirect()
        assert document.categories == []

    def test_title_and_body_document_has_body(self):
        document = SearchFixtureLoader.load_by_id("fixture-title-and-body")
        assert document.body != ""

    def test_redirect_document_is_a_redirect(self):
        document = SearchFixtureLoader.load_by_id("fixture-redirect")
        assert document.is_redirect()
        assert document.redirect_target == "New Title"

    def test_categorized_document_has_categories(self):
        document = SearchFixtureLoader.load_by_id("fixture-categorized")
        assert len(document.categories) > 0

    def test_full_document_has_title_body_and_categories(self):
        document = SearchFixtureLoader.load_by_id("fixture-full")
        assert document.title
        assert document.body != ""
        assert len(document.categories) > 0
