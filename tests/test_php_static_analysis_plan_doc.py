"""`docs/php-static-analysis-plan.md` 가 태스크 0423 의 목표("PHP static
analysis 계획을 문서화한다")와 Notes 요구사항("PHPStan/Psalm 도입은
후속 잡으로 둔다")을 실제로 고정하고 있는지, 그리고 문서가 서술하는
"아직 도구가 없다"는 현재 상태가 `php/composer.json`의 실제 상태와
어긋나지 않는지 확인한다.
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = REPO_ROOT / "docs" / "php-static-analysis-plan.md"
PHP_README_PATH = REPO_ROOT / "php" / "README.md"
PHP_COMPOSER_PATH = REPO_ROOT / "php" / "composer.json"

REQUIRED_DOC_HEADINGS = [
    "## 현재 상태: 정적 분석 도구 없음",
    "## 도구 후보: PHPStan vs Psalm",
    "## 도입 트리거 조건",
    "## 도입 시 지켜야 할 원칙 (실행할 때 참고)",
    "## 이 문서가 하지 않는 것",
    "## 관련 문서",
]


def test_php_static_analysis_plan_doc_exists():
    """PHP 정적 분석 계획 문서가 docs 아래에 존재한다."""
    assert DOC_PATH.is_file()


def test_php_static_analysis_plan_doc_has_required_sections():
    """현재 상태, 도구 후보, 도입 트리거 조건, 도입 원칙, 범위 제외,
    관련 문서 절이 모두 있다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    for heading in REQUIRED_DOC_HEADINGS:
        assert heading in content, f"missing required heading: {heading}"


def test_php_static_analysis_plan_doc_names_both_tool_candidates():
    """태스크 Notes 요구사항: PHPStan과 Psalm을 후보로 언급한다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "PHPStan" in content
    assert "Psalm" in content


def test_php_static_analysis_plan_doc_defers_actual_adoption():
    """Notes 요구사항: "PHPStan/Psalm 도입은 후속 잡으로 둔다" — 이
    문서 스스로 도구를 설치하거나 설정하지 않는다는 범위 제외를
    명시한다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "설치하거나 설정 파일을 작성하지 않는다" in content


def test_php_static_analysis_plan_doc_references_related_docs():
    """코딩 표준 문서, 테스트 bootstrap 문서, 전략 문서, 마이크로잡
    목록 문서와 연결된다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    for reference in [
        "docs/php-coding-standard.md",
        "docs/php-test-bootstrap.md",
        "docs/php-replacement-strategy.md",
        "docs/php-db-ui-micro-job-prompts-0351-0670.md",
    ]:
        assert reference in content, f"missing related doc reference: {reference}"


def test_php_readme_links_to_static_analysis_plan_doc():
    """`php/README.md`가 새 정적 분석 계획 문서를 가리켜, php/ 트리를
    보는 사람이 계획을 바로 찾을 수 있다."""
    content = PHP_README_PATH.read_text(encoding="utf-8")
    assert "docs/php-static-analysis-plan.md" in content


def test_php_composer_manifest_still_has_no_static_analysis_dev_dependency():
    """문서가 "현재는 정적 분석 도구 없음"이라고 서술하는 상태가 실제
    `composer.json`과 일치한다 — PHPStan/Psalm 등 require-dev 패키지가
    아직 없다."""
    import json

    manifest = json.loads(PHP_COMPOSER_PATH.read_text(encoding="utf-8"))
    assert "require-dev" not in manifest
