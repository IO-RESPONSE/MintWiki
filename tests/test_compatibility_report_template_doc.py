"""Compatibility report 템플릿 문서를 검증한다."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = REPO_ROOT / "docs" / "compatibility-report-template.md"


def _content() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


def _unwrapped_content() -> str:
    return " ".join(_content().split())


def test_compatibility_report_template_doc_exists():
    """0664 compatibility report 템플릿 문서가 존재한다."""
    assert DOC_PATH.is_file()


def test_compatibility_report_template_records_php_results():
    """PHP 버전, 확장, 설정값, 판정을 기록한다."""
    content = _unwrapped_content()

    assert "PHP 결과" in content
    assert "**PHP 버전**" in content
    assert "`pdo_mysql`" in content
    assert "`memory_limit`" in content
    assert "`disabled_functions`" in content
    assert "**PHP 판정**: 통과 / 조건부 통과 / 실패" in content


def test_compatibility_report_template_records_mariadb_results():
    """MariaDB 버전, DSN, charset, 권한, migration 결과를 기록한다."""
    content = _unwrapped_content()

    assert "MariaDB 결과" in content
    assert "**DB 엔진/버전**" in content
    assert "mysql:host=<host>;dbname=<db>;charset=utf8mb4" in content
    assert "**Collation**" in content
    assert "`CREATE INDEX`" in content
    assert "**Migration 적용 결과**" in content


def test_compatibility_report_template_records_hosting_provider_results():
    """호스팅 제공자 설정과 public path, writable directory 결과를 기록한다."""
    content = _unwrapped_content()

    assert "Hosting Provider 결과" in content
    assert "**Document root 설정**: `php/public/` 가능" in content
    assert "**URL rewrite**" in content
    assert "`php/src/` URL 접근 차단" in content
    assert "`storage/cache/`" in content
    assert "Cron 또는 URL runner" in content


def test_compatibility_report_template_records_smoke_and_final_decision():
    """Smoke test, 이슈, 최종 판정 기록 기준을 포함한다."""
    content = _unwrapped_content()

    assert "Smoke Test 결과" in content
    assert "installer requirement check" in content
    assert "`storage/installer/install.lock`" in content
    assert "`/admin/diagnostics`" in content
    assert "이슈와 조치" in content
    assert "**전체 판정**: 지원 / 조건부 지원 / 미지원" in content


def test_compatibility_report_template_links_related_docs():
    """관련 shared hosting, security, performance, MariaDB 문서와 연결한다."""
    content = _content()

    for reference in [
        "shared-hosting-target-baseline.md",
        "shared-hosting-qa-checklist.md",
        "shared-hosting-security-checklist.md",
        "shared-hosting-performance-checklist.md",
        "mariadb-compatibility-matrix.md",
    ]:
        assert reference in content, f"missing related doc reference: {reference}"
