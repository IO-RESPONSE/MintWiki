"""리비전 영속성 테스트."""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from modules.revision.repository import DatabaseRevisionRepository
from modules.revision.service import RevisionService
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


class TestRevisionPersistenceBasics:
    """리비전 영속성 기본 테스트."""

    @pytest.mark.asyncio
    async def test_persisted_revision_can_be_retrieved_in_new_session(
        self, async_db_session
    ):
        """저장된 리비전을 새 세션에서 검색할 수 있다."""
        repo = DatabaseRevisionRepository(async_db_session)
        service = RevisionService(repo)

        created = await service.create(
            document_id="doc1",
            source="Persisted content",
            author_id="user1",
            summary="Test persistence",
        )
        revision_id = created.id

        retrieved = await service.get(revision_id)

        assert retrieved is not None
        assert retrieved.id == revision_id
        assert retrieved.source == "Persisted content"
        assert retrieved.author_id == "user1"
        assert retrieved.summary == "Test persistence"

    @pytest.mark.asyncio
    async def test_persisted_revision_with_unicode_content(self, async_db_session):
        """유니코드 콘텐츠를 가진 리비전을 저장하고 검색할 수 있다."""
        repo = DatabaseRevisionRepository(async_db_session)
        service = RevisionService(repo)

        created = await service.create(
            document_id="doc1",
            source="한글 콘텐츠\n日本語\n中文\nemoji: 🎉🚀",
            author_id="user1",
            summary="유니코드 테스트",
        )

        retrieved = await service.get(created.id)

        assert retrieved is not None
        assert retrieved.source == "한글 콘텐츠\n日本語\n中文\nemoji: 🎉🚀"
        assert retrieved.summary == "유니코드 테스트"

    @pytest.mark.asyncio
    async def test_persisted_revision_with_multiline_content(
        self, async_db_session
    ):
        """여러 줄의 콘텐츠를 가진 리비전을 저장하고 검색할 수 있다."""
        repo = DatabaseRevisionRepository(async_db_session)
        service = RevisionService(repo)

        multiline_content = """Line 1
Line 2
Line 3

Line 5 with extra space


Line 8"""

        created = await service.create(
            document_id="doc1",
            source=multiline_content,
            author_id="user1",
            summary="Multiline content",
        )

        retrieved = await service.get(created.id)

        assert retrieved is not None
        assert retrieved.source == multiline_content

    @pytest.mark.asyncio
    async def test_persisted_revision_with_special_characters(
        self, async_db_session
    ):
        """특수 문자를 포함한 리비전을 저장하고 검색할 수 있다."""
        repo = DatabaseRevisionRepository(async_db_session)
        service = RevisionService(repo)

        special_content = "Special chars: !@#$%^&*()_+-=[]{}|;':\",./<>?"

        created = await service.create(
            document_id="doc1",
            source=special_content,
            author_id="user1",
            summary="Special chars test",
        )

        retrieved = await service.get(created.id)

        assert retrieved is not None
        assert retrieved.source == special_content

    @pytest.mark.asyncio
    async def test_persisted_revision_with_long_content(self, async_db_session):
        """긴 콘텐츠를 가진 리비전을 저장하고 검색할 수 있다."""
        repo = DatabaseRevisionRepository(async_db_session)
        service = RevisionService(repo)

        long_content = "x" * 10000

        created = await service.create(
            document_id="doc1",
            source=long_content,
            author_id="user1",
            summary="Long content test",
        )

        retrieved = await service.get(created.id)

        assert retrieved is not None
        assert retrieved.source == long_content
        assert len(retrieved.source) == 10000


class TestRevisionPersistenceOrdering:
    """리비전 영속성 순서 테스트."""

    @pytest.mark.asyncio
    async def test_persisted_revisions_are_retrieved_in_creation_order(
        self, async_db_session
    ):
        """저장된 리비전은 생성 순서대로 검색된다."""
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
            author_id="user1",
            summary="Second",
        )
        rev3 = await service.create(
            document_id="doc1",
            source="v3",
            author_id="user1",
            summary="Third",
        )

        revisions = await service.list_by_document_id("doc1")

        assert len(revisions) == 3
        assert revisions[0].id == rev1.id
        assert revisions[1].id == rev2.id
        assert revisions[2].id == rev3.id
        assert revisions[0].source == "v1"
        assert revisions[1].source == "v2"
        assert revisions[2].source == "v3"

    @pytest.mark.asyncio
    async def test_persisted_revisions_maintain_parent_relationships(
        self, async_db_session
    ):
        """저장된 리비전의 부모 관계가 유지된다."""
        repo = DatabaseRevisionRepository(async_db_session)
        service = RevisionService(repo)

        parent = await service.create(
            document_id="doc1",
            source="v1",
            author_id="user1",
            summary="Parent",
        )
        child = await service.create(
            document_id="doc1",
            source="v2",
            author_id="user1",
            summary="Child",
            parent_revision_id=parent.id,
        )

        retrieved_child = await service.get(child.id)

        assert retrieved_child is not None
        assert retrieved_child.parent_revision_id == parent.id


