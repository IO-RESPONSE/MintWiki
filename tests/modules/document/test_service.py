"""문서 서비스 테스트."""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from modules.document.repository import (
    DuplicateNormalizedTitleError,
    InMemoryDocumentRepository,
    DatabaseDocumentRepository,
)
from modules.document.service import DocumentService, CurrentRevisionReadModel
from modules.document.title import EmptyTitleError
from modules.revision.repository import (
    InMemoryRevisionRepository,
    DatabaseRevisionRepository,
)
from persistence.base import Base


class TestDocumentService:
    """문서 서비스 테스트."""

    @pytest.mark.asyncio
    async def test_create_document_with_title(self):
        """서비스는 제목으로 문서를 생성할 수 있다."""
        repo = InMemoryDocumentRepository()
        service = DocumentService(repo)

        doc = await service.create("My Document")

        assert doc.id is not None
        assert doc.title == "My Document"
        assert doc.normalized_title == "My Document"
        assert doc.current_revision_id is None

    @pytest.mark.asyncio
    async def test_create_normalizes_title(self):
        """서비스는 제목을 정규화한다."""
        repo = InMemoryDocumentRepository()
        service = DocumentService(repo)

        doc = await service.create("  My   Document  ")

        assert doc.title == "  My   Document  "
        assert doc.normalized_title == "My Document"

    @pytest.mark.asyncio
    async def test_create_generates_unique_id(self):
        """서비스는 각 문서에 고유한 id를 생성한다."""
        repo = InMemoryDocumentRepository()
        service = DocumentService(repo)

        doc1 = await service.create("Document One")
        doc2 = await service.create("Document Two")

        assert doc1.id != doc2.id

    @pytest.mark.asyncio
    async def test_create_delegates_to_repository(self):
        """서비스는 저장소에 문서 생성을 위임한다."""
        repo = InMemoryDocumentRepository()
        service = DocumentService(repo)

        doc = await service.create("My Document")

        retrieved = await repo.get(doc.id)
        assert retrieved is not None
        assert retrieved.title == "My Document"

    @pytest.mark.asyncio
    async def test_create_raises_on_empty_title(self):
        """서비스는 빈 제목으로 생성하면 예외를 발생시킨다."""
        repo = InMemoryDocumentRepository()
        service = DocumentService(repo)

        with pytest.raises(EmptyTitleError):
            await service.create("")

    @pytest.mark.asyncio
    async def test_create_raises_on_whitespace_only_title(self):
        """서비스는 공백만 있는 제목으로 생성하면 예외를 발생시킨다."""
        repo = InMemoryDocumentRepository()
        service = DocumentService(repo)

        with pytest.raises(EmptyTitleError):
            await service.create("   ")

    @pytest.mark.asyncio
    async def test_create_raises_on_duplicate_normalized_title(self):
        """서비스는 정규화된 제목이 중복되면 예외를 발생시킨다."""
        repo = InMemoryDocumentRepository()
        service = DocumentService(repo)

        await service.create("My Document")

        with pytest.raises(DuplicateNormalizedTitleError):
            await service.create("My Document")

    @pytest.mark.asyncio
    async def test_create_raises_on_duplicate_normalized_title_with_spaces(self):
        """서비스는 공백이 다른 중복된 제목도 감지한다."""
        repo = InMemoryDocumentRepository()
        service = DocumentService(repo)

        await service.create("My Document")

        with pytest.raises(DuplicateNormalizedTitleError):
            await service.create("  My   Document  ")

    @pytest.mark.asyncio
    async def test_create_allows_different_normalized_titles(self):
        """서비스는 정규화된 제목이 다르면 같은 원본 제목도 허용한다."""
        repo = InMemoryDocumentRepository()
        service = DocumentService(repo)

        doc1 = await service.create("Document One")
        doc2 = await service.create("Document Two")

        assert doc1.normalized_title != doc2.normalized_title
        assert await repo.get(doc1.id) is not None
        assert await repo.get(doc2.id) is not None

    @pytest.mark.asyncio
    async def test_get_document_by_id(self):
        """서비스는 id로 문서를 조회할 수 있다."""
        repo = InMemoryDocumentRepository()
        service = DocumentService(repo)

        created = await service.create("My Document")
        retrieved = await service.get(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.title == "My Document"

    @pytest.mark.asyncio
    async def test_get_document_by_id_not_found(self):
        """서비스는 존재하지 않는 id를 조회하면 None을 반환한다."""
        repo = InMemoryDocumentRepository()
        service = DocumentService(repo)

        result = await service.get("nonexistent-id")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_document_by_title(self):
        """서비스는 제목으로 문서를 조회할 수 있다."""
        repo = InMemoryDocumentRepository()
        service = DocumentService(repo)

        created = await service.create("My Document")
        retrieved = await service.get_by_title("My Document")

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.title == "My Document"

    @pytest.mark.asyncio
    async def test_get_document_by_title_with_different_spacing(self):
        """서비스는 공백이 다른 제목도 정규화하여 조회할 수 있다."""
        repo = InMemoryDocumentRepository()
        service = DocumentService(repo)

        created = await service.create("My Document")
        retrieved = await service.get_by_title("  My   Document  ")

        assert retrieved is not None
        assert retrieved.id == created.id

    @pytest.mark.asyncio
    async def test_get_document_by_title_not_found(self):
        """서비스는 존재하지 않는 제목을 조회하면 None을 반환한다."""
        repo = InMemoryDocumentRepository()
        service = DocumentService(repo)

        result = await service.get_by_title("Nonexistent Document")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_title_raises_on_empty_title(self):
        """서비스는 빈 제목으로 조회하면 예외를 발생시킨다."""
        repo = InMemoryDocumentRepository()
        service = DocumentService(repo)

        with pytest.raises(EmptyTitleError):
            await service.get_by_title("")

    @pytest.mark.asyncio
    async def test_get_by_title_raises_on_whitespace_only_title(self):
        """서비스는 공백만 있는 제목으로 조회하면 예외를 발생시킨다."""
        repo = InMemoryDocumentRepository()
        service = DocumentService(repo)

        with pytest.raises(EmptyTitleError):
            await service.get_by_title("   ")

    @pytest.mark.asyncio
    async def test_create_document_with_source_creates_first_revision(self):
        """서비스는 소스를 제공하면 첫 리비전을 생성한다."""
        doc_repo = InMemoryDocumentRepository()
        rev_repo = InMemoryRevisionRepository()
        service = DocumentService(doc_repo, rev_repo)

        doc = await service.create("My Document", source="Initial content")

        assert doc.id is not None
        assert doc.title == "My Document"
        assert doc.current_revision_id is not None

        revision = await rev_repo.get(doc.current_revision_id)
        assert revision is not None
        assert revision.source == "Initial content"
        assert revision.document_id == doc.id
        assert revision.parent_revision_id is None

    @pytest.mark.asyncio
    async def test_create_document_without_source_no_revision(self):
        """서비스는 소스를 제공하지 않으면 리비전을 생성하지 않는다."""
        doc_repo = InMemoryDocumentRepository()
        rev_repo = InMemoryRevisionRepository()
        service = DocumentService(doc_repo, rev_repo)

        doc = await service.create("My Document")

        assert doc.current_revision_id is None
        revisions = await rev_repo.list_by_document_id(doc.id)
        assert len(revisions) == 0

    @pytest.mark.asyncio
    async def test_create_document_with_source_without_revision_repository(self):
        """서비스는 리비전 저장소가 없으면 소스를 무시한다."""
        doc_repo = InMemoryDocumentRepository()
        service = DocumentService(doc_repo)

        doc = await service.create("My Document", source="Initial content")

        assert doc.current_revision_id is None

    @pytest.mark.asyncio
    async def test_created_revision_linked_to_document(self):
        """서비스가 생성한 리비전은 문서와 올바르게 연결된다."""
        doc_repo = InMemoryDocumentRepository()
        rev_repo = InMemoryRevisionRepository()
        service = DocumentService(doc_repo, rev_repo)

        doc = await service.create("My Document", source="Content here")

        assert doc.current_revision_id is not None
        revision = await rev_repo.get(doc.current_revision_id)
        assert revision.document_id == doc.id
        assert revision.source == "Content here"

    @pytest.mark.asyncio
    async def test_multiple_documents_create_independent_revisions(self):
        """서비스는 여러 문서마다 독립적인 리비전을 생성한다."""
        doc_repo = InMemoryDocumentRepository()
        rev_repo = InMemoryRevisionRepository()
        service = DocumentService(doc_repo, rev_repo)

        doc1 = await service.create("Document One", source="Content One")
        doc2 = await service.create("Document Two", source="Content Two")

        assert doc1.id != doc2.id
        assert doc1.current_revision_id != doc2.current_revision_id

        rev1 = await rev_repo.get(doc1.current_revision_id)
        rev2 = await rev_repo.get(doc2.current_revision_id)

        assert rev1.document_id == doc1.id
        assert rev2.document_id == doc2.id
        assert rev1.source == "Content One"
        assert rev2.source == "Content Two"

    @pytest.mark.asyncio
    async def test_get_current_revision_read_model_with_source(self):
        """서비스는 소스를 포함한 현재 리비전 읽기 모델을 반환할 수 있다."""
        doc_repo = InMemoryDocumentRepository()
        rev_repo = InMemoryRevisionRepository()
        service = DocumentService(doc_repo, rev_repo)

        doc = await service.create("My Document", source="Current content")

        read_model = await service.get_current_revision_read_model(doc.id)

        assert read_model is not None
        assert isinstance(read_model, CurrentRevisionReadModel)
        assert read_model.title == "My Document"
        assert read_model.document_id == doc.id
        assert read_model.revision_id == doc.current_revision_id
        assert read_model.source == "Current content"

    @pytest.mark.asyncio
    async def test_get_current_revision_read_model_without_source(self):
        """서비스는 소스가 없는 경우 리비전 id와 소스를 None으로 반환한다."""
        doc_repo = InMemoryDocumentRepository()
        rev_repo = InMemoryRevisionRepository()
        service = DocumentService(doc_repo, rev_repo)

        doc = await service.create("My Document")

        read_model = await service.get_current_revision_read_model(doc.id)

        assert read_model is not None
        assert read_model.title == "My Document"
        assert read_model.document_id == doc.id
        assert read_model.revision_id is None
        assert read_model.source is None

    @pytest.mark.asyncio
    async def test_get_current_revision_read_model_without_revision_repository(self):
        """서비스는 리비전 저장소가 없는 경우 리비전 정보를 None으로 반환한다."""
        doc_repo = InMemoryDocumentRepository()
        service = DocumentService(doc_repo)

        doc = await service.create("My Document")

        read_model = await service.get_current_revision_read_model(doc.id)

        assert read_model is not None
        assert read_model.title == "My Document"
        assert read_model.document_id == doc.id
        assert read_model.revision_id is None
        assert read_model.source is None

    @pytest.mark.asyncio
    async def test_get_current_revision_read_model_nonexistent_document(self):
        """서비스는 존재하지 않는 문서를 조회하면 None을 반환한다."""
        doc_repo = InMemoryDocumentRepository()
        service = DocumentService(doc_repo)

        read_model = await service.get_current_revision_read_model("nonexistent-id")

        assert read_model is None


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


class TestDocumentServiceWithDatabase:
    """데이터베이스 저장소를 사용하는 서비스 테스트."""

    @pytest.mark.asyncio
    async def test_create_document_with_database_repository(self, async_db_session):
        """서비스는 데이터베이스 저장소에 문서를 생성할 수 있다."""
        repo = DatabaseDocumentRepository(async_db_session)
        service = DocumentService(repo)

        doc = await service.create("My Document")

        assert doc.id is not None
        assert doc.title == "My Document"
        assert doc.normalized_title == "My Document"
        assert doc.current_revision_id is None

    @pytest.mark.asyncio
    async def test_create_document_with_database_repository_persists(self, async_db_session):
        """서비스가 생성한 문서는 데이터베이스에 저장된다."""
        repo = DatabaseDocumentRepository(async_db_session)
        service = DocumentService(repo)

        created = await service.create("Test Document")
        retrieved = await service.get(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.title == "Test Document"

    @pytest.mark.asyncio
    async def test_create_document_with_database_repository_normalizes_title(
        self, async_db_session
    ):
        """서비스는 데이터베이스 저장소에서 제목을 정규화한다."""
        repo = DatabaseDocumentRepository(async_db_session)
        service = DocumentService(repo)

        doc = await service.create("  My   Document  ")

        assert doc.title == "  My   Document  "
        assert doc.normalized_title == "My Document"
        retrieved = await service.get_by_title("My Document")
        assert retrieved is not None
        assert retrieved.id == doc.id

    @pytest.mark.asyncio
    async def test_create_document_with_database_repository_generates_unique_ids(
        self, async_db_session
    ):
        """서비스는 데이터베이스 저장소에서 각 문서에 고유한 id를 생성한다."""
        repo = DatabaseDocumentRepository(async_db_session)
        service = DocumentService(repo)

        doc1 = await service.create("Document One")
        doc2 = await service.create("Document Two")

        assert doc1.id != doc2.id

    @pytest.mark.asyncio
    async def test_create_document_with_database_repository_duplicate_title_fails(
        self, async_db_session
    ):
        """서비스는 데이터베이스 저장소에서 중복된 정규화된 제목을 거부한다."""
        repo = DatabaseDocumentRepository(async_db_session)
        service = DocumentService(repo)

        await service.create("My Document")

        with pytest.raises(DuplicateNormalizedTitleError):
            await service.create("My Document")

    @pytest.mark.asyncio
    async def test_get_document_by_title_with_database_repository(self, async_db_session):
        """서비스는 데이터베이스 저장소에서 제목으로 문서를 조회할 수 있다."""
        repo = DatabaseDocumentRepository(async_db_session)
        service = DocumentService(repo)

        created = await service.create("My Document")
        retrieved = await service.get_by_title("My Document")

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.title == "My Document"

    @pytest.mark.asyncio
    async def test_get_document_by_id_with_database_repository(self, async_db_session):
        """서비스는 데이터베이스 저장소에서 id로 문서를 조회할 수 있다."""
        repo = DatabaseDocumentRepository(async_db_session)
        service = DocumentService(repo)

        created = await service.create("My Document")
        retrieved = await service.get(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.title == "My Document"

    @pytest.mark.asyncio
    async def test_get_nonexistent_document_returns_none_with_database_repository(
        self, async_db_session
    ):
        """서비스는 데이터베이스 저장소에서 없는 id를 조회하면 None을 반환한다."""
        repo = DatabaseDocumentRepository(async_db_session)
        service = DocumentService(repo)

        result = await service.get("nonexistent-id")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_current_revision_read_model_with_database_repository(
        self, async_db_session
    ):
        """서비스는 데이터베이스 저장소에서 현재 리비전 읽기 모델을 반환할 수 있다."""
        repo = DatabaseDocumentRepository(async_db_session)
        service = DocumentService(repo)

        doc = await service.create("My Document")
        read_model = await service.get_current_revision_read_model(doc.id)

        assert read_model is not None
        assert isinstance(read_model, CurrentRevisionReadModel)
        assert read_model.title == "My Document"
        assert read_model.document_id == doc.id
        assert read_model.revision_id is None
        assert read_model.source is None

    @pytest.mark.asyncio
    async def test_multiple_documents_with_database_repository(self, async_db_session):
        """서비스는 데이터베이스 저장소에 여러 문서를 생성할 수 있다."""
        repo = DatabaseDocumentRepository(async_db_session)
        service = DocumentService(repo)

        doc1 = await service.create("Document One")
        doc2 = await service.create("Document Two")
        doc3 = await service.create("Document Three")

        assert await service.get(doc1.id) is not None
        assert await service.get(doc2.id) is not None
        assert await service.get(doc3.id) is not None
        assert await service.get_by_title("Document One") is not None
        assert await service.get_by_title("Document Two") is not None
        assert await service.get_by_title("Document Three") is not None

    @pytest.mark.asyncio
    async def test_create_document_with_source_and_database_repository(
        self, async_db_session
    ):
        """서비스는 데이터베이스 저장소에 소스를 포함하여 문서를 생성할 수 있다."""
        doc_repo = DatabaseDocumentRepository(async_db_session)
        rev_repo = DatabaseRevisionRepository(async_db_session)
        service = DocumentService(doc_repo, rev_repo)

        doc = await service.create("My Document", source="Initial content")

        assert doc.id is not None
        assert doc.title == "My Document"
        assert doc.current_revision_id is not None

        revision = await rev_repo.get(doc.current_revision_id)
        assert revision is not None
        assert revision.source == "Initial content"
        assert revision.document_id == doc.id

    @pytest.mark.asyncio
    async def test_current_revision_id_persisted_to_database(self, async_db_session):
        """현재 리비전 id가 데이터베이스에 저장된다."""
        doc_repo = DatabaseDocumentRepository(async_db_session)
        rev_repo = DatabaseRevisionRepository(async_db_session)
        service = DocumentService(doc_repo, rev_repo)

        doc = await service.create("My Document", source="Initial content")

        retrieved = await service.get(doc.id)

        assert retrieved is not None
        assert retrieved.current_revision_id == doc.current_revision_id
        assert retrieved.current_revision_id is not None
