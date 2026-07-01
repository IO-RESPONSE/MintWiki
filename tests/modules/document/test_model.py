"""문서 모델 테스트."""
import pytest
from modules.document.model import Document
from modules.document.title import EmptyTitleError


class TestDocumentConstruction:
    """문서 생성 테스트."""

    def test_creates_document_with_required_fields(self):
        """필수 필드로 문서를 생성한다."""
        doc = Document(id="doc1", title="My Document")
        assert doc.id == "doc1"
        assert doc.title == "My Document"
        assert doc.normalized_title == "My Document"
        assert doc.current_revision_id is None

    def test_creates_document_without_current_revision(self):
        """현재 리비전 없이 문서를 생성한다."""
        doc = Document(
            id="doc2",
            title="Another Document",
        )
        assert doc.id == "doc2"
        assert doc.title == "Another Document"
        assert doc.current_revision_id is None

    def test_creates_document_with_current_revision(self):
        """현재 리비전을 포함하여 문서를 생성한다."""
        doc = Document(
            id="doc3",
            title="Document with Revision",
            current_revision_id="rev1",
        )
        assert doc.id == "doc3"
        assert doc.title == "Document with Revision"
        assert doc.current_revision_id == "rev1"

    def test_normalizes_title_on_creation(self):
        """생성 시 제목을 정규화한다."""
        doc = Document(id="doc4", title="  Title  with   spaces  ")
        assert doc.title == "  Title  with   spaces  "
        assert doc.normalized_title == "Title with spaces"

    def test_preserves_normalized_title_with_unicode(self):
        """유니코드 제목을 정규화한다."""
        doc = Document(id="doc5", title="  한글 제목  ")
        assert doc.title == "  한글 제목  "
        assert doc.normalized_title == "한글 제목"

    def test_rejects_empty_title(self):
        """빈 제목으로 문서를 생성할 수 없다."""
        with pytest.raises(EmptyTitleError):
            Document(id="doc6", title="")

    def test_rejects_whitespace_only_title(self):
        """공백만 있는 제목으로 문서를 생성할 수 없다."""
        with pytest.raises(EmptyTitleError):
            Document(id="doc7", title="   ")
