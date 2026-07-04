"""Production readiness report placeholder 문서를 검증한다."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = REPO_ROOT / "docs" / "production-readiness-report.md"

REQUIRED_HEADINGS = [
    "## Production Readiness 정의",
    "## 현재 상태: Placeholder",
    "## 최종 검수 절차",
    "## 보고서 템플릿",
    "## 이 문서가 하지 않는 것",
    "## 관련 문서",
]

REQUIRED_RELATED_DOCS = [
    "shared-hosting-target-baseline.md",
    "shared-hosting-qa-checklist.md",
    "shared-hosting-security-checklist.md",
    "shared-hosting-upgrade-procedure.md",
    "shared-hosting-rollback-procedure.md",
    "production-error-handling-policy.md",
    "php-ui-readiness-gate.md",
    "final-python-to-php-cutover-plan.md",
]


def _content() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


def _unwrapped_content() -> str:
    return " ".join(_content().split())


def test_production_readiness_report_doc_exists():
    """0668 production readiness report placeholder 문서가 존재한다."""
    assert DOC_PATH.is_file()


def test_production_readiness_report_doc_has_required_sections():
    """placeholder, 최종 검수 절차, 템플릿 절을 포함한다."""
    content = _content()

    for heading in REQUIRED_HEADINGS:
        assert heading in content, f"missing required heading: {heading}"


def test_production_readiness_report_doc_defines_final_review_scope():
    """최종 검수 보고서가 판정해야 할 readiness 범위를 고정한다."""
    content = _unwrapped_content()

    assert "shared hosting 대상 배포본" in content
    assert "PHP, PDO, MariaDB, URL rewrite 요구사항" in content
    assert "public path, 설정 파일, writable directory" in content
    assert "사용자 메시지와 내부 진단 정보를 분리" in content
    assert "release candidate" in content


def test_production_readiness_report_doc_defines_status_values():
    """최종 보고서의 상태 값과 fail 차단 기준을 명시한다."""
    content = _unwrapped_content()

    assert "pass, warning, fail, not_measured" in content
    assert "fail 이 하나라도 있으면 production 배포를 진행하지 않는다" in content
    assert "warning 은 owner, 영향 범위, 후속 조치" in content


def test_production_readiness_report_doc_includes_template_items():
    """보고서 템플릿에 주요 검수 항목과 QA 기록이 있다."""
    content = _content()

    for item in [
        "Runtime baseline",
        "Public docroot and config isolation",
        "Installer lock and reinstall guard",
        "Upgrade and rollback",
        "Production error handling",
        "Cutover readiness",
        "`scripts/qa.sh`",
        "최종 판정: pass | warning | fail",
    ]:
        assert item in content


def test_production_readiness_report_doc_links_related_docs():
    """관련 Phase E 및 최종 전환 문서를 링크하고 실제 파일도 존재한다."""
    content = _content()

    for doc_name in REQUIRED_RELATED_DOCS:
        assert doc_name in content, f"missing related doc reference: {doc_name}"
        assert (REPO_ROOT / "docs" / doc_name).is_file()
