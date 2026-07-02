"""정렬(ORDER BY) SQL portability 테스트.

docs/acl-portable-repository-plan.md §5가 확정한 규칙 우선순위 재현
계약 -- `acl_rule`/`acl_namespace_rule`은 전용 정수 컬럼 `sort_order`로
순서를 저장하고, `ORDER BY sort_order`로 그 순서를 그대로 재현한다 --
을 db/schema/의 portable SQL 원본에 대해 직접 실행해 검증한다.

이 계약은 discussion 모듈의 페이지네이션 정렬
(test_pagination_sql_portability.py, `ORDER BY created_at, id`)과
다른 문제를 다룬다: `sort_order`는 동시각(tie)에 기대는 대신 애플리케이션이
채우는 전용 정수 값이므로 애초에 동률이 생기지 않는다
(`UNIQUE(document_id, sort_order)`/`UNIQUE(namespace, sort_order)`가 이를
스키마 레벨에서 강제한다) -- 정렬 기준 컬럼이 NULL이거나 로케일에 따라
비교 결과가 달라지는 문자열일 위험이 없다.

acl 모듈은 아직 Database*Repository/Alembic 마이그레이션이 없다
(acl-portable-repository-plan.md §1, §7 "이 문서 이후 단계" -- 그
구현체는 별도 후속 태스크 범위). 그래서 이 파일은 SQLAlchemy ORM 모델이
아니라 db/schema/document.sql, acl_rule.sql, acl_namespace_rule.sql을
그대로 실행한 raw sqlite3 연결에 대해 계획 문서가 명시한 쿼리 형태
(`ORDER BY sort_order`)를 직접 실행한다. db/schema/*.sql이 실제로
존재하는지, 컬럼이 계획과 일치하는지는 tests/test_db_directory.py가 이미
문자열 비교로 고정해 두었으므로, 이 파일은 그 SQL을 실제로 실행했을 때의
런타임 정렬 동작만 다룬다.
"""
import sqlite3
from pathlib import Path

import pytest


def _schema_sql_dir() -> Path:
    return Path(__file__).parent.parent.parent.parent / "db" / "schema"


@pytest.fixture
def sorted_sqlite_connection():
    """document/acl_rule/acl_namespace_rule portable SQL을 그대로 실행한 SQLite 연결."""
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")

    schema_dir = _schema_sql_dir()
    for filename in ("document.sql", "acl_rule.sql", "acl_namespace_rule.sql"):
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


def _insert_acl_rule(
    connection: sqlite3.Connection, rule_id: str, document_id: str, sort_order: int
) -> None:
    connection.execute(
        """
        INSERT INTO acl_rule
            (id, document_id, subject_type, subject_id, permission, effect, sort_order)
        VALUES (?, ?, 'user', 'user1', 'read', 'allow', ?)
        """,
        (rule_id, document_id, sort_order),
    )


def _insert_namespace_rule(
    connection: sqlite3.Connection, rule_id: str, namespace: str, sort_order: int
) -> None:
    connection.execute(
        """
        INSERT INTO acl_namespace_rule
            (id, namespace, subject_type, subject_id, permission, effect, sort_order)
        VALUES (?, ?, 'user', 'user1', 'read', 'allow', ?)
        """,
        (rule_id, namespace, sort_order),
    )


def _select_rule_order(connection: sqlite3.Connection, document_id: str) -> list[str]:
    rows = connection.execute(
        """
        SELECT id FROM acl_rule
        WHERE document_id = ?
        ORDER BY sort_order
        """,
        (document_id,),
    ).fetchall()
    return [row[0] for row in rows]


def _select_namespace_rule_order(connection: sqlite3.Connection, namespace: str) -> list[str]:
    rows = connection.execute(
        """
        SELECT id FROM acl_namespace_rule
        WHERE namespace = ?
        ORDER BY sort_order
        """,
        (namespace,),
    ).fetchall()
    return [row[0] for row in rows]


