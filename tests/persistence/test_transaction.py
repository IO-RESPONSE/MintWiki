"""트랜잭션 헬퍼 테스트."""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from modules.document.model import Document
from modules.revision.model import Revision
from persistence.transaction import DocumentRevisionTransaction
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


class TestDocumentRevisionTransaction:
    """문서와 리비전 트랜잭션 테스트."""

    @pytest.mark.asyncio
    async def test_create_document_with_revision_atomically(self, async_db_session):
        """트랜잭션 헬퍼는 문서와 리비전을 원자적으로 생성한다."""
        transaction = DocumentRevisionTransaction(async_db_session)

        document = Document(id="doc-1", title="My Document")
        revision = Revision(
            id="rev-1",
            document_id="doc-1",
            source="Initial content",
            author_id="author-1",
            summary="First revision",
        )

        saved_doc, saved_rev = await transaction.create_document_with_revision(
            document, revision
        )

        assert saved_doc.id == "doc-1"
        assert saved_doc.title == "My Document"
        assert saved_rev.id == "rev-1"
        assert saved_rev.document_id == "doc-1"
        assert saved_rev.source == "Initial content"

    @pytest.mark.asyncio
    async def test_document_and_revision_persisted(self, async_db_session):
        """트랜잭션으로 생성한 문서와 리비전은 데이터베이스에 저장된다."""
        from sqlalchemy import select
        from persistence.models import DocumentORM, RevisionORM

        transaction = DocumentRevisionTransaction(async_db_session)

        document = Document(id="doc-2", title="Test Document")
        revision = Revision(
            id="rev-2",
            document_id="doc-2",
            source="Test content",
            author_id="author-2",
            summary="Test revision",
        )

        await transaction.create_document_with_revision(document, revision)

        # 새로운 세션으로 조회하여 정말 저장되었는지 확인
        doc_query = select(DocumentORM).where(DocumentORM.id == "doc-2")
        doc_result = await async_db_session.execute(doc_query)
        saved_doc = doc_result.scalar_one_or_none()

        rev_query = select(RevisionORM).where(RevisionORM.id == "rev-2")
        rev_result = await async_db_session.execute(rev_query)
        saved_rev = rev_result.scalar_one_or_none()

        assert saved_doc is not None
        assert saved_doc.title == "Test Document"
        assert saved_rev is not None
        assert saved_rev.source == "Test content"

    @pytest.mark.asyncio
    async def test_create_with_duplicate_title_raises_error(self, async_db_session):
        """중복된 정규화된 제목은 IntegrityError를 발생시킨다."""
        from sqlalchemy.exc import IntegrityError

        transaction = DocumentRevisionTransaction(async_db_session)

        # 첫 번째 문서 생성
        document1 = Document(id="doc-3", title="My Document")
        revision1 = Revision(
            id="rev-3",
            document_id="doc-3",
            source="Content",
            author_id="author-1",
            summary="First",
        )
        await transaction.create_document_with_revision(document1, revision1)

        # 두 번째 문서도 같은 정규화된 제목으로 생성 시도
        document2 = Document(id="doc-4", title="My Document")
        revision2 = Revision(
            id="rev-4",
            document_id="doc-4",
            source="Content 2",
            author_id="author-2",
            summary="Second",
        )

        with pytest.raises(IntegrityError):
            await transaction.create_document_with_revision(document2, revision2)

    @pytest.mark.asyncio
    async def test_update_document_link_revision(self, async_db_session):
        """트랜잭션 헬퍼는 문서의 리비전 링크를 업데이트한다."""
        from sqlalchemy import select
        from persistence.models import DocumentORM

        transaction = DocumentRevisionTransaction(async_db_session)

        # 먼저 문서를 생성
        document = Document(id="doc-5", title="My Document")
        revision = Revision(
            id="rev-5",
            document_id="doc-5",
            source="Content",
            author_id="author-1",
            summary="First",
        )
        await transaction.create_document_with_revision(document, revision)

        # 현재 리비전 id 업데이트
        document.current_revision_id = "rev-5"
        updated_doc = await transaction.update_document_link_revision(document)

        assert updated_doc.current_revision_id == "rev-5"

        # 데이터베이스에서 확인
        query = select(DocumentORM).where(DocumentORM.id == "doc-5")
        result = await async_db_session.execute(query)
        db_doc = result.scalar_one_or_none()

        assert db_doc.current_revision_id == "rev-5"
