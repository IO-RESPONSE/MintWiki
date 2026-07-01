"""리비전 저장소 인터페이스 테스트."""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from modules.revision.model import Revision
from modules.revision.repository import (
    RevisionRepository,
    InMemoryRevisionRepository,
    DatabaseRevisionRepository,
)
from persistence.base import Base
from persistence.models import RevisionORM


class ConcreteRepository(RevisionRepository):
    """테스트용 구체적인 저장소 구현."""

    def __init__(self):
        """저장소를 초기화한다."""
        self.revisions = {}
        self.document_revisions = {}

    async def create(self, revision: Revision) -> Revision:
        """리비전을 저장소에 저장한다."""
        self.revisions[revision.id] = revision
        if revision.document_id not in self.document_revisions:
            self.document_revisions[revision.document_id] = []
        self.document_revisions[revision.document_id].append(revision.id)
        return revision

    async def get(self, id: str) -> Revision | None:
        """id로 리비전을 조회한다."""
        return self.revisions.get(id)

    async def list_by_document_id(self, document_id: str) -> list[Revision]:
        """문서의 리비전을 생성 순서대로 나열한다."""
        revision_ids = self.document_revisions.get(document_id, [])
        return [self.revisions[rid] for rid in revision_ids]


class TestRevisionRepositoryInterface:
    """저장소 인터페이스 테스트."""

    def test_repository_is_abstract(self):
        """저장소는 추상 클래스이다."""
        with pytest.raises(TypeError):
            RevisionRepository()

    def test_create_method_exists(self):
        """저장소는 create 메서드를 정의한다."""
        assert hasattr(RevisionRepository, "create")

    def test_get_method_exists(self):
        """저장소는 get 메서드를 정의한다."""
        assert hasattr(RevisionRepository, "get")

    def test_list_by_document_id_method_exists(self):
        """저장소는 list_by_document_id 메서드를 정의한다."""
        assert hasattr(RevisionRepository, "list_by_document_id")

    @pytest.mark.asyncio
    async def test_concrete_implementation_can_create_revision(self):
        """구체적인 구현은 리비전을 생성할 수 있다."""
        repo = ConcreteRepository()
        rev = Revision(
            id="rev1",
            document_id="doc1",
            source="content",
            author_id="user1",
            summary="Initial",
        )
        result = await repo.create(rev)
        assert result.id == "rev1"
        assert result.document_id == "doc1"

    @pytest.mark.asyncio
    async def test_concrete_implementation_can_get_revision_by_id(self):
        """구체적인 구현은 id로 리비전을 조회할 수 있다."""
        repo = ConcreteRepository()
        rev = Revision(
            id="rev1",
            document_id="doc1",
            source="content",
            author_id="user1",
            summary="Initial",
        )
        await repo.create(rev)
        result = await repo.get("rev1")
        assert result is not None
        assert result.id == "rev1"

    @pytest.mark.asyncio
    async def test_concrete_implementation_returns_none_for_missing_id(self):
        """구체적인 구현은 없는 리비전을 조회하면 None을 반환한다."""
        repo = ConcreteRepository()
        result = await repo.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_concrete_implementation_can_list_revisions_by_document_id(self):
        """구체적인 구현은 문서의 리비전을 나열할 수 있다."""
        repo = ConcreteRepository()
        rev1 = Revision(
            id="rev1",
            document_id="doc1",
            source="v1",
            author_id="user1",
            summary="v1",
        )
        rev2 = Revision(
            id="rev2",
            document_id="doc1",
            source="v2",
            author_id="user1",
            summary="v2",
            parent_revision_id="rev1",
        )
        await repo.create(rev1)
        await repo.create(rev2)
        result = await repo.list_by_document_id("doc1")
        assert len(result) == 2
        assert result[0].id == "rev1"
        assert result[1].id == "rev2"

    @pytest.mark.asyncio
    async def test_concrete_implementation_returns_empty_list_for_missing_document(self):
        """구체적인 구현은 없는 문서의 리비전을 조회하면 빈 목록을 반환한다."""
        repo = ConcreteRepository()
        result = await repo.list_by_document_id("nonexistent")
        assert result == []


