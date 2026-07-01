"""리비전 서비스 테스트."""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from modules.revision.repository import (
    InMemoryRevisionRepository,
    DatabaseRevisionRepository,
)
from modules.revision.service import RevisionService
from persistence.base import Base


class TestRevisionService:
    """리비전 서비스 테스트."""

    @pytest.mark.asyncio
    async def test_create_revision(self):
        """서비스는 리비전을 생성할 수 있다."""
        repo = InMemoryRevisionRepository()
        service = RevisionService(repo)

        rev = await service.create(
            document_id="doc1",
            source="Initial content",
            author_id="user1",
            summary="First revision",
        )

        assert rev.id is not None
        assert rev.document_id == "doc1"
        assert rev.source == "Initial content"
        assert rev.author_id == "user1"
        assert rev.summary == "First revision"
        assert rev.parent_revision_id is None

    @pytest.mark.asyncio
    async def test_create_revision_with_parent(self):
        """서비스는 부모 리비전을 지정하여 리비전을 생성할 수 있다."""
        repo = InMemoryRevisionRepository()
        service = RevisionService(repo)

        parent = await service.create(
            document_id="doc1",
            source="v1",
            author_id="user1",
            summary="First revision",
        )

        child = await service.create(
            document_id="doc1",
            source="v2",
            author_id="user2",
            summary="Second revision",
            parent_revision_id=parent.id,
        )

        assert child.parent_revision_id == parent.id
        assert child.document_id == "doc1"

    @pytest.mark.asyncio
    async def test_create_generates_unique_ids(self):
        """서비스는 각 리비전에 고유한 id를 생성한다."""
        repo = InMemoryRevisionRepository()
        service = RevisionService(repo)

        rev1 = await service.create(
            document_id="doc1",
            source="v1",
            author_id="user1",
            summary="First",
        )
        rev2 = await service.create(
            document_id="doc1",
            source="v2",
            author_id="user1",
            summary="Second",
        )

        assert rev1.id != rev2.id

    @pytest.mark.asyncio
    async def test_create_delegates_to_repository(self):
        """서비스는 저장소에 리비전 생성을 위임한다."""
        repo = InMemoryRevisionRepository()
        service = RevisionService(repo)

        rev = await service.create(
            document_id="doc1",
            source="content",
            author_id="user1",
            summary="Initial",
        )

        retrieved = await repo.get(rev.id)
        assert retrieved is not None
        assert retrieved.document_id == "doc1"
        assert retrieved.source == "content"

    @pytest.mark.asyncio
    async def test_get_revision_by_id(self):
        """서비스는 id로 리비전을 조회할 수 있다."""
        repo = InMemoryRevisionRepository()
        service = RevisionService(repo)

        created = await service.create(
            document_id="doc1",
            source="content",
            author_id="user1",
            summary="Initial",
        )

        retrieved = await service.get(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.document_id == "doc1"

    @pytest.mark.asyncio
    async def test_get_nonexistent_revision_returns_none(self):
        """서비스는 존재하지 않는 id를 조회하면 None을 반환한다."""
        repo = InMemoryRevisionRepository()
        service = RevisionService(repo)

        result = await service.get("nonexistent-id")

        assert result is None

    @pytest.mark.asyncio
    async def test_list_revisions_by_document_id(self):
        """서비스는 문서의 리비전을 생성 순서대로 나열할 수 있다."""
        repo = InMemoryRevisionRepository()
        service = RevisionService(repo)

        rev1 = await service.create(
            document_id="doc1",
            source="v1",
            author_id="user1",
            summary="First",
        )
        rev2 = await service.create(
            document_id="doc1",
            source="v2",
            author_id="user2",
            summary="Second",
            parent_revision_id=rev1.id,
        )
        rev3 = await service.create(
            document_id="doc1",
            source="v3",
            author_id="user1",
            summary="Third",
            parent_revision_id=rev2.id,
        )

        result = await service.list_by_document_id("doc1")

        assert len(result) == 3
        assert result[0].id == rev1.id
        assert result[1].id == rev2.id
        assert result[2].id == rev3.id

    @pytest.mark.asyncio
    async def test_list_revisions_for_nonexistent_document(self):
        """서비스는 없는 문서의 리비전을 조회하면 빈 목록을 반환한다."""
        repo = InMemoryRevisionRepository()
        service = RevisionService(repo)

        result = await service.list_by_document_id("nonexistent")

        assert result == []

    @pytest.mark.asyncio
    async def test_list_revisions_for_different_documents(self):
        """서비스는 여러 문서의 리비전을 독립적으로 나열할 수 있다."""
        repo = InMemoryRevisionRepository()
        service = RevisionService(repo)

        rev1_doc1 = await service.create(
            document_id="doc1",
            source="doc1_v1",
            author_id="user1",
            summary="doc1 rev1",
        )
        rev1_doc2 = await service.create(
            document_id="doc2",
            source="doc2_v1",
            author_id="user1",
            summary="doc2 rev1",
        )
        rev2_doc1 = await service.create(
            document_id="doc1",
            source="doc1_v2",
            author_id="user2",
            summary="doc1 rev2",
            parent_revision_id=rev1_doc1.id,
        )

        doc1_revs = await service.list_by_document_id("doc1")
        doc2_revs = await service.list_by_document_id("doc2")

        assert len(doc1_revs) == 2
        assert len(doc2_revs) == 1
        assert doc1_revs[0].id == rev1_doc1.id
        assert doc1_revs[1].id == rev2_doc1.id
        assert doc2_revs[0].id == rev1_doc2.id


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


class TestRevisionServiceWithDatabase:
    """데이터베이스 저장소를 사용하는 서비스 테스트."""

    @pytest.mark.asyncio
    async def test_create_revision_with_database_repository(self, async_db_session):
        """서비스는 데이터베이스 저장소에 리비전을 생성할 수 있다."""
        repo = DatabaseRevisionRepository(async_db_session)
        service = RevisionService(repo)

        rev = await service.create(
            document_id="doc1",
            source="Initial content",
            author_id="user1",
            summary="First revision",
        )

        assert rev.id is not None
        assert rev.document_id == "doc1"
        assert rev.source == "Initial content"
        assert rev.author_id == "user1"
        assert rev.summary == "First revision"

    @pytest.mark.asyncio
    async def test_create_revision_with_database_repository_persists(
        self, async_db_session
    ):
        """서비스가 생성한 리비전은 데이터베이스에 저장된다."""
        repo = DatabaseRevisionRepository(async_db_session)
        service = RevisionService(repo)

        created = await service.create(
            document_id="doc1",
            source="Test content",
            author_id="user1",
            summary="Test revision",
        )

        retrieved = await service.get(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.source == "Test content"

    @pytest.mark.asyncio
    async def test_create_revision_with_parent_with_database_repository(
        self, async_db_session
    ):
        """서비스는 데이터베이스 저장소에서 부모 리비전을 지정하여 생성할 수 있다."""
        repo = DatabaseRevisionRepository(async_db_session)
        service = RevisionService(repo)

        parent = await service.create(
            document_id="doc1",
            source="v1",
            author_id="user1",
            summary="First",
        )

        child = await service.create(
            document_id="doc1",
            source="v2",
            author_id="user2",
            summary="Second",
            parent_revision_id=parent.id,
        )

        retrieved = await service.get(child.id)

        assert retrieved is not None
        assert retrieved.parent_revision_id == parent.id

    @pytest.mark.asyncio
    async def test_list_revisions_with_database_repository(self, async_db_session):
        """서비스는 데이터베이스 저장소에서 문서의 리비전을 나열할 수 있다."""
        repo = DatabaseRevisionRepository(async_db_session)
        service = RevisionService(repo)

        rev1 = await service.create(
            document_id="doc1",
            source="v1",
            author_id="user1",
            summary="First",
        )
        rev2 = await service.create(
            document_id="doc1",
            source="v2",
            author_id="user2",
            summary="Second",
            parent_revision_id=rev1.id,
        )

        result = await service.list_by_document_id("doc1")

        assert len(result) == 2
        assert result[0].id == rev1.id
        assert result[1].id == rev2.id

    @pytest.mark.asyncio
    async def test_multiple_revisions_with_database_repository(self, async_db_session):
        """서비스는 데이터베이스 저장소에 여러 리비전을 생성할 수 있다."""
        repo = DatabaseRevisionRepository(async_db_session)
        service = RevisionService(repo)

        rev1 = await service.create(
            document_id="doc1",
            source="v1",
            author_id="user1",
            summary="First",
        )
        rev2 = await service.create(
            document_id="doc2",
            source="v1",
            author_id="user1",
            summary="First",
        )

        assert await service.get(rev1.id) is not None
        assert await service.get(rev2.id) is not None
