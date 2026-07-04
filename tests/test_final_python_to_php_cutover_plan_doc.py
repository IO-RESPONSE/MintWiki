"""최종 Python to PHP cutover 계획 문서를 검증한다."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = REPO_ROOT / "docs" / "final-python-to-php-cutover-plan.md"

REQUIRED_HEADINGS = [
    "## 목적과 범위",
    "## 1. Cutover 시작 조건",
    "## 2. 데이터 계획",
    "## 3. Route 전환 계획",
    "## 4. Config 전환 계획",
    "## 5. Rollback 계획",
    "## 6. Cutover 후 검증",
    "## 관련 문서",
]

REQUIRED_RELATED_DOCS = [
    "php-replacement-strategy.md",
    "php-replacement-readiness-checklist.md",
    "php-ui-readiness-gate.md",
    "ui-route-parity-matrix.md",
    "shared-hosting-upgrade-procedure.md",
    "shared-hosting-rollback-procedure.md",
    "portable-backup-format.md",
    "config-file-permission-policy.md",
]


def _content() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


def _unwrapped_content() -> str:
    return " ".join(_content().split())


def test_final_python_to_php_cutover_plan_doc_exists():
    """0666 최종 Python to PHP cutover 계획 문서가 존재한다."""
    assert DOC_PATH.is_file()


def test_final_python_to_php_cutover_plan_doc_has_required_sections():
    """데이터, route, config, rollback을 포함한 필수 절이 모두 있다."""
    content = _content()
    for heading in REQUIRED_HEADINGS:
        assert heading in content, f"missing required heading: {heading}"


def test_final_python_to_php_cutover_plan_doc_defines_data_checkpoint():
    """데이터 freeze, schema version, backup/export 확인을 명시한다."""
    content = _unwrapped_content()

    assert "maintenance mode 또는 읽기 전용 모드" in content
    assert "DB schema version" in content
    assert "portable-backup-format.md" in content
    assert "row count" in content


def test_final_python_to_php_cutover_plan_doc_defines_route_cutover():
    """PHP document root와 route parity 확인 절차를 명시한다."""
    content = _unwrapped_content()

    assert "`php/public/`" in content
    assert "/health" in content
    assert "/documents/{title}" in content
    assert "ui-route-parity-matrix.md" in content


def test_final_python_to_php_cutover_plan_doc_defines_config_mapping():
    """Python 운영 설정을 PHP 설정으로 명시적으로 대응하도록 요구한다."""
    content = _unwrapped_content()

    assert "DB DSN" in content
    assert "secret key" in content
    assert "storage/cache" in content
    assert "Python 전용 설정" in content


def test_final_python_to_php_cutover_plan_doc_defines_rollback_path():
    """rollback 시작 기준과 Python 운영 경로 복원 절차를 고정한다."""
    content = _unwrapped_content()

    assert "rollback의 기본값" in content
    assert "Python 운영 경로 전체로 되돌리기" in content
    assert "shared-hosting-rollback-procedure.md" in content
    assert "백업 또는 portable export를 복원" in content


def test_final_python_to_php_cutover_plan_doc_links_related_docs():
    """관련 문서 링크가 본문에 있고 실제 파일도 존재한다."""
    content = _content()
    for doc_name in REQUIRED_RELATED_DOCS:
        assert doc_name in content, f"missing related doc reference: {doc_name}"
        assert (REPO_ROOT / "docs" / doc_name).is_file()
