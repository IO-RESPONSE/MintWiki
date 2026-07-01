"""문서 영속성 테스트."""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from modules.document.repository import DatabaseDocumentRepository
from modules.document.service import DocumentService
from persistence.base import Base


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


class TestDocumentPersistenceBasics:
    """문서 영속성 기본 테스트."""

    @pytest.mark.asyncio
    async def test_persisted_document_can_be_retrieved(self, async_db_session):
        """저장된 문서를 조회할 수 있다."""
        repo = DatabaseDocumentRepository(async_db_session)
        service = DocumentService(repo)

        created = await service.create(title="Test Document")
        document_id = created.id

        retrieved = await service.get(document_id)

        assert retrieved is not None
        assert retrieved.id == document_id
        assert retrieved.title == "Test Document"
        assert retrieved.normalized_title == "Test Document"

    @pytest.mark.asyncio
    async def test_persisted_document_with_unicode_title(self, async_db_session):
        """유니코드 제목을 가진 문서를 저장하고 검색할 수 있다."""
        repo = DatabaseDocumentRepository(async_db_session)
        service = DocumentService(repo)

        created = await service.create(title="한글 문서 📝")

        retrieved = await service.get(created.id)

        assert retrieved is not None
        assert retrieved.title == "한글 문서 📝"

    @pytest.mark.asyncio
    async def test_persisted_document_with_special_characters_in_title(
        self, async_db_session
    ):
        """특수 문자가 있는 제목의 문서를 저장하고 검색할 수 있다."""
        repo = DatabaseDocumentRepository(async_db_session)
        service = DocumentService(repo)

        created = await service.create(title="Document with !@#$%^&*()")

        retrieved = await service.get(created.id)

        assert retrieved is not None
        assert retrieved.title == "Document with !@#$%^&*()"

    @pytest.mark.asyncio
    async def test_persisted_document_normalizes_title_with_spaces(
        self, async_db_session
    ):
        """여러 공백이 있는 제목을 정규화하여 저장한다."""
        repo = DatabaseDocumentRepository(async_db_session)
        service = DocumentService(repo)

        created = await service.create(title="  Test   Document   Title  ")

        retrieved = await service.get(created.id)

        assert retrieved is not None
        assert retrieved.title == "  Test   Document   Title  "
        assert retrieved.normalized_title == "Test Document Title"

    @pytest.mark.asyncio
    async def test_persisted_document_can_be_retrieved_by_title(
        self, async_db_session
    ):
        """저장된 문서를 제목으로 검색할 수 있다."""
        repo = DatabaseDocumentRepository(async_db_session)
        service = DocumentService(repo)

        created = await service.create(title="  Test   Document  ")

        retrieved = await service.get_by_title("Test Document")

        assert retrieved is not None
        assert retrieved.id == created.id

    @pytest.mark.asyncio
    async def test_persisted_document_current_revision_id_can_be_updated(
        self, async_db_session
    ):
        """저장된 문서의 현재 리비전 id를 업데이트할 수 있다."""
        repo = DatabaseDocumentRepository(async_db_session)
        service = DocumentService(repo)

        created = await service.create(title="Test Document")
        original_id = created.id

        # 현재 리비전 id 업데이트
        from modules.document.model import Document
        updated_doc = Document(
            id=original_id,
            title="Test Document",
            current_revision_id="rev1",
        )
        updated = await repo.update(updated_doc)

        assert updated.current_revision_id == "rev1"

        # 재로드: 변경이 유지되는지 확인
        retrieved = await service.get(original_id)
        assert retrieved.current_revision_id == "rev1"