class TestInMemoryRevisionRepository:
    """인메모리 저장소 구현 테스트."""

    @pytest.mark.asyncio
    async def test_can_create_revision(self):
        """인메모리 저장소는 리비전을 생성할 수 있다."""
        repo = InMemoryRevisionRepository()
        rev = Revision(
            id="rev1",
            document_id="doc1",
            source="Hello, World!",
            author_id="user1",
            summary="Initial content",
        )
        result = await repo.create(rev)
        assert result.id == "rev1"
        assert result.document_id == "doc1"
        assert result.source == "Hello, World!"
        assert result.author_id == "user1"
        assert result.summary == "Initial content"

    @pytest.mark.asyncio
    async def test_can_fetch_revision_by_id(self):
        """인메모리 저장소는 id로 리비전을 조회할 수 있다."""
        repo = InMemoryRevisionRepository()
        rev = Revision(
            id="rev1",
            document_id="doc1",
            source="content",
            author_id="user1",
            summary="Initial",
        )
        await repo.create(rev)
        result = await repo.get("rev1")
        assert result is not None
        assert result.id == "rev1"
        assert result.document_id == "doc1"

    @pytest.mark.asyncio
    async def test_returns_none_for_missing_id(self):
        """인메모리 저장소는 없는 id를 조회하면 None을 반환한다."""
        repo = InMemoryRevisionRepository()
        result = await repo.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_can_list_revisions_for_document_in_creation_order(self):
        """인메모리 저장소는 문서의 리비전을 생성 순서대로 나열할 수 있다."""
        repo = InMemoryRevisionRepository()
        rev1 = Revision(
            id="rev1",
            document_id="doc1",
            source="v1",
            author_id="user1",
            summary="First revision",
        )
        rev2 = Revision(
            id="rev2",
            document_id="doc1",
            source="v2",
            author_id="user2",
            summary="Second revision",
            parent_revision_id="rev1",
        )
        rev3 = Revision(
            id="rev3",
            document_id="doc1",
            source="v3",
            author_id="user1",
            summary="Third revision",
            parent_revision_id="rev2",
        )
        await repo.create(rev1)
        await repo.create(rev2)
        await repo.create(rev3)
        result = await repo.list_by_document_id("doc1")
        assert len(result) == 3
        assert result[0].id == "rev1"
        assert result[1].id == "rev2"
        assert result[2].id == "rev3"

    @pytest.mark.asyncio
    async def test_returns_empty_list_for_nonexistent_document(self):
        """인메모리 저장소는 없는 문서의 리비전을 조회하면 빈 목록을 반환한다."""
        repo = InMemoryRevisionRepository()
        result = await repo.list_by_document_id("nonexistent")
        assert result == []

    @pytest.mark.asyncio
    async def test_can_store_multiple_revisions_for_different_documents(self):
        """인메모리 저장소는 여러 문서의 리비전을 저장할 수 있다."""
        repo = InMemoryRevisionRepository()
        rev1_doc1 = Revision(
            id="rev1_1",
            document_id="doc1",
            source="doc1_v1",
            author_id="user1",
            summary="doc1 rev1",
        )
        rev1_doc2 = Revision(
            id="rev1_2",
            document_id="doc2",
            source="doc2_v1",
            author_id="user1",
            summary="doc2 rev1",
        )
        rev2_doc1 = Revision(
            id="rev2_1",
            document_id="doc1",
            source="doc1_v2",
            author_id="user2",
            summary="doc1 rev2",
            parent_revision_id="rev1_1",
        )
        await repo.create(rev1_doc1)
        await repo.create(rev1_doc2)
        await repo.create(rev2_doc1)

        doc1_revs = await repo.list_by_document_id("doc1")
        doc2_revs = await repo.list_by_document_id("doc2")

        assert len(doc1_revs) == 2
        assert len(doc2_revs) == 1
        assert doc1_revs[0].id == "rev1_1"
        assert doc1_revs[1].id == "rev2_1"
        assert doc2_revs[0].id == "rev1_2"

    @pytest.mark.asyncio
    async def test_preserves_revision_attributes(self):
        """인메모리 저장소는 리비전의 모든 속성을 보존한다."""
        repo = InMemoryRevisionRepository()
        rev = Revision(
            id="rev1",
            document_id="doc1",
            source="Multi-line\ncontent\nhere",
            author_id="user1",
            summary="Complex edit",
            parent_revision_id="rev0",
        )
        await repo.create(rev)
        result = await repo.get("rev1")
        assert result.id == "rev1"
        assert result.document_id == "doc1"
        assert result.source == "Multi-line\ncontent\nhere"
        assert result.author_id == "user1"
        assert result.summary == "Complex edit"
        assert result.parent_revision_id == "rev0"


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


