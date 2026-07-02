"""MariaDB migration smoke plan 문서(0480)를 검증한다.

docs/mariadb-migration-smoke-plan.md가 db/schema의 portable SQL 원본을
실제 MariaDB 서버에 적용해 보는 smoke 테스트의 실행 조건(선택 실행/skip),
적용 순서, 단계, 실패 판정 기준을 확정했는지 확인한다.
"""

from pathlib import Path


def _doc_path() -> Path:
    return Path(__file__).parent.parent / "docs" / "mariadb-migration-smoke-plan.md"


def test_mariadb_migration_smoke_plan_doc_exists():
    """문서 파일이 존재하는지 확인한다."""
    assert _doc_path().exists(), "docs/mariadb-migration-smoke-plan.md should exist"


def test_doc_makes_smoke_run_optional_and_skippable():
    """MariaDB DSN이 없으면 실패가 아니라 skip한다는 규칙을 확인한다."""
    content = _doc_path().read_text()

    assert "WIKI_MARIADB_DSN" in content
    assert "skip" in content


def test_doc_orders_schema_files_by_foreign_key_dependency():
    """db/schema/*.sql 적용 순서가 FK 의존 순서(참조 대상이 먼저)를 따르는지 확인한다."""
    content = _doc_path().read_text()

    ordered_files = [
        "schema_migration.sql",
        "account.sql",
        "document.sql",
        "revision.sql",
        "user_session.sql",
        "acl_rule.sql",
        "acl_namespace_rule.sql",
        "discussion_thread.sql",
        "discussion_comment.sql",
        "audit_event.sql",
        "job.sql",
    ]
    positions = [content.index(name) for name in ordered_files]

    assert positions == sorted(positions), (
        "schema files should be listed in foreign-key dependency order"
    )


def test_doc_defines_failure_categories():
    """접속 실패/DDL 적용 실패/테이블 존재 확인 실패를 구분한다는 규칙을 확인한다."""
    content = _doc_path().read_text()

    assert "접속 실패" in content
    assert "DDL 적용 실패" in content
    assert "테이블 존재 확인 실패" in content


def test_doc_defers_actual_ci_wiring():
    """실제 CI 연결은 이 태스크 범위 밖이라는 노트를 반영하는지 확인한다."""
    content = _doc_path().read_text()

    assert "CI 연결" in content
    assert "범위 밖" in content


def test_doc_excludes_migration_runner_and_collation_fixtures():
    """마이그레이션 러너 구현과 collation fixture 검증이 이 문서 범위 밖임을 확인한다."""
    content = _doc_path().read_text()

    assert "0505" in content
    assert "0511" in content


def test_doc_links_to_related_plan_docs():
    """이 문서가 기존 마이그레이션 체크리스트/db 골격 문서와 연결되는지 확인한다."""
    content = _doc_path().read_text()

    assert "migration-portability-checklist.md" in content
    assert "db/README.md" in content
    assert "mariadb-compatibility-matrix.md" in content
