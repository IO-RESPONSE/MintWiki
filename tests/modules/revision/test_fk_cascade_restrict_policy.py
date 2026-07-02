"""FK의 삭제 시점 동작(cascade/restrict) portability를 고정한다.

`tests/modules/revision/test_portable_repository.py::TestForeignKeyPortability`가
이미 INSERT 시점의 FK 강제(존재하지 않는 document_id를 참조하는 리비전
거부)를 검증한다. 이 파일은 그 반대편, DELETE 시점 동작을 다룬다: 리비전이
참조하는 document 행을 지우려 하면 어떻게 되는가.

`RevisionORM.document_id`의 `ForeignKey`(persistence/models.py),
0003 마이그레이션(`sa.ForeignKeyConstraint`), portable SQL 원본
(db/schema/revision.sql 등) 어디에도 `ondelete="CASCADE"`/`ON DELETE
CASCADE`가 선언되어 있지 않다. PostgreSQL과 MariaDB 모두 이 경우
기본값인 `NO ACTION`을 쓰며, 이는 실질적으로 RESTRICT와 같다 — 참조하는
자식 행이 남아 있는 한 부모 행 삭제를 거부한다. 이 파일은 그 기본 동작이
실제로 이 두 계층(ORM 선언, 런타임 삭제 시도)에서 일관되게 restrict로
고정되어 있는지 검증한다. SQLite는 기본적으로 FK를 강제하지 않으므로
(`PRAGMA foreign_keys=ON`을 켜야 함), 런타임 테스트는 `fk_enforced_db_session`
fixture로 PostgreSQL/MariaDB의 강제 동작을 근사한다
(test_portable_repository.py와 동일한 접근).
"""
from pathlib import Path

import pytest
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from modules.document.model import Document
from modules.document.repository import DatabaseDocumentRepository
from modules.revision.model import Revision
from modules.revision.repository import DatabaseRevisionRepository
from persistence.base import Base
from persistence.models import DocumentORM, RevisionORM


def _db_dir() -> Path:
    return Path(__file__).parent.parent.parent.parent / "db"


