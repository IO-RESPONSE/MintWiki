"""문서 저장소 portability 테스트.

docs/portable-id-column-policy.md, docs/portable-text-collation-policy.md,
docs/portable-query-builder-policy.md 가 정한 정책을 `DatabaseDocumentRepository`가
실제로 만족하는지 검증한다. SQLite는 기본적으로 대소문자를 구분하는 바이너리
비교를 하므로(MariaDB의 `utf8mb4_bin` 기본 collation과 유사한 특성), 이
제약을 SQLite 기반 테스트로 우선 검증한다.
"""
import re
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from modules.document.model import Document
from modules.document.repository import (
    DatabaseDocumentRepository,
    DuplicateNormalizedTitleError,
)
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


class TestPortableIdColumnPolicy:
    """docs/portable-id-column-policy.md: id는 애플리케이션이 uuid4 문자열로 생성한다."""

    @pytest.mark.asyncio
    async def test_stores_and_returns_uuid4_id_unchanged(self, async_db_session):
        """소문자 uuid4 하이픈 문자열 id가 가공 없이 그대로 저장/조회된다."""
        repo = DatabaseDocumentRepository(async_db_session)
        doc_id = str(uuid.uuid4())
        assert UUID4_PATTERN.match(doc_id)

        await repo.create(Document(id=doc_id, title="Portable Id Document"))
        result = await repo.get(doc_id)

        assert result is not None
        assert result.id == doc_id
        assert UUID4_PATTERN.match(result.id)

    @pytest.mark.asyncio
    async def test_does_not_rely_on_db_generated_id(self, async_db_session):
        """DB의 자동 증가/시퀀스 없이 애플리케이션이 지정한 id가 그대로 유지된다."""
        repo = DatabaseDocumentRepository(async_db_session)
        first_id = str(uuid.uuid4())
        second_id = str(uuid.uuid4())

        await repo.create(Document(id=first_id, title="First"))
        await repo.create(Document(id=second_id, title="Second"))

        # id는 생성 순서가 아니라 애플리케이션이 지정한 값으로 조회된다.
        assert (await repo.get(first_id)).id == first_id
        assert (await repo.get(second_id)).id == second_id


class TestPortableTextCollationPolicy:
    """docs/portable-text-collation-policy.md: 문자열 비교는 대소문자를 구분한다."""

    @pytest.mark.asyncio
    async def test_titles_differing_only_by_case_are_not_duplicates(
        self, async_db_session
    ):
        """대소문자만 다른 정규화된 제목은 서로 다른 값으로 취급되어 둘 다 생성된다."""
        repo = DatabaseDocumentRepository(async_db_session)
        await repo.create(Document(id="doc1", title="Test Document"))

        # 대소문자만 다른 제목은 utf8mb4_bin(대소문자 구분) 기준으로 중복이 아니다.
        result = await repo.create(Document(id="doc2", title="test document"))
        assert result.id == "doc2"

    @pytest.mark.asyncio
    async def test_lookup_by_normalized_title_is_case_sensitive(
        self, async_db_session
    ):
        """정규화된 제목 조회는 대소문자가 다르면 일치하지 않는다."""
        repo = DatabaseDocumentRepository(async_db_session)
        await repo.create(Document(id="doc1", title="Test Document"))

        exact_match = await repo.get_by_normalized_title("Test Document")
        case_mismatch = await repo.get_by_normalized_title("test document")

        assert exact_match is not None
        assert exact_match.id == "doc1"
        assert case_mismatch is None

    @pytest.mark.asyncio
    async def test_case_variants_are_independently_retrievable(
        self, async_db_session
    ):
        """대소문자만 다른 두 제목은 각각 독립적으로 조회 가능하다."""
        repo = DatabaseDocumentRepository(async_db_session)
        await repo.create(Document(id="doc1", title="Test Document"))
        await repo.create(Document(id="doc2", title="test document"))

        upper = await repo.get_by_normalized_title("Test Document")
        lower = await repo.get_by_normalized_title("test document")

        assert upper.id == "doc1"
        assert lower.id == "doc2"

    @pytest.mark.asyncio
    async def test_exact_case_duplicate_is_still_rejected(self, async_db_session):
        """대소문자까지 완전히 같은 정규화된 제목은 여전히 중복으로 거부된다."""
        repo = DatabaseDocumentRepository(async_db_session)
        await repo.create(Document(id="doc1", title="Test Document"))

        with pytest.raises(DuplicateNormalizedTitleError):
            await repo.create(Document(id="doc2", title="Test Document"))


class TestPortableQueryBuilderPolicy:
    """docs/portable-query-builder-policy.md: 값은 항상 바인드 파라미터로 전달된다.

    쿼리 빌더 대신 문자열을 이어 붙여 SQL을 조립했다면, 아래처럼 SQL 문법에서
    의미를 갖는 문자(따옴표, 세미콜론, SQL 키워드)가 포함된 제목이 조회/저장
    과정에서 깨지거나 예외를 일으켰을 것이다.
    """

    @pytest.mark.asyncio
    async def test_title_with_quotes_round_trips_unchanged(self, async_db_session):
        """작은따옴표가 포함된 제목이 손상 없이 저장/조회된다."""
        repo = DatabaseDocumentRepository(async_db_session)
        title = "O'Brien's Document"
        await repo.create(Document(id="doc1", title=title))

        result = await repo.get("doc1")
        assert result is not None
        assert result.title == title

    @pytest.mark.asyncio
    async def test_title_with_sql_metacharacters_round_trips_unchanged(
        self, async_db_session
    ):
        """SQL 인젝션 시도처럼 보이는 문자열도 값 그대로 저장/조회된다."""
        repo = DatabaseDocumentRepository(async_db_session)
        title = "Robert'); DROP TABLE document; --"
        await repo.create(Document(id="doc1", title=title))

        result = await repo.get("doc1")
        assert result is not None
        assert result.title == title

        by_title = await repo.get_by_normalized_title(result.normalized_title)
        assert by_title is not None
        assert by_title.id == "doc1"

    @pytest.mark.asyncio
    async def test_lookup_by_normalized_title_with_quotes(self, async_db_session):
        """따옴표가 포함된 정규화된 제목으로도 정확히 조회된다."""
        repo = DatabaseDocumentRepository(async_db_session)
        title = "It's a \"Test\" Document"
        await repo.create(Document(id="doc1", title=title))

        result = await repo.get_by_normalized_title(title)
        assert result is not None
        assert result.id == "doc1"

    @pytest.mark.asyncio
    async def test_table_survives_metacharacter_insert_attempt(
        self, async_db_session
    ):
        """메타문자가 포함된 값을 저장해도 다른 문서 데이터가 온전히 유지된다."""
        repo = DatabaseDocumentRepository(async_db_session)
        await repo.create(Document(id="doc1", title="Safe Document"))
        await repo.create(
            Document(id="doc2", title="Malicious'; DROP TABLE document; --")
        )

        # 두 번째 create가 실제 DDL을 실행하지 않았다면 첫 번째 문서가 그대로 남는다.
        survivor = await repo.get("doc1")
        assert survivor is not None
        assert survivor.title == "Safe Document"