class TestDatabaseRevisionRepository:
    """데이터베이스 저장소 구현 테스트."""

    @pytest.mark.asyncio
    async def test_can_create_revision(self, async_db_session):
        """데이터베이스 저장소는 리비전을 생성할 수 있다."""
        repo = DatabaseRevisionRepository(async_db_session)
        rev = Revision(
            id="rev1",
            document_id="doc1",
            source="Hello, World!",
            author_id="user1",
            summary="Initial content",
        )
        result = await repo.create(rev)
        assert result.id == "rev1"
        assert result.document_id == "doc1"
        assert result.source == "Hello, World!"
        assert result.author_id == "user1"
        assert result.summary == "Initial content"

    @pytest.mark.asyncio
    async def test_can_fetch_revision_by_id(self, async_db_session):
        """데이터베이스 저장소는 id로 리비전을 조회할 수 있다."""
        repo = DatabaseRevisionRepository(async_db_session)
        rev = Revision(
            id="rev1",
            document_id="doc1",
            source="content",
            author_id="user1",
            summary="Initial",
        )
        await repo.create(rev)
        result = await repo.get("rev1")
        assert result is not None
        assert result.id == "rev1"
        assert result.document_id == "doc1"
        assert result.source == "content"

    @pytest.mark.asyncio
    async def test_returns_none_for_missing_id(self, async_db_session):
        """데이터베이스 저장소는 없는 id를 조회하면 None을 반환한다."""
        repo = DatabaseRevisionRepository(async_db_session)
        result = await repo.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_can_list_revisions_for_document_in_creation_order(
        self, async_db_session
    ):
        """데이터베이스 저장소는 문서의 리비전을 생성 순서대로 나열할 수 있다."""
        repo = DatabaseRevisionRepository(async_db_session)
        rev1 = Revision(
            id="rev1",
            document_id="doc1",
            source="v1",
            author_id="user1",
            summary="First revision",
        )
        rev2 = Revision(
            id="rev2",
            document_id="doc1",
            source="v2",
            author_id="user2",
            summary="Second revision",
            parent_revision_id="rev1",
        )
        rev3 = Revision(
            id="rev3",
            document_id="doc1",
            source="v3",
            author_id="user1",
            summary="Third revision",
            parent_revision_id="rev2",
        )
        await repo.create(rev1)
        await repo.create(rev2)
        await repo.create(rev3)
        result = await repo.list_by_document_id("doc1")
        assert len(result) == 3
        assert result[0].id == "rev1"
        assert result[1].id == "rev2"
        assert result[2].id == "rev3"

    @pytest.mark.asyncio
    async def test_returns_empty_list_for_nonexistent_document(
        self, async_db_session
    ):
        """데이터베이스 저장소는 없는 문서의 리비전을 조회하면 빈 목록을 반환한다."""
        repo = DatabaseRevisionRepository(async_db_session)
        result = await repo.list_by_document_id("nonexistent")
        assert result == []

    @pytest.mark.asyncio
    async def test_can_store_multiple_revisions_for_different_documents(
        self, async_db_session
    ):
        """데이터베이스 저장소는 여러 문서의 리비전을 저장할 수 있다."""
        repo = DatabaseRevisionRepository(async_db_session)
        rev1_doc1 = Revision(
            id="rev1_1",
            document_id="doc1",
            source="doc1_v1",
            author_id="user1",
            summary="doc1 rev1",
        )
        rev1_doc2 = Revision(
            id="rev1_2",
            document_id="doc2",
            source="doc2_v1",
            author_id="user1",
            summary="doc2 rev1",
        )
        rev2_doc1 = Revision(
            id="rev2_1",
            document_id="doc1",
            source="doc1_v2",
            author_id="user2",
            summary="doc1 rev2",
            parent_revision_id="rev1_1",
        )
        await repo.create(rev1_doc1)
        await repo.create(rev1_doc2)
        await repo.create(rev2_doc1)

        doc1_revs = await repo.list_by_document_id("doc1")
        doc2_revs = await repo.list_by_document_id("doc2")

        assert len(doc1_revs) == 2
        assert len(doc2_revs) == 1
        assert doc1_revs[0].id == "rev1_1"
        assert doc1_revs[1].id == "rev2_1"
        assert doc2_revs[0].id == "rev1_2"

    @pytest.mark.asyncio
    async def test_preserves_revision_attributes(self, async_db_session):
        """데이터베이스 저장소는 리비전의 모든 속성을 보존한다."""
        repo = DatabaseRevisionRepository(async_db_session)
        rev = Revision(
            id="rev1",
            document_id="doc1",
            source="Multi-line\ncontent\nhere",
            author_id="user1",
            summary="Complex edit",
            parent_revision_id="rev0",
        )
        await repo.create(rev)
        result = await repo.get("rev1")
        assert result.id == "rev1"
        assert result.document_id == "doc1"
        assert result.source == "Multi-line\ncontent\nhere"
        assert result.author_id == "user1"
        assert result.summary == "Complex edit"
        assert result.parent_revision_id == "rev0"
