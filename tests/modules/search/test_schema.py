"""검색 색인 요청 스키마 테스트."""
import pytest
from pydantic import ValidationError

from modules.search.schema import IndexDocumentRequest


class TestIndexDocumentRequestConstruction:
    """검색 색인 요청 스키마 생성 테스트."""

    def test_creates_request_with_required_fields(self):
        """필수 필드(document_id, title)만으로 요청을 생성한다."""
        request = IndexDocumentRequest(document_id="doc1", title="My Document")

        assert request.document_id == "doc1"
        assert request.title == "My Document"
        assert request.body == ""
        assert request.redirect_target is None
        assert request.categories == []

    def test_creates_request_with_all_fields(self):
        """모든 필드를 지정하여 요청을 생성한다."""
        request = IndexDocumentRequest(
            document_id="doc2",
            title="Another Document",
            body="본문 내용입니다.",
            redirect_target="doc1",
            categories=["Wiki", "Technology"],
        )

        assert request.document_id == "doc2"
        assert request.title == "Another Document"
        assert request.body == "본문 내용입니다."
        assert request.redirect_target == "doc1"
        assert request.categories == ["Wiki", "Technology"]

    def test_rejects_missing_document_id(self):
        """document_id가 없으면 검증 오류가 발생한다."""
        with pytest.raises(ValidationError):
            IndexDocumentRequest(title="Title")

    def test_rejects_missing_title(self):
        """title이 없으면 검증 오류가 발생한다."""
        with pytest.raises(ValidationError):
            IndexDocumentRequest(document_id="doc1")