class TestDocumentPersistenceDataIntegrity:
    """문서 영속성 데이터 무결성 테스트."""

    @pytest.mark.asyncio
    async def test_persisted_document_preserves_all_attributes(
        self, async_db_session
    ):
        """저장된 문서가 모든 속성을 보존한다."""
        repo = DatabaseDocumentRepository(async_db_session)
        service = DocumentService(repo)

        created = await service.create(title="Complete Document")

        retrieved = await service.get(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.title == "Complete Document"
        assert retrieved.normalized_title == "Complete Document"
        assert retrieved.current_revision_id is None

    @pytest.mark.asyncio
    async def test_persisted_document_retrieval_returns_exact_copy(
        self, async_db_session
    ):
        """저장된 문서 검색이 정확한 복사본을 반환한다."""
        repo = DatabaseDocumentRepository(async_db_session)
        service = DocumentService(repo)

        created = await service.create(title="Test Document")

        retrieved1 = await service.get(created.id)
        retrieved2 = await service.get(created.id)

        assert retrieved1.id == retrieved2.id
        assert retrieved1.title == retrieved2.title
        assert retrieved1.normalized_title == retrieved2.normalized_title
        assert retrieved1.current_revision_id == retrieved2.current_revision_id

    @pytest.mark.asyncio
    async def test_persisted_document_with_current_revision_id(
        self, async_db_session
    ):
        """현재 리비전 id를 가진 문서를 저장하고 검색할 수 있다."""
        repo = DatabaseDocumentRepository(async_db_session)
        service = DocumentService(repo)

        created = await service.create(title="Document with revision")
        doc_id = created.id

        from modules.document.model import Document
        updated_doc = Document(
            id=doc_id,
            title="Document with revision",
            current_revision_id="rev_123",
        )
        await repo.update(updated_doc)

        retrieved = await service.get(doc_id)

        assert retrieved is not None
        assert retrieved.current_revision_id == "rev_123"


class TestDocumentPersistenceIsolation:
    """문서 영속성 격리 테스트."""

    @pytest.mark.asyncio
    async def test_persisted_documents_are_isolated(self, async_db_session):
        """서로 다른 문서는 독립적으로 저장된다."""
        repo = DatabaseDocumentRepository(async_db_session)
        service = DocumentService(repo)

        doc1 = await service.create(title="Document One")
        doc2 = await service.create(title="Document Two")
        doc3 = await service.create(title="Document Three")

        retrieved1 = await service.get(doc1.id)
        retrieved2 = await service.get(doc2.id)
        retrieved3 = await service.get(doc3.id)

        assert retrieved1.title == "Document One"
        assert retrieved2.title == "Document Two"
        assert retrieved3.title == "Document Three"
        assert retrieved1.id == doc1.id
        assert retrieved2.id == doc2.id
        assert retrieved3.id == doc3.id

    @pytest.mark.asyncio
    async def test_persisted_documents_current_revision_ids_are_independent(
        self, async_db_session
    ):
        """여러 문서 각각은 독립적인 현재 리비전 id를 유지한다."""
        repo = DatabaseDocumentRepository(async_db_session)
        service = DocumentService(repo)

        doc1 = await service.create(title="Document One")
        doc2 = await service.create(title="Document Two")

        from modules.document.model import Document
        updated_doc1 = Document(
            id=doc1.id,
            title="Document One",
            current_revision_id="rev1_for_doc1",
        )
        updated_doc2 = Document(
            id=doc2.id,
            title="Document Two",
            current_revision_id="rev1_for_doc2",
        )
        await repo.update(updated_doc1)
        await repo.update(updated_doc2)

        retrieved1 = await service.get(doc1.id)
        retrieved2 = await service.get(doc2.id)

        assert retrieved1.current_revision_id == "rev1_for_doc1"
        assert retrieved2.current_revision_id == "rev1_for_doc2"


class TestDocumentPersistenceEdgeCases:
    """문서 영속성 엣지 케이스 테스트."""

    @pytest.mark.asyncio
    async def test_persisted_document_without_current_revision_id(
        self, async_db_session
    ):
        """현재 리비전 id가 없는 문서를 저장하고 검색할 수 있다."""
        repo = DatabaseDocumentRepository(async_db_session)
        service = DocumentService(repo)

        created = await service.create(title="Document without revision")

        retrieved = await service.get(created.id)

        assert retrieved is not None
        assert retrieved.current_revision_id is None

    @pytest.mark.asyncio
    async def test_persisted_document_with_tab_and_spaces_in_title(
        self, async_db_session
    ):
        """탭과 공백을 포함한 제목의 문서를 저장하고 검색할 수 있다."""
        repo = DatabaseDocumentRepository(async_db_session)
        service = DocumentService(repo)

        created = await service.create(title="Title\twith\ttabs and  spaces")

        retrieved = await service.get(created.id)

        assert retrieved is not None
        assert retrieved.title == "Title\twith\ttabs and  spaces"

    @pytest.mark.asyncio
    async def test_get_nonexistent_persisted_document_returns_none(
        self, async_db_session
    ):
        """존재하지 않는 문서를 조회하면 None을 반환한다."""
        repo = DatabaseDocumentRepository(async_db_session)
        service = DocumentService(repo)

        result = await service.get("nonexistent_document_id")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_title_nonexistent_returns_none(
        self, async_db_session
    ):
        """존재하지 않는 제목을 조회하면 None을 반환한다."""
        repo = DatabaseDocumentRepository(async_db_session)
        service = DocumentService(repo)

        result = await service.get_by_title("Nonexistent Title")

        assert result is None

    @pytest.mark.asyncio
    async def test_persisted_document_title_with_newlines(self, async_db_session):
        """제목에 줄바꿈 문자가 있는 문서를 저장하고 검색할 수 있다."""
        repo = DatabaseDocumentRepository(async_db_session)
        service = DocumentService(repo)

        title_with_newlines = "Line 1\nLine 2\nLine 3"

        created = await service.create(title=title_with_newlines)

        retrieved = await service.get(created.id)

        assert retrieved is not None
        assert retrieved.title == title_with_newlines
