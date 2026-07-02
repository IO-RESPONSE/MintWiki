"""DB phase QA checklist 문서(0500)를 검증한다.

docs/db-phase-qa-checklist.md가 ANSI lint, MariaDB smoke, PHP PDO skeleton
검증을 포함하는 완결된 QA 체크리스트로 기능하는지 확인한다.
"""

from pathlib import Path


def _doc_path() -> Path:
    return Path(__file__).parent.parent / "docs" / "db-phase-qa-checklist.md"


def test_db_phase_qa_checklist_doc_exists():
    """체크리스트 문서 파일이 존재하는지 확인한다."""
    assert _doc_path().exists(), "docs/db-phase-qa-checklist.md should exist"


def test_doc_defines_three_qa_paths():
    """자동 검사, smoke, PHP PDO 세 경로를 모두 절 제목으로 정의하는지 확인한다."""
    content = _doc_path().read_text()

    assert "1. 자동 검사" in content
    assert "2. 선택 실행: MariaDB Smoke" in content
    assert "3. PHP PDO 스켈레톤 검증" in content


def test_doc_covers_ansi_sql_lint():
    """ANSI SQL feature 금지 목록 검사를 포함하는지 확인한다."""
    content = _doc_path().read_text()

    assert "ANSI SQL feature 금지" in content
    assert "check_sql_denylist.py" in content
    assert "RETURNING" in content or "금지 목록" in content


def test_doc_references_migration_portability_checklist():
    """마이그레이션 portability 체크리스트를 참조하는지 확인한다."""
    content = _doc_path().read_text()

    assert "Migration Portability Checklist" in content
    assert "migration-portability-checklist.md" in content


def test_doc_covers_mariadb_smoke_test():
    """MariaDB smoke 테스트 실행 조건과 단계를 포함하는지 확인한다."""
    content = _doc_path().read_text()

    assert "MariaDB Smoke" in content or "smoke" in content
    assert "WIKI_MARIADB_DSN" in content
    assert "mariadb_smoke_check.py" in content


def test_doc_marks_smoke_test_as_optional_and_skippable():
    """smoke 테스트가 선택 실행이며 skip 가능함을 명시하는지 확인한다."""
    content = _doc_path().read_text()

    assert "서버 필요" in content or "선택 실행" in content
    assert "skip" in content


def test_doc_covers_db_module_boundary_check():
    """DB 모듈 경계 검사를 포함하는지 확인한다."""
    content = _doc_path().read_text()

    assert "경계 검사" in content or "boundary" in content
    assert "check_db_module_boundaries" in content or "import 정책" in content


def test_doc_includes_php_pdo_skeleton_verification():
    """PHP PDO 스켈레톤 검증 항목을 포함하는지 확인한다."""
    content = _doc_path().read_text()

    assert "PHP PDO 스켈레톤" in content
    assert "3. PHP PDO" in content


def test_doc_references_php_pdo_tasks():
    """PHP PDO connection/transaction skeleton 태스크(0484/0485)를 참조하는지 확인한다."""
    content = _doc_path().read_text()

    assert "0484" in content or "Connection" in content
    assert "0485" in content or "Transaction" in content


def test_doc_covers_php_pdo_connection_skeleton():
    """PHP PDO Connection 스켈레톤의 검증 항목을 포함하는지 확인한다."""
    content = _doc_path().read_text()

    assert "3.1 PHP PDO Connection" in content
    assert "MariaDB/PostgreSQL" in content
    assert "DSN" in content


def test_doc_covers_php_pdo_transaction_wrapper():
    """PHP PDO Transaction wrapper의 검증 항목을 포함하는지 확인한다."""
    content = _doc_path().read_text()

    assert "3.2 PHP PDO Transaction" in content
    assert "begin()" in content or "commit()" in content or "rollback()" in content


def test_doc_provides_qa_execution_order():
    """로컬/CI/수동 QA 실행 순서를 명시하는지 확인한다."""
    content = _doc_path().read_text()

    assert "4. QA 실행 순서" in content or "실행 순서" in content
    assert "4.1 로컬" in content or "로컬 개발" in content
    assert "4.2 CI" in content or "CI 경로" in content
    assert "4.3 수동" in content


def test_doc_shows_local_qa_bash_commands():
    """로컬 QA 실행을 위한 bash 명령어를 포함하는지 확인한다."""
    content = _doc_path().read_text()

    assert "scripts/qa.sh" in content
    assert "scripts/test.sh" in content


def test_doc_shows_mariadb_smoke_bash_command():
    """MariaDB smoke 테스트 실행을 위한 bash 명령어를 포함하는지 확인한다."""
    content = _doc_path().read_text()

    assert "WIKI_MARIADB_DSN" in content
    assert ".venv/bin/python" in content or "python" in content
    assert "mariadb_smoke_check.py" in content


def test_doc_defines_phase_scope():
    """이 체크리스트가 Phase C(0441-0520) 범위임을 명시하는지 확인한다."""
    content = _doc_path().read_text()

    assert "Phase C" in content
    assert "0441-0520" in content


def test_doc_excludes_out_of_scope_items():
    """성능 최적화, 데이터 마이그레이션 등 범위 밖 항목을 명시하는지 확인한다."""
    content = _doc_path().read_text()

    # "이 체크리스트가 다루지 않는 것" 섹션 확인
    assert "다루지 않는 것" in content


def test_doc_links_to_related_policy_docs():
    """ANSI SQL, migration, smoke, boundary 등 정책 문서들과 연결되는지 확인한다."""
    content = _doc_path().read_text()

    # 주요 정책 문서 참조
    assert "ansi-sql-persistence-policy.md" in content
    assert "migration-portability-checklist.md" in content
    assert "mariadb-migration-smoke-plan.md" in content
    assert "db-portability-qa-paths.md" in content
    assert "db-module-boundary-check.md" in content


def test_doc_specifies_checklist_items():
    """각 검사 항목마다 확인할 세부 사항을 기술하는지 확인한다."""
    content = _doc_path().read_text()

    # 체크박스 형식으로 확인 항목 제시
    assert "- [ ]" in content


def test_doc_mentions_runner_ci_gate():
    """Runner의 자동 CI 게이트를 참고하도록 명시하는지 확인한다."""
    content = _doc_path().read_text()

    assert "Runner" in content or "run-next-task.sh" in content
