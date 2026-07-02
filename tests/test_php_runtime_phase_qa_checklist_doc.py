"""`docs/php-runtime-phase-qa-checklist.md` 가 태스크 0439 의 목표("PHP
런타임 phase QA 체크리스트를 추가한다")와 Notes 요구사항("parity, autoload,
health, module skeleton을 점검한다")을 실제로 고정하고 있으며, 체크리스트가
가리키는 스크립트/문서/테스트가 실제로 존재하고 서로 어긋나지 않는지
확인한다.
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = REPO_ROOT / "docs" / "php-runtime-phase-qa-checklist.md"
ROOT_QA_SCRIPT_PATH = REPO_ROOT / "scripts" / "qa.sh"
PHP_QA_SCRIPT_PATH = REPO_ROOT / "php" / "scripts" / "qa.sh"

REQUIRED_DOC_HEADINGS = [
    "## 사용법",
    "## 1. Autoload",
    "## 2. Health",
    "## 3. Module skeleton",
    "## 4. Parity",
    "## 이 체크리스트가 다루지 않는 것",
    "## 관련 문서",
]

REFERENCED_SCRIPTS = [
    "php/scripts/qa.sh",
    "php/scripts/test.sh",
]

REFERENCED_DOCS = [
    "docs/portability-phase-qa-checklist.md",
    "docs/php-db-ui-micro-job-prompts-0351-0670.md",
    "docs/php-test-bootstrap.md",
    "docs/php-namespace-mapping.md",
    "docs/php-no-framework-domain-rule.md",
    "docs/php-parity-test-plan.md",
    "docs/php-module-replacement-matrix.md",
    "docs/php-replacement-readiness-checklist.md",
]

REFERENCED_PHP_TEST_FILES = [
    "php/tests/AutoloadSmokeTest.php",
    "php/tests/Http/HealthRouteTest.php",
    "php/tests/Http/RouterTest.php",
    "php/tests/Support/FixtureLoaderTest.php",
    "php/tests/Modules/Document/TitleFixtureRunnerTest.php",
    "php/tests/Modules/Acl/DecisionCodeFixtureRunnerTest.php",
    "php/tests/Modules/Document/ServiceParityTest.php",
    "php/tests/Modules/Document/RevisionIntegrationTest.php",
    "php/tests/Modules/Parser/ParityPlaceholderTest.php",
    "php/tests/Modules/Render/ParityPlaceholderTest.php",
]

REFERENCED_PYTHON_TEST_FILES = [
    "tests/test_php_qa_scripts.py",
    "tests/test_qa_script_php_hook.py",
    "tests/test_php_public_front_controller.py",
]


def _doc_text() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


def test_php_runtime_phase_qa_checklist_doc_exists():
    """Phase B QA 체크리스트 문서가 docs 아래에 존재한다."""
    assert DOC_PATH.is_file()


def test_php_runtime_phase_qa_checklist_doc_has_required_sections():
    """사용법, autoload/health/module skeleton/parity 4개 검증 절, 범위
    제외, 관련 문서 절이 모두 있다(Notes: parity, autoload, health,
    module skeleton을 점검한다)."""
    content = _doc_text()
    for heading in REQUIRED_DOC_HEADINGS:
        assert heading in content, f"missing required heading: {heading}"


def test_php_runtime_phase_qa_checklist_doc_references_existing_scripts():
    """문서가 가리키는 자동 검사 스크립트가 실제로 저장소에 존재한다."""
    content = _doc_text()
    for script in REFERENCED_SCRIPTS:
        assert script in content, f"missing script reference: {script}"
        assert (REPO_ROOT / script).is_file(), f"referenced script missing: {script}"


def test_php_runtime_phase_qa_checklist_doc_references_existing_docs():
    """문서가 가리키는 관련 Phase A/B 문서가 실제로 존재한다(링크 깨짐
    없음)."""
    content = _doc_text()
    for doc in REFERENCED_DOCS:
        assert doc in content, f"missing doc reference: {doc}"
        assert (REPO_ROOT / doc).is_file(), f"referenced doc missing: {doc}"


def test_php_runtime_phase_qa_checklist_doc_references_existing_php_tests():
    """문서가 가리키는 PHP 테스트 파일이 실제로 존재한다."""
    content = _doc_text()
    for test_file in REFERENCED_PHP_TEST_FILES:
        assert test_file in content, f"missing php test reference: {test_file}"
        assert (REPO_ROOT / test_file).is_file(), f"referenced php test missing: {test_file}"


def test_php_runtime_phase_qa_checklist_doc_references_existing_python_tests():
    """문서가 가리키는 파이썬 QA 스크립트 테스트가 실제로 존재한다."""
    content = _doc_text()
    for test_file in REFERENCED_PYTHON_TEST_FILES:
        assert test_file in content, f"missing python test reference: {test_file}"
        assert (REPO_ROOT / test_file).is_file(), f"referenced python test missing: {test_file}"


def test_php_runtime_phase_qa_checklist_doc_lists_all_twelve_modules():
    """module skeleton 절이 docs/modules.md 기준 12개 모듈을 모두
    나열한다."""
    content = _doc_text()
    for module in [
        "document",
        "revision",
        "parser",
        "render",
        "acl",
        "discussion",
        "search",
        "cache",
        "jobs",
        "user",
        "admin",
        "audit",
    ]:
        assert f"`{module}`" in content, f"missing module reference: {module}"


def test_php_qa_hook_is_already_wired_into_root_qa():
    """php/scripts/qa.sh가 이미 루트 scripts/qa.sh에서 선택 실행되도록
    연결되어 있다는 문서의 주장이 실제 스크립트 내용과 맞는지 확인한다
    (0431)."""
    root_qa_contents = ROOT_QA_SCRIPT_PATH.read_text(encoding="utf-8")
    assert "php/scripts/qa.sh" in root_qa_contents


def test_php_qa_sh_wires_test_sh():
    """php/scripts/qa.sh가 php/scripts/test.sh를 호출한다는 문서의
    주장이 실제 스크립트 내용과 맞는지 확인한다(0430)."""
    php_qa_contents = PHP_QA_SCRIPT_PATH.read_text(encoding="utf-8")
    assert "test.sh" in php_qa_contents
