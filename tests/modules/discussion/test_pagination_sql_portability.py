"""페이지네이션 SQL portability 테스트.

docs/discussion-portable-repository-plan.md §5가 확정한 페이지네이션
결정성 계약 -- 필터 컬럼으로 좁힌 뒤 `ORDER BY created_at, id`로 정렬하고
`LIMIT`/`OFFSET`으로 여러 번에 걸쳐 잘라 호출해도 행이 중복되거나
누락되지 않는다 -- 을 db/schema/의 portable SQL 원본에 대해 직접 실행해
검증한다.

discussion 모듈은 아직 Database*Repository/Alembic 마이그레이션이 없다
(discussion-portable-repository-plan.md §1, §7 "이 문서 이후 단계" --
그 구현체는 별도 후속 태스크 범위). 그래서 이 파일은 SQLAlchemy ORM
모델이 아니라 db/schema/document.sql, discussion_thread.sql,
discussion_comment.sql을 그대로 실행한 raw sqlite3 연결에 대해 계획
문서가 명시한 쿼리 형태(`ORDER BY <필터 컬럼>, created_at, id LIMIT ?
OFFSET ?`)를 직접 실행한다. db/schema/*.sql이 실제로 존재하는지, 컬럼이
계획과 일치하는지는 tests/test_db_directory.py가 이미 문자열 비교로
고정해 두었으므로, 이 파일은 그 SQL을 실제로 실행했을 때의 런타임
페이지네이션 동작만 다룬다.
"""
import sqlite3
import uuid
from pathlib import Path

import pytest


def _schema_sql_dir() -> Path:
    return Path(__file__).parent.parent.parent.parent / "db" / "schema"


@pytest.fixture
def paginated_sqlite_connection():
    """document/discussion_thread/discussion_comment portable SQL을 그대로 실행한 SQLite 연결."""
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")

    schema_dir = _schema_sql_dir()
    for filename in ("document.sql", "discussion_thread.sql", "discussion_comment.sql"):
        connection.executescript((schema_dir / filename).read_text())

    yield connection

    connection.close()


def _insert_document(connection: sqlite3.Connection, document_id: str) -> None:
    connection.execute(
        """
        INSERT INTO document (id, title, normalized_title, created_at, updated_at)
        VALUES (?, ?, ?, '2026-01-01T00:00:00', '2026-01-01T00:00:00')
        """,
        (document_id, document_id, document_id),
    )


def _insert_thread(
    connection: sqlite3.Connection, thread_id: str, document_id: str, created_at: str
) -> None:
    connection.execute(
        """
        INSERT INTO discussion_thread (id, document_id, title, created_by, created_at)
        VALUES (?, ?, ?, 'user1', ?)
        """,
        (thread_id, document_id, thread_id, created_at),
    )


def _insert_comment(
    connection: sqlite3.Connection, comment_id: str, thread_id: str, created_at: str
) -> None:
    connection.execute(
        """
        INSERT INTO discussion_comment (id, thread_id, body, created_by, created_at)
        VALUES (?, ?, ?, 'user1', ?)
        """,
        (comment_id, thread_id, comment_id, created_at),
    )


def _select_thread_page(
    connection: sqlite3.Connection, document_id: str, limit: int, offset: int
) -> list[str]:
    rows = connection.execute(
        """
        SELECT id FROM discussion_thread
        WHERE document_id = ?
        ORDER BY created_at, id
        LIMIT ? OFFSET ?
        """,
        (document_id, limit, offset),
    ).fetchall()
    return [row[0] for row in rows]


def _select_comment_page(
    connection: sqlite3.Connection, thread_id: str, limit: int, offset: int
) -> list[str]:
    rows = connection.execute(
        """
        SELECT id FROM discussion_comment
        WHERE thread_id = ?
        ORDER BY created_at, id
        LIMIT ? OFFSET ?
        """,
        (thread_id, limit, offset),
    ).fetchall()
    return [row[0] for row in rows]


