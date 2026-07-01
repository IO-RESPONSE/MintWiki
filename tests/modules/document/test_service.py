"""문서 서비스 테스트."""
import pytest
from modules.document.repository import (
    DuplicateNormalizedTitleError,
    InMemoryDocumentRepository,
)
from modules.document.service import DocumentService
from modules.document.title import EmptyTitleError


class TestDocumentService:
    """문서 서비스 테스트."""

    def test_create_document_with_title(self):
        """서비스는 제목으로 문서를 생성할 수 있다."""
        repo = InMemoryDocumentRepository()
        service = DocumentService(repo)

        doc = service.create("My Document")

        assert doc.id is not None
        assert doc.title == "My Document"
        assert doc.normalized_title == "My Document"
        assert doc.current_revision_id is None

    def test_create_normalizes_title(self):
        """서비스는 제목을 정규화한다."""
        repo = InMemoryDocumentRepository()
        service = DocumentService(repo)

        doc = service.create("  My   Document  ")

        assert doc.title == "  My   Document  "
        assert doc.normalized_title == "My Document"

    def test_create_generates_unique_id(self):
        """서비스는 각 문서에 고유한 id를 생성한다."""
        repo = InMemoryDocumentRepository()
        service = DocumentService(repo)

        doc1 = service.create("Document One")
        doc2 = service.create("Document Two")

        assert doc1.id != doc2.id

    def test_create_delegates_to_repository(self):
        """서비스는 저장소에 문서 생성을 위임한다."""
        repo = InMemoryDocumentRepository()
        service = DocumentService(repo)

        doc = service.create("My Document")

        retrieved = repo.get(doc.id)
        assert retrieved is not None
        assert retrieved.title == "My Document"

    def test_create_raises_on_empty_title(self):
        """서비스는 빈 제목으로 생성하면 예외를 발생시킨다."""
        repo = InMemoryDocumentRepository()
        service = DocumentService(repo)

        with pytest.raises(EmptyTitleError):
            service.create("")

    def test_create_raises_on_whitespace_only_title(self):
        """서비스는 공백만 있는 제목으로 생성하면 예외를 발생시킨다."""
        repo = InMemoryDocumentRepository()
        service = DocumentService(repo)

        with pytest.raises(EmptyTitleError):
            service.create("   ")

    def test_create_raises_on_duplicate_normalized_title(self):
        """서비스는 정규화된 제목이 중복되면 예외를 발생시킨다."""
        repo = InMemoryDocumentRepository()
        service = DocumentService(repo)

        service.create("My Document")

        with pytest.raises(DuplicateNormalizedTitleError):
            service.create("My Document")

    def test_create_raises_on_duplicate_normalized_title_with_spaces(self):
        """서비스는 공백이 다른 중복된 제목도 감지한다."""
        repo = InMemoryDocumentRepository()
        service = DocumentService(repo)

        service.create("My Document")

        with pytest.raises(DuplicateNormalizedTitleError):
            service.create("  My   Document  ")

    def test_create_allows_different_normalized_titles(self):
        """서비스는 정규화된 제목이 다르면 같은 원본 제목도 허용한다."""
        repo = InMemoryDocumentRepository()
        service = DocumentService(repo)

        doc1 = service.create("Document One")
        doc2 = service.create("Document Two")

        assert doc1.normalized_title != doc2.normalized_title
        assert repo.get(doc1.id) is not None
        assert repo.get(doc2.id) is not None

    def test_get_document_by_id(self):
        """서비스는 id로 문서를 조회할 수 있다."""
        repo = InMemoryDocumentRepository()
        service = DocumentService(repo)

        created = service.create("My Document")
        retrieved = service.get(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.title == "My Document"

    def test_get_document_by_id_not_found(self):
        """서비스는 존재하지 않는 id를 조회하면 None을 반환한다."""
        repo = InMemoryDocumentRepository()
        service = DocumentService(repo)

        result = service.get("nonexistent-id")

        assert result is None

    def test_get_document_by_title(self):
        """서비스는 제목으로 문서를 조회할 수 있다."""
        repo = InMemoryDocumentRepository()
        service = DocumentService(repo)

        created = service.create("My Document")
        retrieved = service.get_by_title("My Document")

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.title == "My Document"

    def test_get_document_by_title_with_different_spacing(self):
        """서비스는 공백이 다른 제목도 정규화하여 조회할 수 있다."""
        repo = InMemoryDocumentRepository()
        service = DocumentService(repo)

        created = service.create("My Document")
        retrieved = service.get_by_title("  My   Document  ")

        assert retrieved is not None
        assert retrieved.id == created.id

    def test_get_document_by_title_not_found(self):
        """서비스는 존재하지 않는 제목을 조회하면 None을 반환한다."""
        repo = InMemoryDocumentRepository()
        service = DocumentService(repo)

        result = service.get_by_title("Nonexistent Document")

        assert result is None

    def test_get_by_title_raises_on_empty_title(self):
        """서비스는 빈 제목으로 조회하면 예외를 발생시킨다."""
        repo = InMemoryDocumentRepository()
        service = DocumentService(repo)

        with pytest.raises(EmptyTitleError):
            service.get_by_title("")

    def test_get_by_title_raises_on_whitespace_only_title(self):
        """서비스는 공백만 있는 제목으로 조회하면 예외를 발생시킨다."""
        repo = InMemoryDocumentRepository()
        service = DocumentService(repo)

        with pytest.raises(EmptyTitleError):
            service.get_by_title("   ")
