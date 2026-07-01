"""문서 저장소 인터페이스 테스트."""
import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from modules.document.model import Document
from modules.document.repository import (
    DocumentRepository,
    DuplicateNormalizedTitleError,
    InMemoryDocumentRepository,
    DatabaseDocumentRepository,
)
from persistence.base import Base
from persistence.models import DocumentORM


class ConcreteRepository(DocumentRepository):
    """테스트용 구체적인 저장소 구현."""

    def __init__(self):
        """저장소를 초기화한다."""
        self.documents = {}

    async def create(self, document: Document) -> Document:
        """문서를 저장소에 저장한다."""
        self.documents[document.id] = document
        return document

    async def get(self, id: str) -> Document | None:
        """id로 문서를 조회한다."""
        return self.documents.get(id)

    async def get_by_normalized_title(self, normalized_title: str) -> Document | None:
        """정규화된 제목으로 문서를 조회한다."""
        for doc in self.documents.values():
            if doc.normalized_title == normalized_title:
                return doc
        return None

    async def update(self, document: Document) -> Document:
        """기존 문서를 업데이트한다."""
        if document.id not in self.documents:
            raise KeyError(f"문서 id '{document.id}'를 찾을 수 없습니다")
        self.documents[document.id] = document
        return document


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

    @pytest.mark.asyncio
    async def test_concrete_implementation_can_create_document(self):
        """구체적인 구현은 문서를 생성할 수 있다."""
        repo = ConcreteRepository()
        doc = Document(id="doc1", title="Test Document")
        result = await repo.create(doc)
        assert result.id == "doc1"
        assert result.title == "Test Document"

    @pytest.mark.asyncio
    async def test_concrete_implementation_can_get_document_by_id(self):
        """구체적인 구현은 id로 문서를 조회할 수 있다."""
        repo = ConcreteRepository()
        doc = Document(id="doc1", title="Test Document")
        await repo.create(doc)
        result = await repo.get("doc1")
        assert result is not None
        assert result.id == "doc1"

    @pytest.mark.asyncio
    async def test_concrete_implementation_returns_none_for_missing_id(self):
        """구체적인 구현은 없는 문서를 조회하면 None을 반환한다."""
        repo = ConcreteRepository()
        result = await repo.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_concrete_implementation_can_get_document_by_normalized_title(self):
        """구체적인 구현은 정규화된 제목으로 문서를 조회할 수 있다."""
        repo = ConcreteRepository()
        doc = Document(id="doc1", title="Test Document")
        await repo.create(doc)
        result = await repo.get_by_normalized_title("Test Document")
        assert result is not None
        assert result.id == "doc1"

    @pytest.mark.asyncio
    async def test_concrete_implementation_returns_none_for_missing_normalized_title(self):
        """구체적인 구현은 없는 정규화된 제목을 조회하면 None을 반환한다."""
        repo = ConcreteRepository()
        result = await repo.get_by_normalized_title("Nonexistent Title")
        assert result is None


