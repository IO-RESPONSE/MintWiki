"""Portable restore plan 문서(0497)를 검증한다.

docs/portable-restore-plan.md가 backup format 정책을 따르는 복원 절차와 에러 처리,
MariaDB/PostgreSQL 차이를 정의했는지 확인한다.
"""

from pathlib import Path


def _doc_path() -> Path:
    return Path(__file__).parent.parent / "docs" / "portable-restore-plan.md"


def test_portable_restore_plan_doc_exists():
    """문서 파일이 존재하는지 확인한다."""
    assert _doc_path().exists(), "docs/portable-restore-plan.md should exist"


def test_portable_restore_plan_doc_defines_restore_procedure():
    """복원 절차의 공통 원칙(준비, 트랜잭션, 로드 순서)을 정의하는지 확인한다."""
    content = _doc_path().read_text()

    assert "준비 단계" in content
    assert "트랜잭션" in content
    assert "로드 순서" in content
    assert "BEGIN" in content or "COMMIT" in content
    assert "ROLLBACK" in content


def test_portable_restore_plan_doc_defines_schema_version_compatibility():
    """스키마 버전 호환성 검사를 정의하는지 확인한다."""
    content = _doc_path().read_text()

    assert "스키마 버전 호환성 검사" in content
    assert "동일 버전" in content
    assert "불일치 버전" in content
    assert "구 버전" in content
    assert "신 버전" in content


def test_portable_restore_plan_doc_covers_sql_dump_restore():
    """SQL dump 복원 절차를 정의하는지 확인한다."""
    content = _doc_path().read_text()

    assert "SQL Dump 복원 절차" in content
    assert "seed" in content
    assert "INSERT" in content
    assert "파일 로드" in content or "파일 읽기" in content


def test_portable_restore_plan_doc_covers_json_export_restore():
    """JSON export 복원 절차를 정의하는지 확인한다."""
    content = _doc_path().read_text()

    assert "JSON Export 복원 절차" in content
    assert "export_version" in content
    assert "schema_version" in content
    assert "tables" in content


def test_portable_restore_plan_doc_covers_mariadb_postgresql_differences():
    """MariaDB vs PostgreSQL 차이를 정의하는지 확인한다."""
    content = _doc_path().read_text()

    assert "MariaDB vs PostgreSQL 차이" in content
    assert "PostgreSQL" in content
    assert "MariaDB" in content
    assert "FOREIGN_KEY_CHECKS" in content


def test_portable_restore_plan_doc_defines_error_handling():
    """에러 처리 전략을 정의하는지 확인한다."""
    content = _doc_path().read_text()

    assert "에러 처리 전략" in content
    assert "부분 실패" in content
    assert "롤백" in content
    assert "재복현" in content or "재복원" in content


def test_portable_restore_plan_doc_defines_operation_scenarios():
    """운영 시나리오(정상, 롤백, 부분 복원)를 정의하는지 확인한다."""
    content = _doc_path().read_text()

    assert "운영 시나리오" in content
    assert "정상 복원" in content
    assert "롤백" in content
    assert "부분 복원" in content


def test_portable_restore_plan_doc_defines_validation():
    """복원 후 데이터 검증 절차를 정의하는지 확인한다."""
    content = _doc_path().read_text()

    assert "복원 확인" in content or "검증" in content
    assert "행 개수" in content or "COUNT(*)" in content


def test_portable_restore_plan_doc_links_to_backup_format():
    """backup format 문서를 참조하는지 확인한다."""
    content = _doc_path().read_text()

    assert "portable-backup-format.md" in content


def test_portable_restore_plan_doc_links_to_persistence_boundaries():
    """persistence boundaries 문서를 참조하는지 확인한다."""
    content = _doc_path().read_text()

    assert "persistence-boundaries.md" in content or "Persistence Boundaries" in content


def test_portable_backup_format_doc_links_to_restore_plan():
    """portable-backup-format.md가 restore plan을 참조하는지 확인한다."""
    backup_path = Path(__file__).parent.parent / "docs" / "portable-backup-format.md"
    content = backup_path.read_text()

    assert "portable-restore-plan.md" in content
    assert "0497" in content