class TestThreadPaginationDeterminism:
    """discussion_thread에 대한 (document_id, created_at, id) 정렬 + LIMIT/OFFSET 계약."""

    def test_limit_offset_pages_reconstruct_full_ordered_result_without_gaps_or_duplicates(
        self, paginated_sqlite_connection
    ):
        """페이지 크기 3으로 여러 번 잘라 호출한 결과를 이어붙이면 전체 조회 결과와 정확히 같다."""
        document_id = "doc1"
        _insert_document(paginated_sqlite_connection, document_id)
        # 동시각(tie)을 의도적으로 섞어 넣는다: t1은 세 스레드가 같은
        # created_at을 공유한다 (discussion-portable-repository-plan.md §5
        # "동시각이 실제로 생기는가" 참고).
        thread_ids = [f"thread{i}" for i in range(7)]
        timestamps = [
            "2026-01-01T00:00:00",
            "2026-01-01T00:00:00",
            "2026-01-01T00:00:00",
            "2026-01-02T00:00:00",
            "2026-01-03T00:00:00",
            "2026-01-03T00:00:00",
            "2026-01-04T00:00:00",
        ]
        for thread_id, created_at in zip(thread_ids, timestamps):
            _insert_thread(paginated_sqlite_connection, thread_id, document_id, created_at)

        full_result = _select_thread_page(
            paginated_sqlite_connection, document_id, limit=100, offset=0
        )

        paged_result: list[str] = []
        page_size = 3
        for offset in range(0, len(thread_ids), page_size):
            paged_result.extend(
                _select_thread_page(
                    paginated_sqlite_connection, document_id, limit=page_size, offset=offset
                )
            )

        assert paged_result == full_result
        assert len(paged_result) == len(thread_ids)
        assert len(set(paged_result)) == len(paged_result)

    def test_tie_broken_by_id_when_created_at_is_identical(self, paginated_sqlite_connection):
        """created_at이 완전히 같은 행들은 id 오름차순으로 결정적으로 정렬된다."""
        document_id = "doc1"
        _insert_document(paginated_sqlite_connection, document_id)
        same_timestamp = "2026-01-01T00:00:00"
        # 삽입 순서를 id 오름차순과 일부러 어긋나게 둬서, 정렬이 삽입 순서가
        # 아니라 실제로 id 값을 보고 있는지 드러낸다.
        for thread_id in ("thread-c", "thread-a", "thread-b"):
            _insert_thread(paginated_sqlite_connection, thread_id, document_id, same_timestamp)

        result = _select_thread_page(paginated_sqlite_connection, document_id, limit=100, offset=0)

        assert result == ["thread-a", "thread-b", "thread-c"]

    def test_offset_beyond_row_count_returns_empty(self, paginated_sqlite_connection):
        """전체 행 수를 넘는 offset은 빈 목록을 반환한다."""
        document_id = "doc1"
        _insert_document(paginated_sqlite_connection, document_id)
        for i in range(3):
            _insert_thread(
                paginated_sqlite_connection, f"thread{i}", document_id, "2026-01-01T00:00:00"
            )

        result = _select_thread_page(paginated_sqlite_connection, document_id, limit=10, offset=10)

        assert result == []

    def test_last_page_returns_remaining_rows_shorter_than_limit(
        self, paginated_sqlite_connection
    ):
        """마지막 페이지는 limit보다 적은 나머지 행만 반환한다."""
        document_id = "doc1"
        _insert_document(paginated_sqlite_connection, document_id)
        for i in range(5):
            _insert_thread(
                paginated_sqlite_connection, f"thread{i}", document_id, "2026-01-01T00:00:00"
            )

        last_page = _select_thread_page(paginated_sqlite_connection, document_id, limit=3, offset=3)

        assert len(last_page) == 2

    def test_pagination_is_isolated_per_document_id(self, paginated_sqlite_connection):
        """다른 document_id의 스레드는 페이지 결과에 섞이지 않는다."""
        _insert_document(paginated_sqlite_connection, "doc1")
        _insert_document(paginated_sqlite_connection, "doc2")
        _insert_thread(paginated_sqlite_connection, "doc1-thread", "doc1", "2026-01-01T00:00:00")
        _insert_thread(paginated_sqlite_connection, "doc2-thread", "doc2", "2026-01-01T00:00:00")

        result = _select_thread_page(paginated_sqlite_connection, "doc1", limit=100, offset=0)

        assert result == ["doc1-thread"]


