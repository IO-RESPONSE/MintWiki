"""문서 duplicate 처리를 error code(예외 타입/HTTP status code) 중심으로 검증한다.

메시지 문자열이 아니라 "어떤 에러 코드가 나오는가"에 초점을 맞춘다:

- 저장소 계층: 원시 `IntegrityError`가 아니라 도메인 예외
  `DuplicateNormalizedTitleError`가 나가야 한다(호출자에게 DB 세부사항이
  새면 안 된다).
- 서비스 계층: 저장소 구현(in-memory/database)이 달라도 같은 예외 타입이
  나와야 한다.
- 라우터 계층: HTTP status code가 409로 고정되어야 하고, 응답 본문에
  드라이버/SQL 텍스트가 섞이면 안 된다.

docs/portable-duplicate-key-handling.md가 지적하는 대로, 지금 구현은
`str(e)`에 컬럼 이름이 포함되는지만 보는 부분 문자열 매칭을 쓴다. 이
파일은 그 구현을 바꾸지 않고(0475 범위는 테스트만), 현재 각 경로가 실제로
어떤 에러 코드를 내보내는지를 고정한다 — 트랜잭션 경로(§ 아래
`TestDuplicateErrorAtTransactionalServiceLayer`)처럼 아직 정책을 만족하지
못하는 경로가 있다면 그 사실도 테스트로 드러낸다.
"""
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from modules.document.model import Document
from modules.document.repository import (
    DatabaseDocumentRepository,
    DuplicateNormalizedTitleError,
    InMemoryDocumentRepository,
)
from modules.document.service import DocumentService
from modules.revision.repository import DatabaseRevisionRepository
from persistence.base import Base
from persistence.transaction import DocumentRevisionTransaction

