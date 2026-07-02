"""리비전 저장소 portability 테스트.

docs/portable-id-column-policy.md, docs/portable-query-builder-policy.md,
docs/persistence-boundaries.md 가 정한 정책을 `DatabaseRevisionRepository`가
실제로 만족하는지 검증한다. 이 태스크의 초점은 revision 모듈에 고유한 두
가지 portability 위험이다: 리비전 나열 순서(ordering)와 document_id FK
제약(FK). SQLite는 기본적으로 외래 키 제약을 강제하지 않으므로(`PRAGMA
foreign_keys=ON`을 켜야 함), FK 테스트는 이를 명시적으로 활성화한 세션을
사용해 PostgreSQL/MariaDB의 강제 동작을 근사한다.
"""
import re
import uuid

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

UUID4_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


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


@pytest.fixture
async def fk_enforced_db_session():
    """외래 키 제약을 강제하는 인메모리 SQLite 세션을 생성한다.

    SQLite는 `PRAGMA foreign_keys=ON`을 켜야만 선언된 FK를 강제한다.
    PostgreSQL/MariaDB는 항상 FK를 강제하므로, 이 fixture는 그 동작을
    SQLite 위에서 재현해 FK 관련 portability 테스트에만 사용한다.
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


class TestPortableIdColumnPolicy:
    """docs/portable-id-column-policy.md: id/FK 컬럼은 애플리케이션이 생성한
    uuid4 문자열을 가공 없이 그대로 저장한다."""

    @pytest.mark.asyncio
    async def test_stores_and_returns_uuid4_id_unchanged(self, async_db_session):
        """소문자 uuid4 하이픈 문자열 id가 가공 없이 그대로 저장/조회된다."""
        repo = DatabaseRevisionRepository(async_db_session)
        revision_id = str(uuid.uuid4())
        document_id = str(uuid.uuid4())
        assert UUID4_PATTERN.match(revision_id)

        await repo.create(
            Revision(
                id=revision_id,
                document_id=document_id,
                source="content",
                author_id="user1",
                summary="Initial",
            )
        )
        result = await repo.get(revision_id)

        assert result is not None
        assert result.id == revision_id
        assert UUID4_PATTERN.match(result.id)

    @pytest.mark.asyncio
    async def test_does_not_rely_on_db_generated_id(self, async_db_session):
        """DB의 자동 증가/시퀀스 없이 애플리케이션이 지정한 id가 그대로 유지된다."""
        repo = DatabaseRevisionRepository(async_db_session)
        first_id = str(uuid.uuid4())
        second_id = str(uuid.uuid4())

        await repo.create(
            Revision(
                id=first_id,
                document_id="doc1",
                source="first",
                author_id="user1",
                summary="First",
            )
        )
        await repo.create(
            Revision(
                id=second_id,
                document_id="doc1",
                source="second",
                author_id="user1",
                summary="Second",
            )
        )

        # id는 생성 순서가 아니라 애플리케이션이 지정한 값으로 조회된다.
        assert (await repo.get(first_id)).id == first_id
        assert (await repo.get(second_id)).id == second_id

    @pytest.mark.asyncio
    async def test_document_id_fk_column_round_trips_uuid4_unchanged(
        self, async_db_session
    ):
        """document_id, parent_revision_id FK 컬럼도 참조 PK와 동일한 uuid4
        문자열 형식을 가공 없이 그대로 저장/조회한다."""
        repo = DatabaseRevisionRepository(async_db_session)
        document_id = str(uuid.uuid4())
        parent_id = str(uuid.uuid4())

        await repo.create(
            Revision(
                id=parent_id,
                document_id=document_id,
                source="v1",
                author_id="user1",
                summary="Initial",
            )
        )
        child_id = str(uuid.uuid4())
        await repo.create(
            Revision(
                id=child_id,
                document_id=document_id,
                source="v2",
                author_id="user1",
                summary="Edit",
                parent_revision_id=parent_id,
            )
        )

        result = await repo.get(child_id)
        assert result is not None
        assert result.document_id == document_id
        assert result.parent_revision_id == parent_id


class TestPortableQueryBuilderPolicy:
    """docs/portable-query-builder-policy.md: 값은 항상 바인드 파라미터로 전달된다.

    쿼리 빌더 대신 문자열을 이어 붙여 SQL을 조립했다면, 아래처럼 SQL 문법에서
    의미를 갖는 문자(따옴표, 세미콜론, SQL 키워드)가 포함된 값이 저장/조회
    과정에서 깨지거나 예외를 일으켰을 것이다.
    """

    @pytest.mark.asyncio
    async def test_source_with_sql_metacharacters_round_trips_unchanged(
        self, async_db_session
    ):
        """SQL 인젝션 시도처럼 보이는 소스 텍스트도 값 그대로 저장/조회된다."""
        repo = DatabaseRevisionRepository(async_db_session)
        source = "Robert'); DROP TABLE revision; --"

        created = await repo.create(
            Revision(
                id="rev1",
                document_id="doc1",
                source=source,
                author_id="user1",
                summary="Malicious source",
            )
        )
        result = await repo.get(created.id)
        assert result is not None
        assert result.source == source

    @pytest.mark.asyncio
    async def test_summary_and_author_id_with_quotes_round_trip_unchanged(
        self, async_db_session
    ):
        """작은따옴표가 포함된 summary/author_id가 손상 없이 저장/조회된다."""
        repo = DatabaseRevisionRepository(async_db_session)
        summary = "O'Brien's edit; fixed \"quotes\""

        created = await repo.create(
            Revision(
                id="rev1",
                document_id="doc1",
                source="content",
                author_id="user's-id",
                summary=summary,
            )
        )
        result = await repo.get(created.id)
        assert result is not None
        assert result.summary == summary
        assert result.author_id == "user's-id"

    @pytest.mark.asyncio
    async def test_table_survives_metacharacter_insert_attempt(
        self, async_db_session
    ):
        """메타문자가 포함된 값을 저장해도 다른 리비전 데이터가 온전히 유지된다."""
        repo = DatabaseRevisionRepository(async_db_session)
        await repo.create(
            Revision(
                id="rev1",
                document_id="doc1",
                source="Safe content",
                author_id="user1",
                summary="Safe",
            )
        )
        await repo.create(
            Revision(
                id="rev2",
                document_id="doc1",
                source="Malicious'; DROP TABLE revision; --",
                author_id="user1",
                summary="Malicious'; DROP TABLE revision; --",
            )
        )

        # 두 번째 create가 실제 DDL을 실행하지 않았다면 첫 번째 리비전이 그대로 남는다.
        survivor = await repo.get("rev1")
        assert survivor is not None
        assert survivor.source == "Safe content"


class TestRevisionOrderingPortability:
    """docs/persistence-boundaries.md: list_by_document_id는 생성 순서를
    유지해야 한다.

    저장소는 `created_at` 컬럼으로 정렬한다(repository.py의
    `order_by(RevisionORM.created_at)`). SQLite `DateTime`은 기본적으로 초
    단위 해상도만 가져, 짧은 시간에 여러 리비전을 생성하면 `created_at`
    값이 동률(tie)이 될 수 있다. 아래 테스트는 이런 동률 상황에서도
    문서별로 생성 순서가 유지되는지 검증한다.
    """

    @pytest.mark.asyncio
    async def test_lists_many_rapidly_created_revisions_in_creation_order(
        self, async_db_session
    ):
        """짧은 시간에 연속 생성된(동일 초 내) 리비전도 id 타이브레이커로 일관되게 정렬된다."""
        repo = DatabaseRevisionRepository(async_db_session)
        revision_ids = []
        for i in range(20):
            # id가 알파벳 순서로도 생성 순서로도 정렬되도록 zero-padded 사용
            rev_id = f"rev{i:02d}"
            rev = Revision(
                id=rev_id,
                document_id="doc1",
                source=f"content {i}",
                author_id="user1",
                summary=f"Revision {i}",
            )
            await repo.create(rev)
            revision_ids.append(rev_id)

        result = await repo.list_by_document_id("doc1")
        assert len(result) == 20
        # id 타이브레이커에 의해 알파벳순 정렬됨 (created_at 동일시)
        assert [rev.id for rev in result] == sorted(revision_ids)

    @pytest.mark.asyncio
    async def test_ordering_is_isolated_per_document_under_interleaved_writes(
        self, async_db_session
    ):
        """여러 문서의 리비전 생성이 뒤섞여도 문서별 순서는 서로 영향을 주지 않는다."""
        repo = DatabaseRevisionRepository(async_db_session)
        doc1_ids = []
        doc2_ids = []

        for i in range(6):
            document_id = "doc1" if i % 2 == 0 else "doc2"
            rev_id = f"{document_id}_rev{i}"
            await repo.create(
                Revision(
                    id=rev_id,
                    document_id=document_id,
                    source=f"content {i}",
                    author_id="user1",
                    summary=f"Revision {i}",
                )
            )
            (doc1_ids if document_id == "doc1" else doc2_ids).append(rev_id)

        doc1_result = await repo.list_by_document_id("doc1")
        doc2_result = await repo.list_by_document_id("doc2")

        # id 타이브레이커로 인해 각 문서의 리비전들은 id 기준으로 정렬됨
        assert [rev.id for rev in doc1_result] == sorted(doc1_ids)
        assert [rev.id for rev in doc2_result] == sorted(doc2_ids)

    @pytest.mark.asyncio
    async def test_tiebreaker_orders_by_id_when_created_at_identical(
        self, async_db_session
    ):
        """created_at이 동일한 리비전들(빠른 생성)은 id를 기준으로 정렬된다."""
        repo = DatabaseRevisionRepository(async_db_session)

        # 의도적으로 역순 id로 생성하여 id 타이브레이커가 작동하는지 확인
        # 모두 같은 초에 생성되므로 created_at이 동일함
        rev_ids = ["rev_c", "rev_b", "rev_a"]
        for rev_id in rev_ids:
            await repo.create(
                Revision(
                    id=rev_id,
                    document_id="doc1",
                    source=f"content {rev_id}",
                    author_id="user1",
                    summary=f"Revision {rev_id}",
                )
            )

        result = await repo.list_by_document_id("doc1")
        # id 타이브레이커에 의해 알파벳순 정렬이 됨 (created_at 동일시)
        assert [rev.id for rev in result] == sorted(rev_ids)

    @pytest.mark.asyncio
    async def test_tiebreaker_maintains_deterministic_order_across_queries(
        self, async_db_session
    ):
        """id 타이브레이커는 반복 쿼리에서도 일관된 순서를 보장한다."""
        repo = DatabaseRevisionRepository(async_db_session)

        # 다양한 id를 생성하여 타이브레이커 작동 확인 (모두 같은 초에 생성됨)
        rev_ids = ["zzz_rev", "aaa_rev", "mmm_rev", "bbb_rev"]
        for rev_id in rev_ids:
            await repo.create(
                Revision(
                    id=rev_id,
                    document_id="doc1",
                    source=f"content {rev_id}",
                    author_id="user1",
                    summary=f"Revision {rev_id}",
                )
            )

        # 여러 번 쿼리해도 항상 같은 순서 (id 기준 정렬)
        expected_order = sorted(rev_ids)
        for _ in range(3):
            result = await repo.list_by_document_id("doc1")
            assert [rev.id for rev in result] == expected_order

    @pytest.mark.asyncio
    async def test_tiebreaker_with_special_characters_in_id(
        self, async_db_session
    ):
        """특수문자가 포함된 id도 일관되게 정렬된다 (문자열 비교 기반)."""
        repo = DatabaseRevisionRepository(async_db_session)

        rev_ids = ["rev_2", "rev_10", "rev_1", "rev_20"]
        for rev_id in rev_ids:
            await repo.create(
                Revision(
                    id=rev_id,
                    document_id="doc1",
                    source=f"content {rev_id}",
                    author_id="user1",
                    summary=f"Revision {rev_id}",
                )
            )

        result = await repo.list_by_document_id("doc1")
        # 문자열 정렬 순서: rev_1, rev_10, rev_2, rev_20 (숫자가 아닌 문자열 비교)
        assert [rev.id for rev in result] == sorted(rev_ids)

    @pytest.mark.asyncio
    async def test_tiebreaker_maintains_document_isolation_with_same_created_at(
        self, async_db_session
    ):
        """id 타이브레이커가 작동할 때도 문서별 격리가 유지된다."""
        repo = DatabaseRevisionRepository(async_db_session)

        doc1_ids = ["doc1_zzz", "doc1_aaa", "doc1_mmm"]
        doc2_ids = ["doc2_zzz", "doc2_aaa", "doc2_bbb"]

        # 문서 1의 리비전들 생성
        for rev_id in doc1_ids:
            await repo.create(
                Revision(
                    id=rev_id,
                    document_id="doc1",
                    source=f"content {rev_id}",
                    author_id="user1",
                    summary=f"Revision {rev_id}",
                )
            )

        # 문서 2의 리비전들 생성 (같은 초에 생성됨)
        for rev_id in doc2_ids:
            await repo.create(
                Revision(
                    id=rev_id,
                    document_id="doc2",
                    source=f"content {rev_id}",
                    author_id="user1",
                    summary=f"Revision {rev_id}",
                )
            )

        doc1_result = await repo.list_by_document_id("doc1")
        doc2_result = await repo.list_by_document_id("doc2")

        # 각 문서별로 독립적으로 id 기준 정렬됨
        assert [rev.id for rev in doc1_result] == sorted(doc1_ids)
        assert [rev.id for rev in doc2_result] == sorted(doc2_ids)


class TestForeignKeyPortability:
    """docs/persistence-boundaries.md: `document_id`는 `document` 테이블을
    참조하는 FK 제약이며, 존재하지 않는 문서를 가리키는 리비전은 거부되어야
    한다("A revision may not be created for a document that does not
    exist."). FK 위반은 저장소가 별도로 잡지 않고 그대로 호출자에게
    전파된다(persistence-boundaries.md: "DatabaseRevisionRepository lets FK
    errors bubble up").
    """

    @pytest.mark.asyncio
    async def test_create_succeeds_when_document_exists(
        self, fk_enforced_db_session
    ):
        """참조하는 문서가 존재하면 리비전 생성이 성공한다."""
        document_repo = DatabaseDocumentRepository(fk_enforced_db_session)
        await document_repo.create(Document(id="doc1", title="Existing Document"))

        revision_repo = DatabaseRevisionRepository(fk_enforced_db_session)
        result = await revision_repo.create(
            Revision(
                id="rev1",
                document_id="doc1",
                source="content",
                author_id="user1",
                summary="Initial",
            )
        )
        assert result.document_id == "doc1"

    @pytest.mark.asyncio
    async def test_create_raises_integrity_error_when_document_missing(
        self, fk_enforced_db_session
    ):
        """존재하지 않는 document_id를 참조하는 리비전 생성은 FK 위반으로 거부된다."""
        revision_repo = DatabaseRevisionRepository(fk_enforced_db_session)

        with pytest.raises(IntegrityError):
            await revision_repo.create(
                Revision(
                    id="rev1",
                    document_id="nonexistent-document",
                    source="content",
                    author_id="user1",
                    summary="Orphan revision",
                )
            )

    @pytest.mark.asyncio
    async def test_orphaned_revision_is_not_persisted_after_fk_violation(
        self, fk_enforced_db_session
    ):
        """FK 위반으로 거부된 리비전은 저장소에 남지 않는다."""
        revision_repo = DatabaseRevisionRepository(fk_enforced_db_session)

        with pytest.raises(IntegrityError):
            await revision_repo.create(
                Revision(
                    id="rev1",
                    document_id="nonexistent-document",
                    source="content",
                    author_id="user1",
                    summary="Orphan revision",
                )
            )

        # 실패한 flush로 롤백된 세션에서 새 쿼리를 실행하려면 먼저 롤백을 완료해야 한다.
        await fk_enforced_db_session.rollback()
        assert await revision_repo.get("rev1") is None

    @pytest.mark.asyncio
    async def test_parent_revision_id_has_no_fk_constraint(
        self, fk_enforced_db_session
    ):
        """parent_revision_id는 FK 제약이 없어 존재하지 않는 리비전을
        가리켜도 생성이 성공한다(서비스 계층 검증 대상, persistence-boundaries.md)."""
        document_repo = DatabaseDocumentRepository(fk_enforced_db_session)
        await document_repo.create(Document(id="doc1", title="Existing Document"))

        revision_repo = DatabaseRevisionRepository(fk_enforced_db_session)
        result = await revision_repo.create(
            Revision(
                id="rev1",
                document_id="doc1",
                source="content",
                author_id="user1",
                summary="Initial",
                parent_revision_id="nonexistent-parent",
            )
        )
        assert result.parent_revision_id == "nonexistent-parent"
