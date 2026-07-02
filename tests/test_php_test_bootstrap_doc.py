"""`docs/php-test-bootstrap.md` 가 태스크 0421 의 목표("PHP 테스트 실행
문서를 추가한다")와 Notes 요구사항("composer/phpunit 선택 기준을
적는다")을 실제로 고정하고 있으며, 문서가 서술하는 bootstrap 절차가
`php/` 트리의 실제 상태(외부 프레임워크 없는 테스트, 의존성 없는
composer.json)와 어긋나지 않는지 확인한다.
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = REPO_ROOT / "docs" / "php-test-bootstrap.md"
PHP_README_PATH = REPO_ROOT / "php" / "README.md"
PHP_COMPOSER_PATH = REPO_ROOT / "php" / "composer.json"
PHP_AUTOLOAD_SMOKE_TEST_PATH = REPO_ROOT / "php" / "tests" / "AutoloadSmokeTest.php"

REQUIRED_DOC_HEADINGS = [
    "## 현재 상태: 외부 테스트 프레임워크 없음",
    "## Bootstrap 절차",
    "## composer/phpunit 선택 기준",
    "### 프레임워크 없이 유지하는 이유 (현재)",
    "### PHPUnit(또는 동등 프레임워크) 도입을 검토할 조건",
    "## 이 문서가 하지 않는 것",
    "## 관련 문서",
]


def test_php_test_bootstrap_doc_exists():
    """PHP 테스트 bootstrap 문서가 docs 아래에 존재한다."""
    assert DOC_PATH.is_file()


def test_php_test_bootstrap_doc_has_required_sections():
    """현재 상태, bootstrap 절차, 선택 기준(유지 이유/도입 조건), 범위
    제외, 관련 문서 절이 모두 있다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    for heading in REQUIRED_DOC_HEADINGS:
        assert heading in content, f"missing required heading: {heading}"


def test_php_test_bootstrap_doc_describes_bootstrap_steps():
    """`composer install` 후 개별 테스트 파일을 `php` CLI로 직접
    실행하는 현재 절차를 명시한다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "composer install" in content
    assert "php tests/AutoloadSmokeTest.php" in content


def test_php_test_bootstrap_doc_states_composer_phpunit_criteria():
    """태스크 Notes 요구사항: composer/phpunit 선택 기준(유지 이유와
    도입 조건 양쪽)을 명시한다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "PHPUnit" in content
    assert "shared hosting" in content
    assert "require-dev" in content


def test_php_test_bootstrap_doc_does_not_claim_integration_script_exists():
    """통합 테스트 실행 스크립트(0430) 나 PHPUnit 도입 자체를 이
    태스크가 하지 않는다는 범위 제외를 명시한다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    assert "0430" in content
    assert "0431" in content


def test_php_test_bootstrap_doc_references_related_docs():
    """전략 문서, parity 계획 문서, php/ 트리 README 와 연결된다."""
    content = DOC_PATH.read_text(encoding="utf-8")
    for reference in [
        "docs/php-replacement-strategy.md",
        "docs/php-parity-test-plan.md",
        "php/README.md",
        "php/tests/README.md",
        "docs/php-db-ui-micro-job-prompts-0351-0670.md",
    ]:
        assert reference in content, f"missing related doc reference: {reference}"


def test_php_readme_links_to_test_bootstrap_doc():
    """`php/README.md`가 새 bootstrap 문서를 가리켜, php/ 트리를 보는
    사람이 테스트 실행법을 바로 찾을 수 있다."""
    content = PHP_README_PATH.read_text(encoding="utf-8")
    assert "docs/php-test-bootstrap.md" in content


def test_php_composer_manifest_still_declares_no_dev_dependencies():
    """문서가 "현재는 외부 프레임워크 없음"이라고 서술하는 상태가 실제
    `composer.json`과 일치한다 — PHPUnit 등 require-dev 패키지가 아직
    없다."""
    import json

    manifest = json.loads(PHP_COMPOSER_PATH.read_text(encoding="utf-8"))
    assert "require-dev" not in manifest


def test_autoload_smoke_test_still_runs_without_external_framework():
    """문서가 근거로 드는 첫 테스트 파일이 실제로 PHPUnit 등 외부
    프레임워크 클래스를 참조하지 않는다(순수 `php` CLI 스크립트)."""
    source = PHP_AUTOLOAD_SMOKE_TEST_PATH.read_text(encoding="utf-8")
    assert "PHPUnit" not in source
    assert "exit(0)" in source
    assert "exit(1)" in source