class TestAclRuleSortOrderPortability:
    """acl_rule에 대한 (document_id, sort_order) 정렬 계약."""

    def test_order_by_sort_order_reproduces_priority_regardless_of_insertion_order(
        self, sorted_sqlite_connection
    ):
        """삽입 순서와 sort_order 순서가 어긋나도, 조회 결과는 sort_order 오름차순을 따른다."""
        document_id = "doc1"
        _insert_document(sorted_sqlite_connection, document_id)
        # 삽입 순서를 sort_order 오름차순과 일부러 어긋나게 둬서, 정렬이
        # 삽입 순서가 아니라 실제로 sort_order 값을 보고 있는지 드러낸다.
        for rule_id, sort_order in (("rule-c", 2), ("rule-a", 0), ("rule-b", 1)):
            _insert_acl_rule(sorted_sqlite_connection, rule_id, document_id, sort_order)

        result = _select_rule_order(sorted_sqlite_connection, document_id)

        assert result == ["rule-a", "rule-b", "rule-c"]

    def test_sort_order_need_not_be_contiguous(self, sorted_sqlite_connection):
        """sort_order 값 사이에 빈틈이 있어도(삭제로 인한 결번 등) 상대 순서만 지켜지면 된다."""
        document_id = "doc1"
        _insert_document(sorted_sqlite_connection, document_id)
        for rule_id, sort_order in (("rule-first", 0), ("rule-second", 5), ("rule-third", 100)):
            _insert_acl_rule(sorted_sqlite_connection, rule_id, document_id, sort_order)

        result = _select_rule_order(sorted_sqlite_connection, document_id)

        assert result == ["rule-first", "rule-second", "rule-third"]

    def test_duplicate_sort_order_within_same_document_is_rejected(
        self, sorted_sqlite_connection
    ):
        """같은 document_id 안에서 sort_order가 중복되면 UNIQUE 제약으로 거부된다 --
        동시각(tie)에 기대는 페이지네이션 정렬과 달리, sort_order 정렬은
        애초에 동률 자체가 스키마에서 불가능하다."""
        document_id = "doc1"
        _insert_document(sorted_sqlite_connection, document_id)
        _insert_acl_rule(sorted_sqlite_connection, "rule-first", document_id, 0)

        with pytest.raises(sqlite3.IntegrityError):
            _insert_acl_rule(sorted_sqlite_connection, "rule-second", document_id, 0)

    def test_sorting_is_isolated_per_document_id(self, sorted_sqlite_connection):
        """다른 document_id의 규칙은 정렬 결과에 섞이지 않는다."""
        _insert_document(sorted_sqlite_connection, "doc1")
        _insert_document(sorted_sqlite_connection, "doc2")
        _insert_acl_rule(sorted_sqlite_connection, "doc2-rule", "doc2", 0)
        _insert_acl_rule(sorted_sqlite_connection, "doc1-rule-b", "doc1", 1)
        _insert_acl_rule(sorted_sqlite_connection, "doc1-rule-a", "doc1", 0)

        result = _select_rule_order(sorted_sqlite_connection, "doc1")

        assert result == ["doc1-rule-a", "doc1-rule-b"]


class TestAclNamespaceRuleSortOrderPortability:
    """acl_namespace_rule에 대한 (namespace, sort_order) 정렬 계약.

    acl_rule과 acl_namespace_rule은 계획 문서(§3~§5)가 동일한 우선순위
    재현 설계를 두 번 적용한 것이므로, 여기서는 acl_namespace_rule에서도
    같은 계약이 성립하는지만 확인한다(acl_rule 쪽 시나리오 반복은 생략).
    """

    def test_order_by_sort_order_reproduces_priority_regardless_of_insertion_order(
        self, sorted_sqlite_connection
    ):
        """네임스페이스 규칙도 삽입 순서가 아니라 sort_order 오름차순으로 정렬된다."""
        namespace = "*"
        for rule_id, sort_order in (("rule-z", 2), ("rule-x", 0), ("rule-y", 1)):
            _insert_namespace_rule(sorted_sqlite_connection, rule_id, namespace, sort_order)

        result = _select_namespace_rule_order(sorted_sqlite_connection, namespace)

        assert result == ["rule-x", "rule-y", "rule-z"]

    def test_duplicate_sort_order_within_same_namespace_is_rejected(
        self, sorted_sqlite_connection
    ):
        """같은 namespace 안에서 sort_order가 중복되면 UNIQUE 제약으로 거부된다."""
        namespace = "*"
        _insert_namespace_rule(sorted_sqlite_connection, "rule-first", namespace, 0)

        with pytest.raises(sqlite3.IntegrityError):
            _insert_namespace_rule(sorted_sqlite_connection, "rule-second", namespace, 0)

    def test_sorting_is_isolated_per_namespace(self, sorted_sqlite_connection):
        """다른 namespace의 규칙은 정렬 결과에 섞이지 않는다."""
        _insert_namespace_rule(sorted_sqlite_connection, "other-rule", "other", 0)
        _insert_namespace_rule(sorted_sqlite_connection, "default-rule-b", "*", 1)
        _insert_namespace_rule(sorted_sqlite_connection, "default-rule-a", "*", 0)

        result = _select_namespace_rule_order(sorted_sqlite_connection, "*")

        assert result == ["default-rule-a", "default-rule-b"]
