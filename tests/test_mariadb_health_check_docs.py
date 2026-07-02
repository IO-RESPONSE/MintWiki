"""MariaDB health check 문서(0503)를 검증한다.

docs/mariadb-health-check.md가 운영자가 MariaDB 연결 상태를 확인할 수 있는
방법(헬스 엔드포인트, CLI, smoke 테스트)을 제시했는지 확인한다.
"""

from pathlib import Path


def _doc_path() -> Path:
    return Path(__file__).parent.parent / "docs" / "mariadb-health-check.md"


def test_mariadb_health_check_doc_exists():
    """문서 파일이 존재하는지 확인한다."""
    assert _doc_path().exists(), "docs/mariadb-health-check.md should exist"


def test_doc_provides_three_check_methods():
    """애플리케이션 헬스 엔드포인트, CLI, smoke 테스트의 세 가지 방법을 제시하는지 확인한다."""
    content = _doc_path().read_text()

    assert "/health" in content, "doc should mention /health endpoint"
    assert "엔드포인트" in content or "endpoint" in content
    assert "CLI" in content or "mysql" in content or "mariadb" in content
    assert "smoke" in content or "smoke 테스트" in content


def test_doc_mentions_health_endpoint_limitation():
    """현재 /health 엔드포인트가 DB 연결을 확인하지 않는다는 제한을 명시하는지 확인한다."""
    content = _doc_path().read_text()

    assert "데이터베이스 연결 상태는 포함하지 않는다" in content or \
           "database connection" in content or \
           "DB 헬스 체크는" in content


def test_doc_provides_cli_usage_examples():
    """CLI 클라이언트 사용 예시를 제시하는지 확인한다."""
    content = _doc_path().read_text()

    assert "mysql" in content
    assert "-u wiki" in content or "사용자명" in content


def test_doc_references_smoke_check_script():
    """smoke 테스트를 통한 검증 방법이 scripts/mariadb_smoke_check.py를 참조하는지 확인한다."""
    content = _doc_path().read_text()

    assert "smoke" in content or "smoke 테스트" in content
    assert "mariadb_smoke_check" in content or "scripts/" in content


def test_doc_includes_skip_vs_failure_distinction():
    """smoke 테스트의 skip(정상)과 실패를 구분하는지 확인한다."""
    content = _doc_path().read_text()

    assert "skip" in content
    assert "실패" in content


def test_doc_provides_troubleshooting_section():
    """트러블슈팅 섹션이 있는지 확인한다."""
    content = _doc_path().read_text()

    assert "트러블슈팅" in content or "Troubleshooting" in content


def test_doc_links_to_related_mariadb_docs():
    """이 문서가 다른 MariaDB 관련 문서와 연결되는지 확인한다."""
    content = _doc_path().read_text()

    assert "mariadb-local-compose-override.md" in content
    assert "mariadb-migration-smoke-plan.md" in content or "migration-smoke-plan" in content


def test_doc_mentions_out_of_scope_items():
    """이 문서 범위 밖인 항목(프로덕션 모니터링, DB 헬스 엔드포인트 구현)을 명시하는지 확인한다."""
    content = _doc_path().read_text()

    assert "범위" in content  # 범위 정의 섹션 확인
    assert "0518" in content or "정하지 않는 것" in content