class TestRevisionPersistenceIsolation:
    """리비전 영속성 격리 테스트."""

    @pytest.mark.asyncio
    async def test_persisted_revisions_are_isolated_by_document(
        self, async_db_session
    ):
        """서로 다른 문서의 리비전은 독립적으로 저장된다."""
        repo = DatabaseRevisionRepository(async_db_session)
        service = RevisionService(repo)

        rev_doc1_v1 = await service.create(
            document_id="doc1",
            source="doc1 v1",
            author_id="user1",
            summary="doc1 rev1",
        )
        rev_doc2_v1 = await service.create(
            document_id="doc2",
            source="doc2 v1",
            author_id="user1",
            summary="doc2 rev1",
        )
        rev_doc1_v2 = await service.create(
            document_id="doc1",
            source="doc1 v2",
            author_id="user1",
            summary="doc1 rev2",
        )

        doc1_revs = await service.list_by_document_id("doc1")
        doc2_revs = await service.list_by_document_id("doc2")

        assert len(doc1_revs) == 2
        assert len(doc2_revs) == 1
        assert doc1_revs[0].id == rev_doc1_v1.id
        assert doc1_revs[1].id == rev_doc1_v2.id
        assert doc2_revs[0].id == rev_doc2_v1.id


class TestRevisionPersistenceDataIntegrity:
    """리비전 영속성 데이터 무결성 테스트."""

    @pytest.mark.asyncio
    async def test_persisted_revision_preserves_all_attributes(
        self, async_db_session
    ):
        """저장된 리비전이 모든 속성을 보존한다."""
        repo = DatabaseRevisionRepository(async_db_session)
        service = RevisionService(repo)

        created = await service.create(
            document_id="test_doc",
            source="Complete content",
            author_id="test_author",
            summary="Complete summary",
            parent_revision_id="parent_id",
        )

        retrieved = await service.get(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.document_id == "test_doc"
        assert retrieved.source == "Complete content"
        assert retrieved.author_id == "test_author"
        assert retrieved.summary == "Complete summary"
        assert retrieved.parent_revision_id == "parent_id"

    @pytest.mark.asyncio
    async def test_persisted_revision_retrieval_returns_exact_copy(
        self, async_db_session
    ):
        """저장된 리비전 검색이 정확한 복사본을 반환한다."""
        repo = DatabaseRevisionRepository(async_db_session)
        service = RevisionService(repo)

        created = await service.create(
            document_id="doc1",
            source="Test source content",
            author_id="author1",
            summary="Test summary",
        )

        retrieved1 = await service.get(created.id)
        retrieved2 = await service.get(created.id)

        assert retrieved1.id == retrieved2.id
        assert retrieved1.document_id == retrieved2.document_id
        assert retrieved1.source == retrieved2.source
        assert retrieved1.author_id == retrieved2.author_id
        assert retrieved1.summary == retrieved2.summary
        assert retrieved1.parent_revision_id == retrieved2.parent_revision_id


class TestRevisionPersistenceEdgeCases:
    """리비전 영속성 엣지 케이스 테스트."""

    @pytest.mark.asyncio
    async def test_persisted_revision_without_parent_id(self, async_db_session):
        """부모 id가 없는 리비전을 저장하고 검색할 수 있다."""
        repo = DatabaseRevisionRepository(async_db_session)
        service = RevisionService(repo)

        created = await service.create(
            document_id="doc1",
            source="Initial content",
            author_id="user1",
            summary="First revision",
            parent_revision_id=None,
        )

        retrieved = await service.get(created.id)

        assert retrieved is not None
        assert retrieved.parent_revision_id is None

    @pytest.mark.asyncio
    async def test_persisted_revision_empty_string_content(self, async_db_session):
        """빈 문자열 콘텐츠를 가진 리비전을 저장하고 검색할 수 있다."""
        repo = DatabaseRevisionRepository(async_db_session)
        service = RevisionService(repo)

        created = await service.create(
            document_id="doc1",
            source="",
            author_id="user1",
            summary="Empty content",
        )

        retrieved = await service.get(created.id)

        assert retrieved is not None
        assert retrieved.source == ""

    @pytest.mark.asyncio
    async def test_persisted_revision_with_whitespace_only_content(
        self, async_db_session
    ):
        """공백만 있는 콘텐츠를 가진 리비전을 저장하고 검색할 수 있다."""
        repo = DatabaseRevisionRepository(async_db_session)
        service = RevisionService(repo)

        whitespace_content = "   \n\t\n  "

        created = await service.create(
            document_id="doc1",
            source=whitespace_content,
            author_id="user1",
            summary="Whitespace content",
        )

        retrieved = await service.get(created.id)

        assert retrieved is not None
        assert retrieved.source == whitespace_content

    @pytest.mark.asyncio
    async def test_list_persisted_revisions_for_nonexistent_document_returns_empty(
        self, async_db_session
    ):
        """존재하지 않는 문서의 리비전 목록은 빈 목록이다."""
        repo = DatabaseRevisionRepository(async_db_session)
        service = RevisionService(repo)

        result = await service.list_by_document_id("nonexistent_doc")

        assert result == []

    @pytest.mark.asyncio
    async def test_get_nonexistent_persisted_revision_returns_none(
        self, async_db_session
    ):
        """존재하지 않는 리비전을 조회하면 None을 반환한다."""
        repo = DatabaseRevisionRepository(async_db_session)
        service = RevisionService(repo)

        result = await service.get("nonexistent_revision")

        assert result is None
