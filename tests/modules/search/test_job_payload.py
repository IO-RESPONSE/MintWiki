"""문서 색인 작업 페이로드 테스트."""
import pytest

from modules.search import SEARCH_INDEX_VERSION
from modules.search.document import (
    SearchDocument,
    EmptySearchDocumentIdError,
    EmptySearchDocumentTitleError,
)
from modules.search.job_payload import IndexDocumentJobPayload


class TestIndexDocumentJobPayloadConstruction:
    """문서 색인 작업 페이로드 생성 테스트."""

    def test_creates_payload_with_required_fields(self):
        """필수 필드(document_id, title)만으로 페이로드를 생성한다."""
        payload = IndexDocumentJobPayload(document_id="doc1", title="My Document")

        assert payload.document_id == "doc1"
        assert payload.title == "My Document"
        assert payload.body == ""
        assert payload.redirect_target is None
        assert payload.categories == []

    def test_creates_payload_with_all_fields(self):
        """모든 필드를 지정하여 페이로드를 생성한다."""
        payload = IndexDocumentJobPayload(
            document_id="doc2",
            title="Another Document",
            body="본문 내용입니다.",
            redirect_target="doc1",
            categories=["Wiki", "Technology"],
        )

        assert payload.document_id == "doc2"
        assert payload.title == "Another Document"
        assert payload.body == "본문 내용입니다."
        assert payload.redirect_target == "doc1"
        assert payload.categories == ["Wiki", "Technology"]

    def test_rejects_empty_document_id(self):
        """빈 문서 id로 페이로드를 생성할 수 없다."""
        with pytest.raises(EmptySearchDocumentIdError):
            IndexDocumentJobPayload(document_id="", title="Title")

    def test_rejects_empty_title(self):
        """빈 제목으로 페이로드를 생성할 수 없다."""
        with pytest.raises(EmptySearchDocumentTitleError):
            IndexDocumentJobPayload(document_id="doc1", title="")


class TestIndexDocumentJobPayloadIndexVersion:
    """페이로드에 담긴 색인 버전 정보 테스트."""

    def test_defaults_to_search_index_version_constant(self):
        """index_version을 지정하지 않으면 SEARCH_INDEX_VERSION을 사용한다."""
        payload = IndexDocumentJobPayload(document_id="doc1", title="My Document")

        assert payload.index_version == SEARCH_INDEX_VERSION

    def test_accepts_explicit_index_version_override(self):
        """index_version을 명시하면 해당 값을 그대로 사용한다."""
        payload = IndexDocumentJobPayload(
            document_id="doc1",
            title="My Document",
            index_version="2.0.0",
        )

        assert payload.index_version == "2.0.0"


class TestIndexDocumentJobPayloadToSearchDocument:
    """페이로드를 SearchDocument로 변환하는 기능 테스트."""

    def test_converts_to_search_document_with_required_fields(self):
        """필수 필드만 있는 페이로드를 SearchDocument로 변환한다."""
        payload = IndexDocumentJobPayload(document_id="doc1", title="My Document")

        doc = payload.to_search_document()

        assert isinstance(doc, SearchDocument)
        assert doc.document_id == "doc1"
        assert doc.title == "My Document"
        assert doc.body == ""
        assert doc.redirect_target is None
        assert doc.categories == []

    def test_converts_to_search_document_with_all_fields(self):
        """모든 필드가 채워진 페이로드를 SearchDocument로 변환한다."""
        payload = IndexDocumentJobPayload(
            document_id="doc2",
            title="Another Document",
            body="본문 내용입니다.",
            redirect_target="doc1",
            categories=["Wiki", "Technology"],
        )

        doc = payload.to_search_document()

        assert doc.document_id == "doc2"
        assert doc.title == "Another Document"
        assert doc.body == "본문 내용입니다."
        assert doc.redirect_target == "doc1"
        assert doc.categories == ["Wiki", "Technology"]
        assert doc.is_redirect() is True
