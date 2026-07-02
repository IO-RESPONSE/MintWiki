"""`docs/php-no-framework-domain-rule.md` 가 태스크 0424 의 목표("PHP
도메인 계층 framework 금지 규칙을 문서화한다")와 Notes 요구사항("Python
boundary와 같은 원칙이다")을 실제로 고정하고 있으며, 문서가 서술하는
도메인 루트/어댑터 계층 경계가 `php/` 트리의 실제 상태와 어긋나지
않는지 확인한다.
"""
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = REPO_ROOT / "docs" / "php-no-framework-domain-rule.md"
CODING_STANDARD_DOC_PATH = REPO_ROOT / "docs" / "php-coding-standard.md"
STATIC_ANALYSIS_DOC_PATH = REPO_ROOT / "docs" / "php-static-analysis-plan.md"
PHP_SRC_DIR = REPO_ROOT / "php" / "src"
PHP_MODULES_DIR = PHP_SRC_DIR / "Modules"

REQUIRED_DOC_HEADINGS = [
    "## 배경: Python 쪽 두 경계 검사기",
    "## PHP 쪽 대응 경계",
    "### 도메인 루트",
    "### 검사 제외 계층 (어댑터)",
    "### 규칙 1 — framework import 금지",
    "### 규칙 2 — 어댑터 계층 역참조 금지",
    "## 시행 방법",
    "## 이 문서가 하지 않는 것",
    "## 관련 문서",
]


def test_php_no_framework_domain_rule_doc_exists():
    """PHP 도메인 framework 금지 규칙 문서가 docs 아래에 존재한다."""
    assert DOC_PATH.is_file()


def test_php_no_framework_domain_rule_doc_has_required_sections():
    """배경, 도메인 루트/어댑터 경계, 두 규칙, 시행 방법, 범위 제외,
    관련 문서 절이 모두 있다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    for heading in REQUIRED_DOC_HEADINGS:
        assert heading in content, f"missing required heading: {heading}"


def test_php_no_framework_domain_rule_doc_names_python_boundary_scripts():
    """태스크 Notes 요구사항: "Python boundary와 같은 원칙이다" — 실제
    Python 원본 검사기 두 개를 근거로 명시한다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "scripts/check_boundaries.py" in content
    assert "scripts/check_no_app_import_in_modules.py" in content
    python_scripts_dir = REPO_ROOT / "scripts"
    assert (python_scripts_dir / "check_boundaries.py").is_file()
    assert (python_scripts_dir / "check_no_app_import_in_modules.py").is_file()


def test_php_no_framework_domain_rule_doc_names_domain_root_and_adapters():
    """도메인 루트(`php/src/Modules/`)와 검사 제외 어댑터 계층
    (`php/src/App/`, `php/src/Http/`)을 실제 디렉터리 존재와 함께
    명시한다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "php/src/Modules/" in content
    assert "php/src/App/" in content
    assert "php/src/Http/" in content
    assert (PHP_SRC_DIR / "Modules").is_dir()
    assert (PHP_SRC_DIR / "App").is_dir()
    assert (PHP_SRC_DIR / "Http").is_dir()


def test_php_no_framework_domain_rule_doc_defers_automated_enforcement():
    """이 문서 스스로는 자동 검사 스크립트를 작성하지 않는다는 범위
    제외를 명시한다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "자동 검사 스크립트" in content
    assert "이 문서의 범위가 아니다" in content


def test_php_no_framework_domain_rule_doc_references_related_docs():
    """코딩 표준 문서, 정적 분석 계획 문서, namespace 매핑 문서, 전략
    문서, repository 포트 계약 문서, 마이크로잡 목록 문서와 연결된다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    for reference in [
        "docs/php-coding-standard.md",
        "docs/php-static-analysis-plan.md",
        "docs/php-namespace-mapping.md",
        "docs/php-replacement-strategy.md",
        "docs/repository-port-contracts.md",
        "docs/php-db-ui-micro-job-prompts-0351-0670.md",
    ]:
        assert reference in content, f"missing related doc reference: {reference}"


def test_php_coding_standard_doc_links_to_no_framework_domain_rule_doc():
    """`docs/php-coding-standard.md`가 0424 완료 후 새 문서를 가리켜,
    범위 제외로만 남겨두지 않고 실제 정본 위치를 알려준다."""
    content = CODING_STANDARD_DOC_PATH.read_text(encoding="utf-8")
    assert "docs/php-no-framework-domain-rule.md" in content


def test_php_static_analysis_plan_doc_links_to_no_framework_domain_rule_doc():
    """`docs/php-static-analysis-plan.md`가 0424 완료 후 새 문서를
    가리킨다."""
    content = STATIC_ANALYSIS_DOC_PATH.read_text(encoding="utf-8")
    assert "docs/php-no-framework-domain-rule.md" in content


def _iter_php_module_files():
    return sorted(PHP_MODULES_DIR.rglob("*.php"))


def test_no_existing_modules_file_imports_app_or_http_namespace():
    """문서가 "현재 위반 사례가 없다"고 서술한 상태가 실제 `php/src/Modules/`
    코드와 일치하는지 확인한다 — `MintWiki\\App`/`MintWiki\\Http` 를
    `use` 하는 파일이 없어야 한다."""
    files = _iter_php_module_files()
    assert files, "expected at least one PHP source file under php/src/Modules/"
    forbidden_pattern = re.compile(r"^use MintWiki\\(App|Http)\\", re.MULTILINE)
    for path in files:
        content = path.read_text(encoding="utf-8")
        assert not forbidden_pattern.search(content), (
            f"{path}: domain module must not import MintWiki\\App or MintWiki\\Http"
        )