@pytest.fixture
async def fk_enforced_db_session():
    """외래 키 제약을 강제하는 인메모리 SQLite 세션을 생성한다.

    test_portable_repository.py의 동일 이름 fixture와 같은 목적이다.
    """
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    @event.listens_for(engine.sync_engine, "connect")
    def _enable_sqlite_fk(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    await engine.dispose()


class TestForeignKeyDeleteIsRestrictedNotCascaded:
    """참조되는 document 행을 지우려는 시도가 RESTRICT(=NO ACTION)로
    거부되는지 검증한다 — CASCADE로 자식 리비전이 함께 지워지지 않는다."""

    @pytest.mark.asyncio
    async def test_deleting_referenced_document_raises_integrity_error(
        self, fk_enforced_db_session
    ):
        """리비전이 참조하는 document를 지우면 FK 위반으로 거부된다."""
        document_repo = DatabaseDocumentRepository(fk_enforced_db_session)
        await document_repo.create(Document(id="doc1", title="Referenced Document"))

        revision_repo = DatabaseRevisionRepository(fk_enforced_db_session)
        await revision_repo.create(
            Revision(
                id="rev1",
                document_id="doc1",
                source="content",
                author_id="user1",
                summary="Initial",
            )
        )

        orm_document = await fk_enforced_db_session.get(DocumentORM, "doc1")
        await fk_enforced_db_session.delete(orm_document)
        with pytest.raises(IntegrityError):
            await fk_enforced_db_session.flush()

    @pytest.mark.asyncio
    async def test_document_and_revision_both_survive_restricted_delete_attempt(
        self, fk_enforced_db_session
    ):
        """거부된 삭제 시도 이후 document와 revision 모두 그대로 남는다(CASCADE 아님)."""
        document_repo = DatabaseDocumentRepository(fk_enforced_db_session)
        await document_repo.create(Document(id="doc1", title="Referenced Document"))

        revision_repo = DatabaseRevisionRepository(fk_enforced_db_session)
        await revision_repo.create(
            Revision(
                id="rev1",
                document_id="doc1",
                source="content",
                author_id="user1",
                summary="Initial",
            )
        )

        orm_document = await fk_enforced_db_session.get(DocumentORM, "doc1")
        await fk_enforced_db_session.delete(orm_document)
        with pytest.raises(IntegrityError):
            await fk_enforced_db_session.flush()
        await fk_enforced_db_session.rollback()

        assert await document_repo.get("doc1") is not None
        assert await revision_repo.get("rev1") is not None

    @pytest.mark.asyncio
    async def test_deleting_document_with_multiple_revisions_is_still_restricted(
        self, fk_enforced_db_session
    ):
        """리비전이 여럿이어도(하나만 남아도) 삭제는 restrict로 거부된다."""
        document_repo = DatabaseDocumentRepository(fk_enforced_db_session)
        await document_repo.create(Document(id="doc1", title="Referenced Document"))

        revision_repo = DatabaseRevisionRepository(fk_enforced_db_session)
        await revision_repo.create(
            Revision(
                id="rev1",
                document_id="doc1",
                source="v1",
                author_id="user1",
                summary="Initial",
            )
        )
        await revision_repo.create(
            Revision(
                id="rev2",
                document_id="doc1",
                source="v2",
                author_id="user1",
                summary="Edit",
                parent_revision_id="rev1",
            )
        )

        # 리비전 하나를 먼저 지워도(다른 하나가 여전히 참조 중이므로) document는
        # 여전히 삭제가 거부되어야 한다 — restrict는 "참조가 하나라도 남아 있으면
        # 막는다"이지 "참조 개수가 줄면 완화된다"가 아니다.
        orm_revision = await fk_enforced_db_session.get(RevisionORM, "rev1")
        await fk_enforced_db_session.delete(orm_revision)
        await fk_enforced_db_session.flush()

        orm_document = await fk_enforced_db_session.get(DocumentORM, "doc1")
        await fk_enforced_db_session.delete(orm_document)
        with pytest.raises(IntegrityError):
            await fk_enforced_db_session.flush()

    @pytest.mark.asyncio
    async def test_deleting_document_without_revisions_succeeds(
        self, fk_enforced_db_session
    ):
        """참조하는 리비전이 없는 document는 정상적으로 삭제된다(대조군)."""
        document_repo = DatabaseDocumentRepository(fk_enforced_db_session)
        await document_repo.create(Document(id="doc1", title="Unreferenced Document"))

        orm_document = await fk_enforced_db_session.get(DocumentORM, "doc1")
        await fk_enforced_db_session.delete(orm_document)
        await fk_enforced_db_session.flush()

        assert await document_repo.get("doc1") is None

    @pytest.mark.asyncio
    async def test_deleting_revision_does_not_cascade_to_document(
        self, fk_enforced_db_session
    ):
        """자식(revision) 삭제는 부모(document) 쪽에 영향을 주지 않는다."""
        document_repo = DatabaseDocumentRepository(fk_enforced_db_session)
        await document_repo.create(Document(id="doc1", title="Referenced Document"))

        revision_repo = DatabaseRevisionRepository(fk_enforced_db_session)
        await revision_repo.create(
            Revision(
                id="rev1",
                document_id="doc1",
                source="content",
                author_id="user1",
                summary="Initial",
            )
        )

        orm_revision = await fk_enforced_db_session.get(RevisionORM, "rev1")
        await fk_enforced_db_session.delete(orm_revision)
        await fk_enforced_db_session.flush()

        assert await document_repo.get("doc1") is not None
        assert await revision_repo.get("rev1") is None


class TestForeignKeyDoesNotDeclareCascadeAtOrmLevel:
    """ORM/마이그레이션이 `ondelete="CASCADE"`를 선언하지 않았다는 사실 자체를
    고정한다 — 위 런타임 restrict 동작이 우연이 아니라 명시적으로
    설정하지 않은 결과임을 보여준다."""

    def test_revision_document_id_fk_has_no_ondelete_clause(self):
        """RevisionORM.document_id의 FK는 ondelete를 지정하지 않는다(NO ACTION 기본값)."""
        column = RevisionORM.__table__.columns["document_id"]
        assert len(column.foreign_keys) == 1
        (fk,) = column.foreign_keys
        assert fk.ondelete is None


class TestPortableSchemaDeclaresNoOnDeleteCascade:
    """db/schema/*.sql의 모든 FK 제약이 ON DELETE CASCADE 없이 선언되어
    PostgreSQL/MariaDB 양쪽 모두 기본값(NO ACTION=사실상 RESTRICT)을 쓰는지
    확인한다 — ORM 레벨 정책(위 클래스)과 portable SQL 원본이 어긋나지
    않아야 한다."""

    SCHEMA_FILES_WITH_FK = (
        "revision.sql",
        "user_session.sql",
        "discussion_thread.sql",
        "discussion_comment.sql",
        "acl_rule.sql",
    )

    def test_schema_files_with_fk_exist(self):
        """이 테스트가 전제하는 FK 포함 스키마 파일들이 실제로 존재한다."""
        schema_dir = _db_dir() / "schema"
        for filename in self.SCHEMA_FILES_WITH_FK:
            assert (schema_dir / filename).exists(), f"{filename} should exist"

    def test_schema_files_declare_foreign_key_without_on_delete_cascade(self):
        """FK를 선언하는 각 스키마 파일에 ON DELETE CASCADE 문구가 없다."""
        schema_dir = _db_dir() / "schema"
        for filename in self.SCHEMA_FILES_WITH_FK:
            content = (schema_dir / filename).read_text()
            assert "FOREIGN KEY" in content, f"{filename} should declare a FOREIGN KEY"
            assert "ON DELETE" not in content, (
                f"{filename} should rely on the NO ACTION default, "
                "not declare an explicit ON DELETE clause"
            )