class TestInMemoryDocumentRepository:
    """인메모리 저장소 구현 테스트."""

    @pytest.mark.asyncio
    async def test_can_create_document(self):
        """인메모리 저장소는 문서를 생성할 수 있다."""
        repo = InMemoryDocumentRepository()
        doc = Document(id="doc1", title="Test Document")
        result = await repo.create(doc)
        assert result.id == "doc1"
        assert result.title == "Test Document"

    @pytest.mark.asyncio
    async def test_can_fetch_document_by_id(self):
        """인메모리 저장소는 id로 문서를 조회할 수 있다."""
        repo = InMemoryDocumentRepository()
        doc = Document(id="doc1", title="Test Document")
        await repo.create(doc)
        result = await repo.get("doc1")
        assert result is not None
        assert result.id == "doc1"
        assert result.title == "Test Document"

    @pytest.mark.asyncio
    async def test_returns_none_for_missing_id(self):
        """인메모리 저장소는 없는 id를 조회하면 None을 반환한다."""
        repo = InMemoryDocumentRepository()
        result = await repo.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_can_fetch_document_by_normalized_title(self):
        """인메모리 저장소는 정규화된 제목으로 문서를 조회할 수 있다."""
        repo = InMemoryDocumentRepository()
        doc = Document(id="doc1", title="Test Document")
        await repo.create(doc)
        result = await repo.get_by_normalized_title("Test Document")
        assert result is not None
        assert result.id == "doc1"

    @pytest.mark.asyncio
    async def test_can_fetch_document_by_normalized_title_with_spaces(self):
        """인메모리 저장소는 공백이 다른 제목도 정규화하여 조회할 수 있다."""
        repo = InMemoryDocumentRepository()
        doc = Document(id="doc1", title="  Test   Document  ")
        await repo.create(doc)
        result = await repo.get_by_normalized_title("Test Document")
        assert result is not None
        assert result.id == "doc1"

    @pytest.mark.asyncio
    async def test_returns_none_for_missing_normalized_title(self):
        """인메모리 저장소는 없는 정규화된 제목을 조회하면 None을 반환한다."""
        repo = InMemoryDocumentRepository()
        result = await repo.get_by_normalized_title("Nonexistent Title")
        assert result is None

    @pytest.mark.asyncio
    async def test_rejects_duplicate_normalized_title(self):
        """인메모리 저장소는 중복된 정규화된 제목을 거부한다."""
        repo = InMemoryDocumentRepository()
        doc1 = Document(id="doc1", title="Test Document")
        await repo.create(doc1)

        doc2 = Document(id="doc2", title="Test Document")
        with pytest.raises(DuplicateNormalizedTitleError):
            await repo.create(doc2)

    @pytest.mark.asyncio
    async def test_rejects_duplicate_normalized_title_with_different_spaces(self):
        """인메모리 저장소는 정규화 후 중복인 제목을 거부한다."""
        repo = InMemoryDocumentRepository()
        doc1 = Document(id="doc1", title="Test Document")
        await repo.create(doc1)

        doc2 = Document(id="doc2", title="  Test   Document  ")
        with pytest.raises(DuplicateNormalizedTitleError):
            await repo.create(doc2)

    @pytest.mark.asyncio
    async def test_stores_multiple_documents(self):
        """인메모리 저장소는 여러 문서를 저장할 수 있다."""
        repo = InMemoryDocumentRepository()
        doc1 = Document(id="doc1", title="Document One")
        doc2 = Document(id="doc2", title="Document Two")
        doc3 = Document(id="doc3", title="Document Three")

        await repo.create(doc1)
        await repo.create(doc2)
        await repo.create(doc3)

        assert await repo.get("doc1") is not None
        assert await repo.get("doc2") is not None
        assert await repo.get("doc3") is not None
        assert await repo.get_by_normalized_title("Document One") is not None
        assert await repo.get_by_normalized_title("Document Two") is not None
        assert await repo.get_by_normalized_title("Document Three") is not None


