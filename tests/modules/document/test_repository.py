"""문서 저장소 인터페이스 테스트."""
import pytest
from modules.document.model import Document
from modules.document.repository import DocumentRepository


class ConcreteRepository(DocumentRepository):
    """테스트용 구체적인 저장소 구현."""

    def __init__(self):
        """저장소를 초기화한다."""
        self.documents = {}

    def create(self, document: Document) -> Document:
        """문서를 저장소에 저장한다."""
        self.documents[document.id] = document
        return document

    def get(self, id: str) -> Document | None:
        """id로 문서를 조회한다."""
        return self.documents.get(id)

    def get_by_normalized_title(self, normalized_title: str) -> Document | None:
        """정규화된 제목으로 문서를 조회한다."""
        for doc in self.documents.values():
            if doc.normalized_title == normalized_title:
                return doc
        return None


class TestDocumentRepositoryInterface:
    """저장소 인터페이스 테스트."""

    def test_repository_is_abstract(self):
        """저장소는 추상 클래스이다."""
        with pytest.raises(TypeError):
            DocumentRepository()

    def test_create_method_exists(self):
        """저장소는 create 메서드를 정의한다."""
        assert hasattr(DocumentRepository, "create")

    def test_get_method_exists(self):
        """저장소는 get 메서드를 정의한다."""
        assert hasattr(DocumentRepository, "get")

    def test_get_by_normalized_title_method_exists(self):
        """저장소는 get_by_normalized_title 메서드를 정의한다."""
        assert hasattr(DocumentRepository, "get_by_normalized_title")

    def test_concrete_implementation_can_create_document(self):
        """구체적인 구현은 문서를 생성할 수 있다."""
        repo = ConcreteRepository()
        doc = Document(id="doc1", title="Test Document")
        result = repo.create(doc)
        assert result.id == "doc1"
        assert result.title == "Test Document"

    def test_concrete_implementation_can_get_document_by_id(self):
        """구체적인 구현은 id로 문서를 조회할 수 있다."""
        repo = ConcreteRepository()
        doc = Document(id="doc1", title="Test Document")
        repo.create(doc)
        result = repo.get("doc1")
        assert result is not None
        assert result.id == "doc1"

    def test_concrete_implementation_returns_none_for_missing_id(self):
        """구체적인 구현은 없는 문서를 조회하면 None을 반환한다."""
        repo = ConcreteRepository()
        result = repo.get("nonexistent")
        assert result is None

    def test_concrete_implementation_can_get_document_by_normalized_title(self):
        """구체적인 구현은 정규화된 제목으로 문서를 조회할 수 있다."""
        repo = ConcreteRepository()
        doc = Document(id="doc1", title="Test Document")
        repo.create(doc)
        result = repo.get_by_normalized_title("Test Document")
        assert result is not None
        assert result.id == "doc1"

    def test_concrete_implementation_returns_none_for_missing_normalized_title(self):
        """구체적인 구현은 없는 정규화된 제목을 조회하면 None을 반환한다."""
        repo = ConcreteRepository()
        result = repo.get_by_normalized_title("Nonexistent Title")
        assert result is None