class TestCommentPaginationDeterminism:
    """discussion_comment에 대한 (thread_id, created_at, id) 정렬 + LIMIT/OFFSET 계약.

    스레드/댓글은 계획 문서(§3~§5)가 동일한 페이지네이션 설계를 두 번
    적용한 것이므로, 여기서는 discussion_comment에서도 같은 계약이
    성립하는지만 확인한다(스레드 쪽과 같은 시나리오 반복은 생략).
    """

    @pytest.fixture
    def thread_with_document(self, paginated_sqlite_connection):
        document_id = str(uuid.uuid4())
        thread_id = str(uuid.uuid4())
        _insert_document(paginated_sqlite_connection, document_id)
        _insert_thread(paginated_sqlite_connection, thread_id, document_id, "2026-01-01T00:00:00")
        return thread_id

    def test_limit_offset_pages_reconstruct_full_ordered_result_without_gaps_or_duplicates(
        self, paginated_sqlite_connection, thread_with_document
    ):
        """댓글도 페이지 단위로 잘라 이어붙이면 전체 조회 결과와 정확히 같다."""
        thread_id = thread_with_document
        comment_ids = [f"comment{i}" for i in range(6)]
        timestamps = [
            "2026-01-01T00:00:00",
            "2026-01-01T00:00:00",
            "2026-01-02T00:00:00",
            "2026-01-03T00:00:00",
            "2026-01-03T00:00:00",
            "2026-01-04T00:00:00",
        ]
        for comment_id, created_at in zip(comment_ids, timestamps):
            _insert_comment(paginated_sqlite_connection, comment_id, thread_id, created_at)

        full_result = _select_comment_page(
            paginated_sqlite_connection, thread_id, limit=100, offset=0
        )

        paged_result: list[str] = []
        page_size = 2
        for offset in range(0, len(comment_ids), page_size):
            paged_result.extend(
                _select_comment_page(
                    paginated_sqlite_connection, thread_id, limit=page_size, offset=offset
                )
            )

        assert paged_result == full_result
        assert len(paged_result) == len(comment_ids)
        assert len(set(paged_result)) == len(paged_result)

    def test_tie_broken_by_id_when_created_at_is_identical(
        self, paginated_sqlite_connection, thread_with_document
    ):
        """created_at이 같은 댓글들도 id 오름차순으로 결정적으로 정렬된다."""
        thread_id = thread_with_document
        same_timestamp = "2026-01-01T00:00:00"
        for comment_id in ("comment-z", "comment-x", "comment-y"):
            _insert_comment(paginated_sqlite_connection, comment_id, thread_id, same_timestamp)

        result = _select_comment_page(paginated_sqlite_connection, thread_id, limit=100, offset=0)

        assert result == ["comment-x", "comment-y", "comment-z"]

    def test_pagination_is_isolated_per_thread_id(self, paginated_sqlite_connection):
        """다른 thread_id의 댓글은 페이지 결과에 섞이지 않는다."""
        document_id = "doc1"
        _insert_document(paginated_sqlite_connection, document_id)
        _insert_thread(paginated_sqlite_connection, "thread1", document_id, "2026-01-01T00:00:00")
        _insert_thread(paginated_sqlite_connection, "thread2", document_id, "2026-01-01T00:00:00")
        _insert_comment(
            paginated_sqlite_connection, "thread1-comment", "thread1", "2026-01-01T00:00:00"
        )
        _insert_comment(
            paginated_sqlite_connection, "thread2-comment", "thread2", "2026-01-01T00:00:00"
        )

        result = _select_comment_page(paginated_sqlite_connection, "thread1", limit=100, offset=0)

        assert result == ["thread1-comment"]


class TestInMemoryPaginationMatchesPortableSqlPagination:
    """InMemoryDiscussionRepository의 list slicing과 portable SQL LIMIT/OFFSET이
    같은 입력에 대해 같은 페이지 경계를 만드는지 대조한다.

    discussion-portable-repository-plan.md §1이 지적하듯
    `InMemoryDiscussionRepository`는 이미 `list[offset:offset+limit]`
    형태로 페이지네이션 계약을 구현해 두었다 -- 미래 Database 구현체가
    같은 인터페이스 계약을 지켜야 하므로, 두 백엔드가 같은 정렬 입력에
    대해 같은 페이지를 반환하는지 미리 고정해 둔다.
    """

    @pytest.mark.asyncio
    async def test_thread_pagination_matches_in_memory_repository_slicing(
        self, paginated_sqlite_connection
    ):
        from datetime import datetime, timezone

        from modules.discussion.repository import InMemoryDiscussionRepository
        from modules.discussion.thread import DiscussionThread

        document_id = "doc1"
        _insert_document(paginated_sqlite_connection, document_id)

        # InMemoryDiscussionRepository는 정렬 없이 삽입 순서를 그대로
        # 페이지네이션하므로(list[offset:offset+limit]), 여기서는 삽입
        # 순서를 created_at 오름차순과 일치시켜 두 백엔드가 같은 정렬
        # 입력에 대해 비교 가능하도록 만든다.
        in_memory_repo = InMemoryDiscussionRepository()
        thread_ids = [f"thread{i}" for i in range(5)]
        for i, thread_id in enumerate(thread_ids):
            created_at = datetime(2026, 1, i + 1, tzinfo=timezone.utc)
            _insert_thread(
                paginated_sqlite_connection, thread_id, document_id, created_at.isoformat()
            )
            await in_memory_repo.create_thread(
                DiscussionThread(
                    id=thread_id,
                    document_id=document_id,
                    title=thread_id,
                    created_by="user1",
                    created_at=created_at,
                )
            )

        sql_page = _select_thread_page(paginated_sqlite_connection, document_id, limit=2, offset=1)
        in_memory_page = await in_memory_repo.list_threads_by_document_id(
            document_id, limit=2, offset=1
        )

        assert sql_page == [thread.id for thread in in_memory_page]
