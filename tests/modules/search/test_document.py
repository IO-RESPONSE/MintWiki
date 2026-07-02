"""검색 문서 모델 테스트."""
import pytest
from modules.search.document import (
    SearchDocument,
    EmptySearchDocumentIdError,
    EmptySearchDocumentTitleError,
)


class TestSearchDocumentConstruction:
    """검색 문서 생성 테스트."""

    def test_creates_search_document_with_required_fields(self):
        """필수 필드로 검색 문서를 생성한다."""
        doc = SearchDocument(document_id="doc1", title="My Document")
        assert doc.document_id == "doc1"
        assert doc.title == "My Document"
        assert doc.body == ""
        assert doc.redirect_target is None

    def test_creates_search_document_with_body(self):
        """본문을 포함하여 검색 문서를 생성한다."""
        doc = SearchDocument(
            document_id="doc2",
            title="Another Document",
            body="본문 내용입니다.",
        )
        assert doc.body == "본문 내용입니다."

    def test_creates_search_document_with_redirect_target(self):
        """리다이렉트 대상을 포함하여 검색 문서를 생성한다."""
        doc = SearchDocument(
            document_id="doc3",
            title="Redirect Document",
            redirect_target="doc1",
        )
        assert doc.redirect_target == "doc1"

    def test_rejects_empty_document_id(self):
        """빈 문서 id로 검색 문서를 생성할 수 없다."""
        with pytest.raises(EmptySearchDocumentIdError):
            SearchDocument(document_id="", title="Title")

    def test_rejects_whitespace_only_document_id(self):
        """공백만 있는 문서 id로 검색 문서를 생성할 수 없다."""
        with pytest.raises(EmptySearchDocumentIdError):
            SearchDocument(document_id="   ", title="Title")

    def test_rejects_empty_title(self):
        """빈 제목으로 검색 문서를 생성할 수 없다."""
        with pytest.raises(EmptySearchDocumentTitleError):
            SearchDocument(document_id="doc4", title="")

    def test_rejects_whitespace_only_title(self):
        """공백만 있는 제목으로 검색 문서를 생성할 수 없다."""
        with pytest.raises(EmptySearchDocumentTitleError):
            SearchDocument(document_id="doc5", title="   ")


class TestSearchDocumentIsRedirect:
    """검색 문서의 리다이렉트 여부 판별 테스트."""

    def test_is_redirect_false_by_default(self):
        """리다이렉트 대상이 없으면 리다이렉트 문서가 아니다."""
        doc = SearchDocument(document_id="doc1", title="Title")
        assert doc.is_redirect() is False

    def test_is_redirect_true_when_target_set(self):
        """리다이렉트 대상이 있으면 리다이렉트 문서이다."""
        doc = SearchDocument(
            document_id="doc1", title="Title", redirect_target="doc2"
        )
        assert doc.is_redirect() is True