# 저장소 계층 원시 에러 텍스트가 도메인 예외 메시지에 섞이면 안 되는 토큰들.
DRIVER_LEAK_TOKENS = (
    "insert into",
    "select ",
    "sqlite3",
    "integrityerror",
    "unique constraint",
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


class TestDuplicateErrorTypeAtRepositoryLevel:
    """DatabaseDocumentRepository.create가 내보내는 에러 코드(예외 타입)를 검증한다."""

    @pytest.mark.asyncio
    async def test_duplicate_create_raises_exact_domain_error_type(
        self, async_db_session
    ):
        """중복 생성은 정확히 DuplicateNormalizedTitleError 타입을 낸다."""
        repo = DatabaseDocumentRepository(async_db_session)
        await repo.create(Document(id="doc1", title="Test Document"))

        with pytest.raises(DuplicateNormalizedTitleError) as exc_info:
            await repo.create(Document(id="doc2", title="Test Document"))

        assert type(exc_info.value) is DuplicateNormalizedTitleError

    @pytest.mark.asyncio
    async def test_duplicate_error_does_not_leak_raw_integrity_error(
        self, async_db_session
    ):
        """호출자는 원시 IntegrityError가 아니라 도메인 예외만 받는다."""
        repo = DatabaseDocumentRepository(async_db_session)
        await repo.create(Document(id="doc1", title="Test Document"))

        with pytest.raises(DuplicateNormalizedTitleError) as exc_info:
            await repo.create(Document(id="doc2", title="Test Document"))

        assert not isinstance(exc_info.value, IntegrityError)

    @pytest.mark.asyncio
    async def test_duplicate_error_message_has_no_driver_or_sql_leak(
        self, async_db_session
    ):
        """도메인 예외 메시지에 SQL 문/드라이버 원문이 섞이지 않는다."""
        repo = DatabaseDocumentRepository(async_db_session)
        await repo.create(Document(id="doc1", title="Test Document"))

        with pytest.raises(DuplicateNormalizedTitleError) as exc_info:
            await repo.create(Document(id="doc2", title="Test Document"))

        message = str(exc_info.value).lower()
        for token in DRIVER_LEAK_TOKENS:
            assert token not in message

    @pytest.mark.asyncio
    async def test_repeated_duplicate_attempts_each_raise_same_error_type(
        self, async_db_session
    ):
        """같은 제목으로 반복 시도해도 매번 동일한 에러 코드가 나온다."""
        repo = DatabaseDocumentRepository(async_db_session)
        await repo.create(Document(id="doc1", title="Test Document"))

        for attempt in range(3):
            with pytest.raises(DuplicateNormalizedTitleError) as exc_info:
                await repo.create(Document(id=f"doc-attempt-{attempt}", title="Test Document"))
            assert type(exc_info.value) is DuplicateNormalizedTitleError

    @pytest.mark.asyncio
    async def test_duplicate_error_does_not_break_session_for_later_creates(
        self, async_db_session
    ):
        """중복 에러 이후에도 세션은 정상적인 새 문서 생성을 계속 처리한다."""
        repo = DatabaseDocumentRepository(async_db_session)
        await repo.create(Document(id="doc1", title="Test Document"))

        with pytest.raises(DuplicateNormalizedTitleError):
            await repo.create(Document(id="doc2", title="Test Document"))

        # rollback 이후에도 서로 다른 제목의 문서는 정상적으로 생성돼야 한다.
        result = await repo.create(Document(id="doc3", title="Another Document"))
        assert result.id == "doc3"


class TestDuplicateErrorTypeConsistentAcrossRepositoryImplementations:
    """어떤 저장소 구현을 쓰든 duplicate의 에러 코드(예외 타입)는 같아야 한다."""

    @pytest.mark.asyncio
    async def test_in_memory_repository_duplicate_error_type(self):
        """인메모리 저장소도 정확히 DuplicateNormalizedTitleError를 낸다."""
        repo = InMemoryDocumentRepository()
        await repo.create(Document(id="doc1", title="Test Document"))

        with pytest.raises(DuplicateNormalizedTitleError) as exc_info:
            await repo.create(Document(id="doc2", title="Test Document"))

        assert type(exc_info.value) is DuplicateNormalizedTitleError

    @pytest.mark.asyncio
    async def test_database_repository_duplicate_error_type(self, async_db_session):
        """데이터베이스 저장소도 정확히 DuplicateNormalizedTitleError를 낸다."""
        repo = DatabaseDocumentRepository(async_db_session)
        await repo.create(Document(id="doc1", title="Test Document"))

        with pytest.raises(DuplicateNormalizedTitleError) as exc_info:
            await repo.create(Document(id="doc2", title="Test Document"))

        assert type(exc_info.value) is DuplicateNormalizedTitleError


class TestDuplicateErrorAtTransactionalServiceLayer:
    """`DocumentRevisionTransaction`을 쓰는 경로의 에러 코드를 고정한다.

    `persistence/transaction.py`의 `create_document_with_revision`은 중복
    시 `IntegrityError`를 그대로 재전파한다(`DuplicateNormalizedTitleError`로
    바꾸지 않는다) — `DatabaseDocumentRepository.create`(비-트랜잭션 경로)와
    에러 코드가 갈린다. 이 테스트는 그 실제 동작을 고정해, 두 경로의 에러
    코드가 일치하지 않는다는 사실을 드러낸다. `persistence/transaction.py`
    수정은 이 태스크(0475, tests/modules/document)의 범위 밖이다.
    """

    @pytest.mark.asyncio
    async def test_transactional_duplicate_create_raises_integrity_error(
        self, async_db_session
    ):
        """소스와 함께 생성하는 트랜잭션 경로는 현재 원시 IntegrityError를 낸다."""
        doc_repo = DatabaseDocumentRepository(async_db_session)
        revision_repo = DatabaseRevisionRepository(async_db_session)
        transaction = DocumentRevisionTransaction(async_db_session)
        service = DocumentService(doc_repo, revision_repo, transaction)

        await service.create("Test Document", source="first revision")

        with pytest.raises(IntegrityError):
            await service.create("Test Document", source="second revision")

    @pytest.mark.asyncio
    async def test_non_transactional_duplicate_create_raises_domain_error(
        self, async_db_session
    ):
        """소스 없이 생성하는 비-트랜잭션 경로는 도메인 예외를 낸다(대조군)."""
        doc_repo = DatabaseDocumentRepository(async_db_session)
        service = DocumentService(doc_repo)

        await service.create("Test Document")

        with pytest.raises(DuplicateNormalizedTitleError):
            await service.create("Test Document")


class TestDuplicateErrorAtRouterLevel:
    """HTTP 계층의 에러 코드(status code, 응답 본문)를 검증한다."""

    def test_duplicate_response_status_code_is_409(self, client):
        """중복 제목 생성 요청은 409 Conflict를 반환한다."""
        client.post(
            "/api/documents",
            json={"title": "Router Duplicate Title", "source": "content"},
        )
        response = client.post(
            "/api/documents",
            json={"title": "Router Duplicate Title", "source": "content2"},
        )

        assert response.status_code == 409

    def test_duplicate_response_detail_has_no_driver_or_sql_leak(self, client):
        """409 응답의 detail에는 SQL/드라이버 원문이 섞이지 않는다."""
        client.post(
            "/api/documents",
            json={"title": "Leak Check Title", "source": "content"},
        )
        response = client.post(
            "/api/documents",
            json={"title": "Leak Check Title", "source": "content2"},
        )

        assert response.status_code == 409
        detail = response.json()["detail"].lower()
        for token in DRIVER_LEAK_TOKENS:
            assert token not in detail

    def test_repeated_duplicate_requests_all_return_409(self, client):
        """같은 제목으로 반복 요청해도 매번 409가 반환된다."""
        client.post(
            "/api/documents",
            json={"title": "Repeated Duplicate Title", "source": "content"},
        )

        for attempt in range(3):
            response = client.post(
                "/api/documents",
                json={"title": "Repeated Duplicate Title", "source": f"content-{attempt}"},
            )
            assert response.status_code == 409
            assert "detail" in response.json()

    def test_duplicate_requests_do_not_change_original_document(self, client):
        """중복 요청이 반복돼도 원본 문서는 그대로 유지된다."""
        create_response = client.post(
            "/api/documents",
            json={"title": "Stable Title", "source": "original content"},
        )
        original_id = create_response.json()["id"]

        for attempt in range(2):
            client.post(
                "/api/documents",
                json={"title": "Stable Title", "source": f"rejected-{attempt}"},
            )

        lookup_response = client.get("/api/documents/by-title", params={"title": "Stable Title"})
        assert lookup_response.status_code == 200
        assert lookup_response.json()["id"] == original_id