@pytest.fixture
async def async_db_session():
    """테스트용 인메모리 SQLite 데이터베이스 세션을 생성한다."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    await engine.dispose()


class TestDatabaseDocumentRepository:
    """데이터베이스 저장소 구현 테스트."""

    @pytest.mark.asyncio
    async def test_can_create_document(self, async_db_session):
        """데이터베이스 저장소는 문서를 생성할 수 있다."""
        repo = DatabaseDocumentRepository(async_db_session)
        doc = Document(id="doc1", title="Test Document")
        result = await repo.create(doc)
        assert result.id == "doc1"
        assert result.title == "Test Document"

    @pytest.mark.asyncio
    async def test_can_fetch_document_by_id(self, async_db_session):
        """데이터베이스 저장소는 id로 문서를 조회할 수 있다."""
        repo = DatabaseDocumentRepository(async_db_session)
        doc = Document(id="doc1", title="Test Document")
        await repo.create(doc)
        result = await repo.get("doc1")
        assert result is not None
        assert result.id == "doc1"
        assert result.title == "Test Document"

    @pytest.mark.asyncio
    async def test_returns_none_for_missing_id(self, async_db_session):
        """데이터베이스 저장소는 없는 id를 조회하면 None을 반환한다."""
        repo = DatabaseDocumentRepository(async_db_session)
        result = await repo.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_can_fetch_document_by_normalized_title(self, async_db_session):
        """데이터베이스 저장소는 정규화된 제목으로 문서를 조회할 수 있다."""
        repo = DatabaseDocumentRepository(async_db_session)
        doc = Document(id="doc1", title="Test Document")
        await repo.create(doc)
        result = await repo.get_by_normalized_title("Test Document")
        assert result is not None
        assert result.id == "doc1"

    @pytest.mark.asyncio
    async def test_can_fetch_document_by_normalized_title_with_spaces(self, async_db_session):
        """데이터베이스 저장소는 공백이 다른 제목도 정규화하여 조회할 수 있다."""
        repo = DatabaseDocumentRepository(async_db_session)
        doc = Document(id="doc1", title="  Test   Document  ")
        await repo.create(doc)
        result = await repo.get_by_normalized_title("Test Document")
        assert result is not None
        assert result.id == "doc1"

    @pytest.mark.asyncio
    async def test_returns_none_for_missing_normalized_title(self, async_db_session):
        """데이터베이스 저장소는 없는 정규화된 제목을 조회하면 None을 반환한다."""
        repo = DatabaseDocumentRepository(async_db_session)
        result = await repo.get_by_normalized_title("Nonexistent Title")
        assert result is None

    @pytest.mark.asyncio
    async def test_rejects_duplicate_normalized_title(self, async_db_session):
        """데이터베이스 저장소는 중복된 정규화된 제목을 거부한다."""
        repo = DatabaseDocumentRepository(async_db_session)
        doc1 = Document(id="doc1", title="Test Document")
        await repo.create(doc1)

        doc2 = Document(id="doc2", title="Test Document")
        with pytest.raises(DuplicateNormalizedTitleError):
            await repo.create(doc2)

    @pytest.mark.asyncio
    async def test_rejects_duplicate_normalized_title_with_different_spaces(self, async_db_session):
        """데이터베이스 저장소는 정규화 후 중복인 제목을 거부한다."""
        repo = DatabaseDocumentRepository(async_db_session)
        doc1 = Document(id="doc1", title="Test Document")
        await repo.create(doc1)

        doc2 = Document(id="doc2", title="  Test   Document  ")
        with pytest.raises(DuplicateNormalizedTitleError):
            await repo.create(doc2)

    @pytest.mark.asyncio
    async def test_stores_multiple_documents(self, async_db_session):
        """데이터베이스 저장소는 여러 문서를 저장할 수 있다."""
        repo = DatabaseDocumentRepository(async_db_session)
        doc1 = Document(id="doc1", title="Document One")
        doc2 = Document(id="doc2", title="Document Two")
        doc3 = Document(id="doc3", title="Document Three")

        await repo.create(doc1)
        await repo.create(doc2)
        await repo.create(doc3)

        assert await repo.get("doc1") is not None
        assert await repo.get("doc2") is not None
        assert await repo.get("doc3") is not None
        assert await repo.get_by_normalized_title("Document One") is not None
        assert await repo.get_by_normalized_title("Document Two") is not None
        assert await repo.get_by_normalized_title("Document Three") is not None

    @pytest.mark.asyncio
    async def test_get_preserves_all_document_properties(self, async_db_session):
        """데이터베이스 저장소는 조회 시 문서의 모든 속성을 유지한다."""
        repo = DatabaseDocumentRepository(async_db_session)
        doc = Document(id="doc1", title="  Test   Document  ")
        await repo.create(doc)
        result = await repo.get("doc1")

        assert result is not None
        assert result.id == "doc1"
        assert result.title == "  Test   Document  "
        assert result.normalized_title == "Test Document"
        assert result.current_revision_id is None

    @pytest.mark.asyncio
    async def test_get_with_uuid_id(self, async_db_session):
        """데이터베이스 저장소는 UUID 형식의 id로 문서를 조회할 수 있다."""
        repo = DatabaseDocumentRepository(async_db_session)
        doc_id = str(uuid.uuid4())
        doc = Document(id=doc_id, title="UUID Test Document")
        await repo.create(doc)

        result = await repo.get(doc_id)
        assert result is not None
        assert result.id == doc_id
        assert result.title == "UUID Test Document"

    @pytest.mark.asyncio
    async def test_get_returns_correct_document_from_multiple(self, async_db_session):
        """데이터베이스 저장소는 여러 문서 중 올바른 문서를 조회한다."""
        repo = DatabaseDocumentRepository(async_db_session)
        doc1 = Document(id="doc1", title="First Document")
        doc2 = Document(id="doc2", title="Second Document")
        doc3 = Document(id="doc3", title="Third Document")

        await repo.create(doc1)
        await repo.create(doc2)
        await repo.create(doc3)

        result = await repo.get("doc2")
        assert result is not None
        assert result.id == "doc2"
        assert result.title == "Second Document"
        assert result.normalized_title == "Second Document"

    @pytest.mark.asyncio
    async def test_get_with_special_characters_in_title(self, async_db_session):
        """데이터베이스 저장소는 특수 문자가 있는 제목의 문서를 조회할 수 있다."""
        repo = DatabaseDocumentRepository(async_db_session)
        doc = Document(id="doc1", title="Document with 특수 문자 & symbols!")
        await repo.create(doc)

        result = await repo.get("doc1")
        assert result is not None
        assert result.title == "Document with 특수 문자 & symbols!"

    @pytest.mark.asyncio
    async def test_get_by_normalized_title_preserves_all_document_properties(self, async_db_session):
        """데이터베이스 저장소는 정규화된 제목으로 조회 시 문서의 모든 속성을 유지한다."""
        repo = DatabaseDocumentRepository(async_db_session)
        doc = Document(id="doc1", title="  Test   Document  ")
        await repo.create(doc)
        result = await repo.get_by_normalized_title("Test Document")

        assert result is not None
        assert result.id == "doc1"
        assert result.title == "  Test   Document  "
        assert result.normalized_title == "Test Document"
        assert result.current_revision_id is None

    @pytest.mark.asyncio
    async def test_get_by_normalized_title_with_uuid_id(self, async_db_session):
        """데이터베이스 저장소는 정규화된 제목으로 UUID 형식의 id 문서를 조회할 수 있다."""
        repo = DatabaseDocumentRepository(async_db_session)
        doc_id = str(uuid.uuid4())
        doc = Document(id=doc_id, title="UUID Test Document")
        await repo.create(doc)

        result = await repo.get_by_normalized_title("UUID Test Document")
        assert result is not None
        assert result.id == doc_id
        assert result.title == "UUID Test Document"

    @pytest.mark.asyncio
    async def test_get_by_normalized_title_returns_correct_document_from_multiple(self, async_db_session):
        """데이터베이스 저장소는 정규화된 제목으로 여러 문서 중 올바른 문서를 조회한다."""
        repo = DatabaseDocumentRepository(async_db_session)
        doc1 = Document(id="doc1", title="First Document")
        doc2 = Document(id="doc2", title="Second Document")
        doc3 = Document(id="doc3", title="Third Document")

        await repo.create(doc1)
        await repo.create(doc2)
        await repo.create(doc3)

        result = await repo.get_by_normalized_title("Second Document")
        assert result is not None
        assert result.id == "doc2"
        assert result.title == "Second Document"
        assert result.normalized_title == "Second Document"

    @pytest.mark.asyncio
    async def test_get_by_normalized_title_with_special_characters_in_title(self, async_db_session):
        """데이터베이스 저장소는 정규화된 제목으로 특수 문자가 있는 제목의 문서를 조회할 수 있다."""
        repo = DatabaseDocumentRepository(async_db_session)
        doc = Document(id="doc1", title="Document with 특수 문자 & symbols!")
        await repo.create(doc)

        result = await repo.get_by_normalized_title("Document with 특수 문자 & symbols!")
        assert result is not None
        assert result.title == "Document with 특수 문자 & symbols!"
        assert result.normalized_title == "Document with 특수 문자 & symbols!"
