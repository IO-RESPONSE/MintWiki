"""DB portability QA paths 문서(0483)를 검증한다.

docs/db-portability-qa-paths.md가 기존 DB portability 검사들을 로컬/CI/
수동 세 경로로 빠짐없이 지도화했는지 확인한다.
"""

from pathlib import Path


def _doc_path() -> Path:
    return Path(__file__).parent.parent / "docs" / "db-portability-qa-paths.md"


def test_db_portability_qa_paths_doc_exists():
    """문서 파일이 존재하는지 확인한다."""
    assert _doc_path().exists(), "docs/db-portability-qa-paths.md should exist"


def test_doc_defines_local_and_ci_and_manual_paths():
    """로컬/CI/수동 세 경로가 모두 절 제목으로 존재하는지 확인한다."""
    content = _doc_path().read_text()

    assert "로컬 경로" in content
    assert "CI 경로" in content
    assert "수동/선택 경로" in content


def test_doc_maps_local_and_ci_paths_to_the_same_scripts():
    """로컬/CI 경로가 동일한 scripts/test.sh, scripts/qa.sh를 쓴다는 것을 확인한다."""
    content = _doc_path().read_text()

    assert "scripts/test.sh" in content
    assert "scripts/qa.sh" in content
    assert "run-next-task.sh" in content


def test_doc_marks_smoke_scripts_as_manual_and_skippable():
    """MariaDB/PostgreSQL smoke 스크립트가 수동/선택 경로이며 skip 가능함을 확인한다."""
    content = _doc_path().read_text()

    assert "scripts/mariadb_smoke_check.py" in content
    assert "scripts/postgresql_smoke_check.py" in content
    assert "WIKI_MARIADB_DSN" in content
    assert "WIKI_DATABASE_URL" in content
    assert "skip" in content


def test_doc_excludes_smoke_scripts_from_qa_sh_gate():
    """smoke 스크립트가 scripts/qa.sh 게이트에 포함되지 않는다는 것을 확인한다."""
    content = _doc_path().read_text()

    assert "포함되지 않는다" in content


def test_doc_defers_unified_qa_checklist_to_later_task():
    """0500 통합 QA 체크리스트가 이 문서의 범위 밖 후속 작업임을 확인한다."""
    content = _doc_path().read_text()

    assert "0500" in content


def test_doc_links_to_related_plan_docs():
    """이 문서가 기존 마이그레이션 체크리스트/smoke 계획/runner 문서와 연결되는지 확인한다."""
    content = _doc_path().read_text()

    assert "migration-portability-checklist.md" in content
    assert "mariadb-migration-smoke-plan.md" in content
    assert "runner.md" in content
